# posts/views.py
from rest_framework import generics
from .models import Post
from .serializers import PostSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
# posts/views.py
from rest_framework import status
from .ai_agent import generate_blog_content


# posts/views.py
class AIAgentView(APIView):
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
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer

    # Look up by slug instead of ID
    lookup_field = 'slug'

# Get a single post by slug
class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = 'slug'

