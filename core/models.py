from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Profile(models.Model):
    """User profile extending the built-in User model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        default='profile_pics/default.png',
        blank=True,
    )
    location = models.CharField(max_length=100, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def followers_count(self):
        return self.user.followers_set.count()

    def following_count(self):
        return self.user.following_set.count()

    def __str__(self):
        return f'{self.user.username} Profile'


class Post(models.Model):
    """A user-created post with optional image."""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=2200)
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def total_likes(self):
        return self.likes.count()

    def total_comments(self):
        return self.comments.count()

    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}'


class Comment(models.Model):
    """A comment on a post."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments_made')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username} on {self.post}: {self.content[:30]}'


class Like(models.Model):
    """A like on a post – unique per user per post."""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} likes {self.post}'


class Follow(models.Model):
    """A follow relationship between two users."""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_set')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_set')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']

    def clean(self):
        if self.follower == self.following:
            raise ValidationError('You cannot follow yourself.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.follower.username} follows {self.following.username}'


class Conversation(models.Model):
    """A private conversation between two or more users."""
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Conversation {self.id}'

    def get_last_message(self):
        return self.messages.order_by('-timestamp').first()

    def get_unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """A single message within a conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'Message {self.id} by {self.sender.username}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update conversation's updated_at field when a new message is saved
        self.conversation.save()
