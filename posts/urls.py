# posts/urls.py
from django.urls import path
from .views import (
    PostListView, PostDetailView, ImageUploadView, AIAgentView,
    MyPostsView, CategoryListView, TagListView
)
from .auth_views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    CurrentUserView,
    AuthorProfileView,
    CheckAuthView
)

urlpatterns = [
    # Post endpoints
    path('posts/', PostListView.as_view(), name='post-list'),
    path('posts/<slug:slug>/', PostDetailView.as_view(), name='post-detail'),
    path('my-posts/', MyPostsView.as_view(), name='my-posts'),
    path('upload-image/', ImageUploadView.as_view(), name='upload-image'),
    path('generate-ai-content/', AIAgentView.as_view(), name='generate-ai-content'),
    
    # Category and Tag endpoints
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('tags/', TagListView.as_view(), name='tag-list'),
    
    # Authentication endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('auth/login/', UserLoginView.as_view(), name='user-login'),
    path('auth/logout/', UserLogoutView.as_view(), name='user-logout'),
    path('auth/user/', CurrentUserView.as_view(), name='current-user'),
    path('auth/check/', CheckAuthView.as_view(), name='check-auth'),
    path('auth/profile/', AuthorProfileView.as_view(), name='author-profile'),
]