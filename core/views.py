import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, View
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages

from .models import Post, Profile, Comment, Like, Follow
from .forms import UserRegistrationForm, PostForm, CommentForm, ProfileForm


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class HomeFeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'core/home.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        # Get posts from users the current user follows + own posts
        following_users = User.objects.filter(followers_set__follower=self.request.user)
        if following_users.exists():
            return Post.objects.filter(
                Q(author__in=following_users) | Q(author=self.request.user)
            ).select_related('author', 'author__profile').prefetch_related('likes', 'comments')
        else:
            return Post.objects.all().select_related('author', 'author__profile').prefetch_related('likes', 'comments')


class ExploreView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'core/explore.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        return Post.objects.all().select_related('author', 'author__profile').prefetch_related('likes', 'comments')


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'core/post_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Post created successfully!')
        return super().form_valid(form)


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'core/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['is_liked'] = self.object.likes.filter(user=self.request.user).exists()
        return context


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'core/post_form.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_success_url(self):
        messages.success(self.request, 'Post updated successfully!')
        return reverse_lazy('post_detail', kwargs={'pk': self.object.pk})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'core/post_confirm_delete.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Post deleted successfully.')
        return super().delete(request, *args, **kwargs)


class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        post_obj = get_object_or_404(Post, pk=pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post_obj
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added.')
        return redirect('post_detail', pk=pk)


class DeleteCommentView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=pk)
        post_pk = comment.post.pk
        if comment.author == request.user:
            comment.delete()
            messages.success(request, 'Comment deleted.')
        return redirect('post_detail', pk=post_pk)


class ToggleLikeView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        post_obj = get_object_or_404(Post, pk=pk)
        like_qs = Like.objects.filter(post=post_obj, user=request.user)
        if like_qs.exists():
            like_qs.delete()
            liked = False
        else:
            Like.objects.create(post=post_obj, user=request.user)
            liked = True
        return JsonResponse({'liked': liked, 'total_likes': post_obj.total_likes()})


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'core/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['posts'] = user.posts.all()
        context['is_following'] = Follow.objects.filter(follower=self.request.user, following=user).exists()
        context['followers_count'] = user.followers_set.count()
        context['following_count'] = user.following_set.count()
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'core/edit_profile.html'

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_success_url(self):
        messages.success(self.request, 'Profile updated successfully!')
        return reverse_lazy('profile', kwargs={'username': self.request.user.username})


class FollowToggleView(LoginRequiredMixin, View):
    def post(self, request, username, *args, **kwargs):
        user_to_follow = get_object_or_404(User, username=username)
        if user_to_follow == request.user:
            return JsonResponse({'error': 'You cannot follow yourself'}, status=400)
            
        follow_qs = Follow.objects.filter(follower=request.user, following=user_to_follow)
        if follow_qs.exists():
            follow_qs.delete()
            is_following = False
        else:
            Follow.objects.create(follower=request.user, following=user_to_follow)
            is_following = True
            
        return JsonResponse({
            'is_following': is_following,
            'followers_count': user_to_follow.followers_set.count()
        })


class FollowersListView(LoginRequiredMixin, ListView):
    template_name = 'core/followers_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return User.objects.filter(followers_set__following=user)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_type'] = 'Followers'
        context['profile_user'] = get_object_or_404(User, username=self.kwargs.get('username'))
        return context


class FollowingListView(LoginRequiredMixin, ListView):
    template_name = 'core/followers_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return User.objects.filter(following_set__follower=user)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['list_type'] = 'Following'
        context['profile_user'] = get_object_or_404(User, username=self.kwargs.get('username'))
        return context


class SearchView(LoginRequiredMixin, ListView):
    template_name = 'core/search_results.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            return User.objects.filter(
                Q(username__icontains=query) | 
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query)
            )
        return User.objects.none()
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

class InboxView(LoginRequiredMixin, ListView):
    template_name = 'core/inbox.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        return self.request.user.conversations.all()

class ConversationDetailView(LoginRequiredMixin, DetailView):
    template_name = 'core/conversation.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        return self.request.user.conversations.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mark all messages from the other user as read
        conversation = self.get_object()
        conversation.messages.filter(is_read=False).exclude(sender=self.request.user).update(is_read=True)
        context['messages'] = conversation.messages.all()
        # Find the other participant for context (avatar, username, etc.)
        other_participant = conversation.participants.exclude(id=self.request.user.id).first()
        context['other_participant'] = other_participant
        return context

    def post(self, request, *args, **kwargs):
        conversation = self.get_object()
        content = request.POST.get('content')
        if content:
            from .models import Message
            Message.objects.create(conversation=conversation, sender=request.user, content=content)
        return redirect('conversation_detail', pk=conversation.pk)

class StartConversationView(LoginRequiredMixin, View):
    def get(self, request, user_id, *args, **kwargs):
        target_user = get_object_or_404(User, id=user_id)
        if target_user == request.user:
            messages.error(request, "You cannot message yourself.")
            return redirect('profile', username=request.user.username)

        # Check if a 1-to-1 conversation already exists
        from .models import Conversation
        # We need a conversation that has both users and ONLY these two users
        conversations = request.user.conversations.filter(participants=target_user)
        for conv in conversations:
            if conv.participants.count() == 2:
                return redirect('conversation_detail', pk=conv.pk)

        # Create new conversation
        new_conv = Conversation.objects.create()
        new_conv.participants.add(request.user, target_user)
        return redirect('conversation_detail', pk=new_conv.pk)
