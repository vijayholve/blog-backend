# posts/urls.py
from django.urls import path
from .views import PostListView, PostDetailView ,ImageUploadView ,AIAgentView

urlpatterns = [
    path('posts/', PostListView.as_view(), name='post-list'),
    path('posts/<slug:slug>/', PostDetailView.as_view(), name='post-detail'),
    path('upload-image/', ImageUploadView.as_view(), name='upload-image'),
path('generate-ai-content/', AIAgentView.as_view(), name='generate-ai-content'),
]