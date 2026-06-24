def dark_mode_processor(request):
    """Context processor to make dark_mode preference available to all templates."""
    return {'dark_mode': request.COOKIES.get('dark_mode', 'false')}

def unread_messages_processor(request):
    """Context processor to count total unread messages across all conversations."""
    count = 0
    if request.user.is_authenticated:
        from .models import Message
        count = Message.objects.filter(conversation__participants=request.user, is_read=False).exclude(sender=request.user).count()
    return {'unread_messages_count': count}
