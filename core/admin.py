from django.contrib import admin
from .models import Profile, Post, Comment, Like, Follow, Conversation, Message

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'last_seen', 'created_at']
    search_fields = ['user__username', 'location']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'content_preview', 'created_at', 'total_likes']
    search_fields = ['content', 'author__username']
    list_filter = ['created_at']

    def content_preview(self, obj):
        return obj.content[:50]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'created_at']
    search_fields = ['content', 'author__username']

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'updated_at']
    filter_horizontal = ['participants']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'content_preview', 'is_read', 'timestamp']
    list_filter = ['is_read', 'timestamp']

    def content_preview(self, obj):
        return obj.content[:50]
