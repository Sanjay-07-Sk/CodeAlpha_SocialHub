import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from .models import Conversation, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.chat_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Secure access validation
        if not await self.is_participant(self.conversation_id, self.user):
            await self.close()
            return

        # Add user to conversation-specific room
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        await self.accept()

        # Mark messages as read upon entering the conversation
        await self.mark_messages_as_read()
        await self.broadcast_unread_updates()

    async def disconnect(self, close_code):
        # Remove user from room
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'message':
            content = data.get('message', '').strip()
            if content:
                message_data = await self.save_message(self.conversation_id, self.user, content)
                if message_data:
                    # Broadcast to conversation group
                    await self.channel_layer.group_send(
                        self.chat_group_name,
                        {
                            'type': 'chat_message_broadcast',
                            'message': message_data
                        }
                    )
                    # Broadcast unread updates to all other participants' notification channels
                    await self.broadcast_unread_updates(message_data)

        elif action == 'typing':
            is_typing = data.get('typing', False)
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'chat_typing_broadcast',
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'typing': is_typing
                }
            )

        elif action == 'read_receipt':
            await self.mark_messages_as_read()
            await self.broadcast_unread_updates()

    async def chat_message_broadcast(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))

    async def chat_typing_broadcast(self, event):
        # Send typing status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'typing': event['typing']
        }))

    @database_sync_to_async
    def is_participant(self, conversation_id, user):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return conversation.participants.filter(id=user.id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, conversation_id, sender, content):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if not conversation.participants.filter(id=sender.id).exists():
                return None
            
            message = Message.objects.create(conversation=conversation, sender=sender, content=content)
            
            # Serialize
            avatar_url = ""
            if hasattr(sender, 'profile') and sender.profile.profile_picture:
                avatar_url = sender.profile.profile_picture.url

            timestamp_formatted = timezone.localtime(message.timestamp).strftime('%I:%M %p')

            return {
                'message_id': message.id,
                'conversation_id': conversation.id,
                'sender_id': sender.id,
                'sender_username': sender.username,
                'sender_avatar': avatar_url,
                'content': message.content,
                'timestamp': timestamp_formatted,
                'participants_ids': list(conversation.participants.values_list('id', flat=True))
            }
        except Exception as e:
            print("Error in save_message:", e)
            return None

    @database_sync_to_async
    def mark_messages_as_read(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            conversation.messages.filter(is_read=False).exclude(sender=self.user).update(is_read=True)
        except Exception as e:
            print("Error in mark_messages_as_read:", e)

    async def broadcast_unread_updates(self, message_data=None):
        # Notify other participants to update their inbox unread badges
        try:
            participants_ids = await self.get_participants_ids()
            for pid in participants_ids:
                if pid != self.user.id:
                    # Fetch counts
                    unread_count = await self.get_unread_count_for_user(self.conversation_id, pid)
                    total_unread = await self.get_total_unread_count_for_user(pid)
                    
                    last_msg_text = message_data['content'] if message_data else ""
                    last_msg_time = message_data['timestamp'] if message_data else ""
                    last_msg_sender = message_data['sender_username'] if message_data else ""
                    
                    await self.channel_layer.group_send(
                        f'user_{pid}',
                        {
                            'type': 'user_message_notification',
                            'conversation_id': int(self.conversation_id),
                            'sender_id': self.user.id,
                            'sender_username': self.user.username,
                            'content': last_msg_text,
                            'timestamp': last_msg_time,
                            'unread_count': unread_count,
                            'total_unread_count': total_unread
                        }
                    )
        except Exception as e:
            print("Error in broadcast_unread_updates:", e)

    @database_sync_to_async
    def get_participants_ids(self):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return list(conversation.participants.values_list('id', flat=True))
        except Exception:
            return []

    @database_sync_to_async
    def get_unread_count_for_user(self, conversation_id, user_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            user = User.objects.get(id=user_id)
            return conversation.get_unread_count(user)
        except Exception:
            return 0

    @database_sync_to_async
    def get_total_unread_count_for_user(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            return sum(conv.get_unread_count(user) for conv in user.conversations.all())
        except Exception:
            return 0


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.user_group_name = f'user_{self.user.id}'

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.accept()

        # Update online status
        await self.set_online()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            # Update offline status
            await self.set_offline()

    async def receive(self, text_data):
        pass

    async def user_message_notification(self, event):
        # Forward unread message counts and details to client
        await self.send(text_data=json.dumps({
            'type': 'message_notification',
            'conversation_id': event['conversation_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'content': event['content'],
            'timestamp': event['timestamp'],
            'unread_count': event['unread_count'],
            'total_unread_count': event['total_unread_count']
        }))

    async def user_status_notification(self, event):
        # Forward user status change to client
        await self.send(text_data=json.dumps({
            'type': 'status_notification',
            'user_id': event['user_id'],
            'status': event['status'],
            'last_seen': event.get('last_seen', '')
        }))

    async def set_online(self):
        conns = cache.get(f'online_conn_{self.user.id}', 0) + 1
        cache.set(f'online_conn_{self.user.id}', conns, timeout=None)

        if conns == 1:
            partners = await self.update_db_status(True)
            # Broadcast to all conversation partners
            for partner_id in partners:
                await self.channel_layer.group_send(
                    f'user_{partner_id}',
                    {
                        'type': 'user_status_notification',
                        'user_id': self.user.id,
                        'status': 'online'
                    }
                )

    async def set_offline(self):
        conns = max(0, cache.get(f'online_conn_{self.user.id}', 0) - 1)
        cache.set(f'online_conn_{self.user.id}', conns, timeout=None)

        if conns == 0:
            partners = await self.update_db_status(False)
            # Broadcast to all conversation partners
            for partner_id in partners:
                await self.channel_layer.group_send(
                    f'user_{partner_id}',
                    {
                        'type': 'user_status_notification',
                        'user_id': self.user.id,
                        'status': 'offline',
                        'last_seen': 'Just now'
                    }
                )

    @database_sync_to_async
    def update_db_status(self, is_online):
        try:
            user = User.objects.get(id=self.user.id)
            profile = user.profile
            profile.last_seen = timezone.now()
            profile.save()

            return list(User.objects.filter(conversations__participants=user).exclude(id=user.id).distinct().values_list('id', flat=True))
        except Exception as e:
            print("Error in update_db_status:", e)
            return []
