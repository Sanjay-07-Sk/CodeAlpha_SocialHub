from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('', views.HomeFeedView.as_view(), name='home'),
    path('explore/', views.ExploreView.as_view(), name='explore'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    path('post/new/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('post/<int:pk>/like/', views.ToggleLikeView.as_view(), name='toggle_like'),
    path('post/<int:pk>/comment/', views.AddCommentView.as_view(), name='add_comment'),
    path('comment/<int:pk>/delete/', views.DeleteCommentView.as_view(), name='delete_comment'),
    
    path('profile/edit/me/', views.EditProfileView.as_view(), name='edit_profile'),
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('profile/<str:username>/followers/', views.FollowersListView.as_view(), name='followers_list'),
    path('profile/<str:username>/following/', views.FollowingListView.as_view(), name='following_list'),
    path('profile/<str:username>/follow/', views.FollowToggleView.as_view(), name='toggle_follow'),
    
    path('search/', views.SearchView.as_view(), name='search'),

    path('messages/', views.InboxView.as_view(), name='inbox'),
    path('messages/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('messages/start/<int:user_id>/', views.StartConversationView.as_view(), name='start_conversation'),
]
