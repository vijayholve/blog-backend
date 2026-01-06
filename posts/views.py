# posts/views.py
from rest_framework import generics
from .models import Post
from .serializers import PostSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage

class ImageUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.data.get('image')
        # Save the file to the media folder
        file_name = default_storage.save(f"blog_images/{file_obj.name}", file_obj)
        file_url = request.build_absolute_uri(default_storage.url(file_name))
        
        return Response({'url': file_url})
# List all published posts
class PostListView(generics.ListCreateAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer

    # Look up by slug instead of ID
    lookup_field = 'slug'

# Get a single post by slug
class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = 'slug'

