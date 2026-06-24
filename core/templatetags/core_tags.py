from django import template
from django.utils.timesince import timesince
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def is_online(user):
    """Returns True if user was seen in the last 5 minutes."""
    if hasattr(user, 'profile') and user.profile.last_seen:
        return timezone.now() - user.profile.last_seen < timedelta(minutes=5)
    return False

@register.filter
def unread_count(conversation, user):
    """Returns the unread message count for a given user in a conversation."""
    return conversation.get_unread_count(user)

@register.filter
def is_liked_by(post, user):
    """Returns True if the given user has liked the given post."""
    if not user.is_authenticated:
        return False
    return post.likes.filter(user=user).exists()

@register.filter
def is_following(user, target_user):
    """Returns True if the user is following the target_user."""
    if not user.is_authenticated or not target_user.is_authenticated:
        return False
    return user.following_set.filter(following=target_user).exists()

@register.filter
def time_ago(value):
    """Returns a short human-readable time difference."""
    if not value:
        return ""
    
    now = timezone.now()
    diff = now - value
    
    if diff.days == 0 and diff.seconds >= 0 and diff.seconds < 60:
        return 'Just now'
    
    if diff.days == 0 and diff.seconds >= 60 and diff.seconds < 3600:
        return f"{diff.seconds // 60}m"
        
    if diff.days == 0 and diff.seconds >= 3600 and diff.seconds < 86400:
        return f"{diff.seconds // 3600}h"
        
    if diff.days >= 1 and diff.days < 7:
        return f"{diff.days}d"
        
    if diff.days >= 7 and diff.days < 30:
        return f"{diff.days // 7}w"
        
    if diff.days >= 30 and diff.days < 365:
        return f"{diff.days // 30}mo"
        
    return f"{diff.days // 365}y"
