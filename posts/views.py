# posts/views.py
from rest_framework import generics
from .models import Post
from .serializers import PostSerializer

# List all published posts
class PostListView(generics.ListCreateAPIView):
    queryset = Post.objects.filter(is_published=True).order_by('-created_at')
    serializer_class = PostSerializer

    # Look up by slug instead of ID
    lookup_field = 'slug'

# Get a single post by slug
class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.filter(is_published=True)
    serializer_class = PostSerializer
lookup_field = 'slug'