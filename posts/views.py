# posts/views.py
from rest_framework import generics
from .models import Post, Category, Tag
from .serializers import PostSerializer, CategorySerializer, TagSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
# posts/views.py
from rest_framework import status
from .ai_agent import generate_blog_content


# posts/views.py
class AIAgentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        requirement = request.data.get('requirement')
        if not requirement:
            return Response({"error": "Requirement is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            raw_ai_response = generate_blog_content(requirement)
            
            # Robust Parsing
            title = ""
            excerpt = ""
            html_code = ""

            # Extract Title
            if "TITLE:" in raw_ai_response:
                title = raw_ai_response.split("TITLE:")[1].split("EXCERPT:")[0].strip()
            
            # Extract Excerpt
            if "EXCERPT:" in raw_ai_response:
                excerpt = raw_ai_response.split("EXCERPT:")[1].split("CODE:")[0].strip()
            
            # Extract everything after "CODE:"
            if "CODE:" in raw_ai_response:
                html_code = raw_ai_response.split("CODE:")[1].strip()
            
            # Final cleanup of any rogue markdown tags
            html_code = html_code.replace("```html", "").replace("```", "").strip()

            return Response({
                "title": title,
                "excerpt": excerpt,
                "generated_code": html_code
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
    queryset = Post.objects.filter(status='published').order_by('-created_at')
    serializer_class = PostSerializer
    lookup_field = 'slug'
    
    def perform_create(self, serializer):
        # Automatically set the author to the logged-in user
        if self.request.user.is_authenticated:
            author = self.request.user.author_profile
            serializer.save(author=author, status='published')
        else:
            serializer.save()

# Get a single post by slug
class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = 'slug'


# Get user's own posts
class MyPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user.author_profile).order_by('-created_at')


# Category list view
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# Tag list view  
class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

