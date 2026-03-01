# posts/views.py
import re
from rest_framework import generics, status
from .models import Post, Category, Tag
from .serializers import PostSerializer, CategorySerializer, TagSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.core.files.storage import default_storage
from .ai_agent import (
    generate_blog_content,
    generate_graphical_content,
    refine_text_snippet,
    enhance_blog_design,
    REFINE_COMMANDS,
    AIAgentRateLimitError,
    AIAgentError,
)


def _extract_html(text):
    """Extract HTML from AI response, handling missing markers."""
    text = text.replace("```html", "").replace("```", "").strip()
    # Try to find the HTML document
    match = re.search(r'(<!DOCTYPE html[\s\S]*</html>)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: find any block starting with <html or <body or <div
    match = re.search(r'(<(?:html|body|div|section)[\s\S]*)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


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
                title_block = raw_ai_response.split("TITLE:")[1]
                if "EXCERPT:" in title_block:
                    title = title_block.split("EXCERPT:")[0].strip()
                elif "CODE:" in title_block:
                    title = title_block.split("CODE:")[0].strip()
                else:
                    # Title goes up to first newline or HTML tag
                    title = re.split(r'\n|<', title_block)[0].strip()
            
            # Extract Excerpt
            if "EXCERPT:" in raw_ai_response:
                excerpt_block = raw_ai_response.split("EXCERPT:")[1]
                if "CODE:" in excerpt_block:
                    excerpt = excerpt_block.split("CODE:")[0].strip()
                else:
                    excerpt = re.split(r'\n\n|<', excerpt_block)[0].strip()
            
            if "CODE:" in raw_ai_response:
                html_code = raw_ai_response.split("CODE:")[1].strip()
            
            # Fallback: if no html_code was extracted, detect HTML in full response
            if not html_code:
                html_code = _extract_html(raw_ai_response)
                # If title grabbed the HTML, clean it
                if title and '<!DOCTYPE' in title:
                    title = re.split(r'\n|<!', title)[0].strip()
            
            html_code = html_code.replace("```html", "").replace("```", "").strip()

            return Response({
                "title": title,
                "excerpt": excerpt,
                "generated_code": html_code
            }, status=status.HTTP_200_OK)
            
        except AIAgentRateLimitError as exc:
            detail = str(exc)
            retry_after = None

            if "||retry_after=" in detail:
                detail, retry_raw = detail.split("||retry_after=", 1)
                try:
                    retry_after = int(retry_raw)
                except ValueError:
                    retry_after = None

            payload = {
                "error": "AI service is currently rate limited. Please wait a moment and try again.",
                "detail": detail,
            }
            if retry_after is not None:
                payload["retry_after_seconds"] = retry_after

            return Response(
                payload,
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except AIAgentError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GraphicalAIView(APIView):
    """Generate graphical/infographic HTML from a user prompt."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        requirement = request.data.get('requirement')
        if not requirement:
            return Response({"error": "Requirement is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            raw_ai_response = generate_graphical_content(requirement)

            title = ""
            html_code = ""

            if "TITLE:" in raw_ai_response:
                title_block = raw_ai_response.split("TITLE:")[1]
                if "CODE:" in title_block:
                    title = title_block.split("CODE:")[0].strip()
                else:
                    title = re.split(r'\n|<', title_block)[0].strip()

            if "CODE:" in raw_ai_response:
                html_code = raw_ai_response.split("CODE:")[1].strip()

            # Fallback: if no html_code was extracted, detect HTML in full response
            if not html_code:
                html_code = _extract_html(raw_ai_response)
                if title and '<!DOCTYPE' in title:
                    title = re.split(r'\n|<!', title)[0].strip()

            html_code = html_code.replace("```html", "").replace("```", "").strip()

            return Response({
                "title": title,
                "generated_code": html_code,
            }, status=status.HTTP_200_OK)

        except AIAgentRateLimitError as exc:
            detail = str(exc)
            retry_after = None
            if "||retry_after=" in detail:
                detail, retry_raw = detail.split("||retry_after=", 1)
                try:
                    retry_after = int(retry_raw)
                except ValueError:
                    retry_after = None
            payload = {
                "error": "AI service is currently rate limited. Please wait a moment and try again.",
                "detail": detail,
            }
            if retry_after is not None:
                payload["retry_after_seconds"] = retry_after
            return Response(payload, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except AIAgentError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


# Tag list view — supports ?category=<id> filtering
class TagListView(generics.ListAPIView):
    serializer_class = TagSerializer

    def get_queryset(self):
        qs = Tag.objects.all()
        category_id = self.request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs


# AI Refine Text — accepts text_snippet + command, returns refined text
class EnhanceDesignView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        html_content = request.data.get('html_content', '').strip()
        if not html_content:
            return Response({"error": "html_content is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            enhanced = enhance_blog_design(html_content)
            return Response({
                "enhanced_code": enhanced,
            }, status=status.HTTP_200_OK)

        except AIAgentRateLimitError as exc:
            detail = str(exc)
            retry_after = None
            if "||retry_after=" in detail:
                detail, retry_raw = detail.split("||retry_after=", 1)
                try:
                    retry_after = int(retry_raw)
                except ValueError:
                    retry_after = None
            payload = {
                "error": "AI service rate limited. Please wait and try again.",
                "detail": detail,
            }
            if retry_after is not None:
                payload["retry_after_seconds"] = retry_after
            return Response(payload, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except AIAgentError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefineTextView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return available refine commands."""
        commands = [
            {"key": k, "label": k.replace("_", " ").title()}
            for k in REFINE_COMMANDS
        ]
        return Response({"commands": commands}, status=status.HTTP_200_OK)

    def post(self, request):
        text_snippet = request.data.get('text_snippet', '').strip()
        command = request.data.get('command', '').strip()

        if not text_snippet:
            return Response({"error": "text_snippet is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not command:
            return Response({"error": "command is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refined = refine_text_snippet(text_snippet, command)
            return Response({
                "original": text_snippet,
                "command": command,
                "refined_text": refined.strip(),
            }, status=status.HTTP_200_OK)

        except AIAgentRateLimitError as exc:
            detail = str(exc)
            retry_after = None
            if "||retry_after=" in detail:
                detail, retry_raw = detail.split("||retry_after=", 1)
                try:
                    retry_after = int(retry_raw)
                except ValueError:
                    retry_after = None
            payload = {
                "error": "AI service rate limited. Please wait and try again.",
                "detail": detail,
            }
            if retry_after is not None:
                payload["retry_after_seconds"] = retry_after
            return Response(payload, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except AIAgentError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

