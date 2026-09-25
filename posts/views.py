# posts/views.py
import re
import json
from rest_framework import generics, status
from .models import Post, Category, Tag
from .serializers import PostSerializer, CategorySerializer, TagSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny

from django.core.files.storage import default_storage
from .prompts import build_blog_system_instruction
from .ai_agent import (
    generate_blog_content,
    generate_graphical_content,
    refine_text_snippet,
    enhance_blog_design,
    enhance_section_design,
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


def _extract_json_block(text):
    match = re.search(
        r'JSON_META:\s*(\{[\s\S]*?\})\s*(?:JSON_LD:|CODE:|$)',
        text,
        re.IGNORECASE
    )
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return {}
    return {}
def _extract_json_ld_block(text):
    match = re.search(
        r'JSON_LD:\s*(\{[\s\S]*?\})\s*(?:CODE:|$)',
        text,
        re.IGNORECASE
    )
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return {}
    return {}

# posts/views.py
class AIAgentView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        
        requirement = request.data.get('requirement')

        isStatic = request.data.get('isStatic')
        if(isStatic==True):
            return Response({
    "title": "AI Revolutionizes Healthcare: A Comprehensive Guide to 2026 Trends",
    "excerpt": "Discover how artificial intelligence is transforming healthcare in 2026, from diagnosis and treatment planning to drug discovery and patient care, and explore the benefits and ethical considerations of this revolution.\n\nJSON_META:\n{\n  \"meta_title\": \"AI in Healthcare 2026: Trends, Benefits, and Ethics\",\n  \"meta_description\": \"Learn about the latest AI applications in healthcare, including diagnosis, treatment planning, and patient care, and explore the benefits and ethical considerations of this technology.\",\n  \"keywords\": [\"AI in healthcare\", \"healthcare technology\", \"medical AI\", \"artificial intelligence in medicine\"]\n}\n\nJSON_LD:\n{\n  \"@context\": \"https://schema.org\",\n  \"@type\": \"BlogPosting\",\n  \"headline\": \"AI Revolutionizes Healthcare: A Comprehensive Guide to 2026 Trends\",\n  \"description\": \"Discover how artificial intelligence is transforming healthcare in 2026, from diagnosis and treatment planning to drug discovery and patient care, and explore the benefits and ethical considerations of this revolution.\",\n  \"author\": {\n    \"@type\": \"Person\",\n    \"name\": \"Vijay Gholve\"\n  },\n  \"publisher\": {\n    \"@type\": \"Organization\",\n    \"name\": \"Healthcare Tech\",\n    \"url\": \"https://example.com\"\n  }\n}",
    "generated_code": "<body id=\"editorial-body\">\n\n<!-- HERO -->\n<section id=\"editorial-hero-section\">\n <h1 id=\"editorial-hero-title\">AI Revolutionizes Healthcare: A Comprehensive Guide to 2026 Trends</h1>\n <p id=\"editorial-hero-subtitle\">Discover how artificial intelligence is transforming healthcare, from diagnosis and treatment planning to drug discovery and patient care.</p>\n</section>\n\n<!-- INTRO -->\n<section id=\"editorial-intro-section\">\n <h2 id=\"editorial-intro-title\">Introduction to AI in Healthcare</h2>\n <p id=\"editorial-intro-text-1\">Artificial intelligence (AI) is transforming the healthcare industry in unprecedented ways, from improving diagnosis and treatment planning to streamlining clinical workflows and enhancing patient care.</p>\n <p id=\"editorial-intro-text-2\">In this comprehensive guide, we will explore the latest AI applications in healthcare, discuss the benefits and ethical considerations of this technology, and examine the future of AI in medicine.</p>\n</section>\n\n<!-- CARD GRID -->\n<section id=\"editorial-card-section\">\n <h2 id=\"editorial-card-title\">AI Applications in Healthcare</h2>\n <p id=\"editorial-card-subtitle\">From diagnosis and treatment planning to drug discovery and patient care, AI is being applied in various ways to improve healthcare outcomes.</p>\n\n <div id=\"editorial-card-container\">\n\n <div id=\"editorial-card-1\">\n <h3 id=\"editorial-card-1-title\">Diagnosis and Imaging</h3>\n <p id=\"editorial-card-1-desc\">AI-powered algorithms can analyze medical images, such as X-rays and MRIs, to help doctors diagnose diseases more accurately and quickly.</p>\n </div>\n\n <div id=\"editorial-card-2\">\n <h3 id=\"editorial-card-2-title\">Treatment Planning and Personalized Medicine</h3>\n <p id=\"editorial-card-2-desc\">AI can help doctors develop personalized treatment plans tailored to individual patients' needs, taking into account their medical history, genetic profile, and lifestyle.</p>\n </div>\n\n <div id=\"editorial-card-3\">\n <h3 id=\"editorial-card-3-title\">Drug Discovery and Development</h3>\n <p id=\"editorial-card-3-desc\">AI can accelerate the drug discovery process by analyzing large datasets, identifying potential drug targets, and predicting the efficacy and safety of new compounds.</p>\n </div>\n\n </div>\n</section>\n\n<!-- QUOTE -->\n<section id=\"editorial-quote-section\">\n <blockquote id=\"editorial-quote-text\">\"AI has the potential to revolutionize healthcare by improving diagnosis, treatment, and patient outcomes, but it's crucial to address the ethical considerations and ensure that this technology is developed and used responsibly.\"</blockquote>\n <p id=\"editorial-quote-author\">- Dr. Vijay Gholve, Healthcare Expert</p>\n</section>\n\n<!-- STEPS -->\n<section id=\"editorial-steps-section\">\n <h2 id=\"editorial-steps-title\">Benefits of AI in Healthcare</h2>\n\n <div id=\"editorial-steps-1\">\n <h3 id=\"editorial-steps-1-title\">Improved Diagnosis and Treatment</h3>\n <p id=\"editorial-steps-1-desc\">AI can help doctors diagnose diseases more accurately and quickly, leading to better treatment outcomes and improved patient care.</p>\n </div>\n\n <div id=\"editorial-steps-2\">\n <h3 id=\"editorial-steps-2-title\">Enhanced Patient Experience</h3>\n <p id=\"editorial-steps-2-desc\">AI-powered chatbots and virtual assistants can help patients navigate the healthcare system, answer questions, and provide support, leading to a more personalized and satisfying experience.</p>\n </div>\n\n <div id=\"editorial-steps-3\">\n <h3 id=\"editorial-steps-3-title\">Increased Efficiency and Productivity</h3>\n <p id=\"editorial-steps-3-desc\">AI can automate routine administrative tasks, freeing up healthcare professionals to focus on more complex and high-value tasks, such as patient care and research.</p>\n </div>\n\n</section>\n\n<!-- STATS -->\n<section id=\"editorial-stats-section\">\n\n <div id=\"editorial-stats-1\">\n <div id=\"editorial-stats-1-number\">80%</div>\n <div id=\"editorial-stats-1-label\">of healthcare executives believe that AI will improve patient outcomes</div>\n </div>\n\n <div id=\"editorial-stats-2\">\n <div id=\"editorial-stats-2-number\">70%</div>\n <div id=\"editorial-stats-2-label\">of healthcare organizations are already using AI in some capacity</div>\n </div>\n\n <div id=\"editorial-stats-3\">\n <div id=\"editorial-stats-3-number\">50%</div>\n <div id=\"editorial-stats-3-label\">of patients are willing to share their medical data with AI-powered healthcare systems</div>\n </div>\n\n</section>\n\n<!-- DETAIL -->\n<section id=\"editorial-detail-section\">\n <h2 id=\"editorial-detail-title\">Ethical Considerations and Future Directions</h2>\n <p id=\"editorial-detail-text-1\">As AI continues to transform healthcare, it's essential to address the ethical considerations, such as data privacy, bias, and accountability, to ensure that this technology is developed and used responsibly.</p>\n <p id=\"editorial-detail-text-2\">The future of AI in healthcare will depend on the ability to balance the benefits of this technology with the need to protect patient rights and promote transparency and trust in the healthcare system.</p>\n</section>\n\n<!-- CTA -->\n<section id=\"editorial-cta-section\">\n <h2 id=\"editorial-cta-title\">Get Started with AI in Healthcare</h2>\n <p id=\"editorial-cta-subtitle\">Stay up-to-date with the latest developments in AI and healthcare, and explore how this technology can improve patient outcomes and transform the healthcare industry.</p>\n <button id=\"editorial-cta-button\">Learn More</button>\n</section>\n\n</body>",
    "meta_data": {
        "meta_title": "AI in Healthcare 2026: Trends, Benefits, and Ethics",
        "meta_description": "Learn about the latest AI applications in healthcare, including diagnosis, treatment planning, and patient care, and explore the benefits and ethical considerations of this technology.",
        "keywords": [
            "AI in healthcare",
            "healthcare technology",
            "medical AI",
            "artificial intelligence in medicine"
        ]
    },
    "json_ld": {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "AI Revolutionizes Healthcare: A Comprehensive Guide to 2026 Trends",
        "description": "Discover how artificial intelligence is transforming healthcare in 2026, from diagnosis and treatment planning to drug discovery and patient care, and explore the benefits and ethical considerations of this revolution.",
        "author": {
            "@type": "Person",
            "name": "Vijay Gholve"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Healthcare Tech",
            "url": "https://example.com"
        }
    }
}, status=status.HTTP_200_OK)
        if not requirement:
            return Response({"error": "Requirement is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
             
            raw_ai_response = generate_blog_content(requirement)
            
            # Robust Parsing
            title = ""
            excerpt = ""
            html_code = ""
            meta_data = {}
            json_ld = {}

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

            if "JSON_META:" in raw_ai_response:
                meta_data = _extract_json_block(raw_ai_response)

            if "JSON_LD:" in raw_ai_response:
                json_ld = _extract_json_ld_block(raw_ai_response)
             
            
            # Fallback: if no html_code was extracted, detect HTML in full response
            if not html_code:
                html_code = _extract_html(raw_ai_response)
                # If title grabbed the HTML, clean it
                if title and '<!DOCTYPE' in title:
                    title = re.split(r'\n|<!', title)[0].strip()

            if not meta_data:
                meta_data = {
                    "meta_title": title,
                    "meta_description": excerpt,
                    "keywords": [word for word in re.split(r'[\n,]+', requirement) if word.strip()][:8],
                }

            if not json_ld:
                json_ld = {
                    "@context": "https://schema.org",
                    "@type": "BlogPosting",
                    "headline": meta_data.get("meta_title") or title,
                    "description": meta_data.get("meta_description") or excerpt,
                    "keywords": meta_data.get("keywords") or [],
                }
            
            html_code = html_code.replace("```html", "").replace("```", "").strip()

            return Response({
                "title": title,
                "excerpt": excerpt,
                "generated_code": html_code,
                "meta_data": meta_data,
                "json_ld": json_ld,
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
class PostListUrlView(generics.ListCreateAPIView):
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

        content_type = request.data.get('content_type', 'blog').strip()

        try:
            enhanced = enhance_blog_design(html_content, content_type=content_type)
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


class EnhanceSectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        html_section = request.data.get('html_content', '').strip()
        if not html_section:
            return Response({"error": "html_content is required"}, status=status.HTTP_400_BAD_REQUEST)

        instructions = request.data.get('instructions', '').strip() or None
        content_type = request.data.get('content_type', 'blog').strip()

        try:
            enhanced = enhance_section_design(html_section, instructions=instructions, content_type=content_type)
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

