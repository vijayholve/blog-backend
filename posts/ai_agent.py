# posts/ai_agent.py
import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class AIAgentRateLimitError(Exception):
    """Raised when the upstream AI API responds with a rate limit (429)."""


class AIAgentError(Exception):
    """Raised for non-rate-limit AI errors."""


def _is_rate_limit_error(exc):
    code = getattr(exc, "code", None)
    status_code = getattr(exc, "status_code", None)
    status = getattr(exc, "status", None)
    message = str(exc).upper()

    if code == 429 or status_code == 429 or status == "RESOURCE_EXHAUSTED":
        return True

    return "429" in message or "RATE LIMIT" in message or "RESOURCE_EXHAUSTED" in message


def _extract_retry_after_seconds(exc_message):
    match = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", exc_message, re.IGNORECASE)
    if not match:
        return None
    try:
        return int(float(match.group(1)))
    except (TypeError, ValueError):
        return None


# Initialize the client (Groq — free, OpenAI-compatible)
api_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)



def generate_blog_content(user_requirement):
    system_instruction = (
        "You are a world-class editorial web designer specializing in Swiss Design and Digital Minimalism. Generate a blog post using HTML and Tailwind CSS.\n\n"
        "STRICT VISUAL REQUIREMENTS:\n"
        "1. Layout & Space: Use a pure white background (bg-white). Implement aggressive white space using 'py-32 px-6 md:px-24'. Use an asymmetric layout (e.g., md:grid-cols-12 with offsets) to create a premium, non-generic look.\n"
        "2. Typography: ALL text must use dark colors for maximum contrast on white backgrounds. Use text-slate-950 for body text, text-slate-900 for headings. Allowed accent colors: text-blue-800, text-yellow-800, text-red-800. NEVER use light colors like text-slate-400 or text-gray-500 for main content.\n"
        "3. Hierarchy: Headings must be massive and tight (text-6xl to text-9xl, leading-none, tracking-tighter) with text-slate-950 or text-slate-900. Highlight critical insights using 'bg-yellow-100 px-2 rounded-sm text-slate-950' or 'text-blue-700 font-black italic'.\n"
        "4. Editorial Elements: Include \"Pull Quotes\" with large decorative quotation marks and vertical \"Running Heads\" or \"Sidebar Labels\" for sections. All text must be dark (text-slate-900 or darker).\n"
        "5. Containers: Use ultra-modern 'rounded-[3rem]' or 'rounded-[4rem]' for section blocks. Add a very subtle 'border border-slate-100' or 'shadow-[0_32px_64px_-15px_rgba(0,0,0,0.05)]' for depth.\n"
        "6. Content Structure:\n"
        "   - A cinematic Hero section with dark text (No images).\n"
        "   - An \"At a Glance\" takeaways grid with hardcoded Lucide-style SVGs using dark strokes.\n"
        "   - A deep-dive body section with high-contrast dark text (text-slate-950).\n"
        "   - A massive, centered Summary/CTA with dark text.\n"
        "7. Exclusions: NO image sliders, NO carousels, and NO external images. Use colored geometric placeholders or SVG patterns if a visual break is needed.\n"
        "8. Output Format: Output ONLY raw HTML/Tailwind code. Do NOT use markdown code blocks (```html). Start directly with <!DOCTYPE html>.\n"
        "9. Color Consistency: The entire page must have bg-white at the root level. ALL text content must use dark colors (text-slate-900, text-slate-950) for readability. Only use lighter colors for subtle borders or backgrounds, NEVER for text.\n\n"
        "RESPONSE FORMAT:\n"
        "TITLE: [Unique Creative Title - Must be different from the <h1> in the code]\n"
        "EXCERPT: [Compelling SEO Summary]\n"
        "CODE: [Full HTML/Tailwind content starting with <!DOCTYPE html>]"
    )
    
    try:
        if not api_key:
            raise AIAgentError("Missing GROQ_API_KEY in environment. Get one free at https://console.groq.com")
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_requirement},
            ],
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        if _is_rate_limit_error(exc):
            print(f"AI Rate Limit: {exc}")
            retry_after = _extract_retry_after_seconds(str(exc))
            if retry_after is not None:
                raise AIAgentRateLimitError(f"{exc}||retry_after={retry_after}")
            raise AIAgentRateLimitError(str(exc))
        print(f"AI Error: {exc}")
        raise AIAgentError(str(exc))
def generate_graphical_content(user_requirement):
    """Generate an interactive graphical/infographic HTML explanation using AI."""
    system_instruction = (
        "You are an elite data-visualization and infographic designer. "
        "Generate a SINGLE self-contained HTML page using Tailwind CSS and inline SVG that "
        "visually explains the topic the user describes.\n\n"
        "STRICT REQUIREMENTS:\n"
        "1. The output must be a rich GRAPHICAL representation — NOT a normal blog post. "
        "   Use charts (bar, pie, line built with SVG), flowcharts, timelines, comparison tables, "
        "   icon grids, progress bars, stat cards, process diagrams, or any combination.\n"
        "2. Every data point must have a clear label and value in dark text (text-slate-900/950).\n"
        "3. Use vibrant but professional accent colors: blue-500, indigo-500, emerald-500, amber-500, rose-500.\n"
        "4. Background must be white (bg-white). All text must be dark for contrast.\n"
        "5. Layout: Use CSS Grid or Flexbox for a dashboard-style multi-panel layout. "
        "   Include at least 3 distinct visual sections.\n"
        "6. Include a bold title section at the top describing what the graphic explains.\n"
        "7. All graphics must be built with inline SVG or pure CSS — NO external images, NO JavaScript libraries, NO chart.js.\n"
        "8. Make it responsive with Tailwind breakpoints.\n"
        "9. Output Format: Output ONLY raw HTML/Tailwind code. Do NOT use markdown code blocks. "
        "   Start directly with <!DOCTYPE html>.\n\n"
        "CRITICAL STYLING & LAYOUT RULES:\n"
        "10. MARGINS & PADDING: Every section/card must have proper spacing. Use p-6 or p-8 inside cards. "
        "    Use gap-6 or gap-8 between grid/flex children. Outer container must have px-6 md:px-12 lg:px-24 py-12.\n"
        "11. Z-INDEX: If using any overlapping elements, layered shapes, or positioned items, explicitly set z-index "
        "    (z-0, z-10, z-20, z-30) so nothing clips or hides behind another. Avoid negative z-index.\n"
        "12. OVERFLOW: Set overflow-hidden on cards/containers to prevent SVG or absolute elements from spilling out. "
        "    The root <body> must NOT have overflow-hidden.\n"
        "13. SVG SIZING: Every <svg> must have explicit width, height, and viewBox attributes. "
        "    Wrap SVGs in a container div with a fixed height (e.g., h-48, h-64) and use w-full h-full on the SVG.\n"
        "14. TEXT INSIDE SVG: All <text> elements inside SVG must use fill (not color). "
        "    Use fill='#0f172a' (slate-900). Set font-size explicitly (e.g., font-size='14'). "
        "    Use text-anchor='middle' for centered labels. Ensure text does not overflow the SVG viewBox.\n"
        "15. POSITIONING: Prefer static/relative layouts. If using absolute positioning, the parent MUST be relative. "
        "    Never use fixed positioning. Ensure nothing overlaps or cuts off content.\n"
        "16. CARD CONSISTENCY: All dashboard cards must have equal border-radius (rounded-2xl), "
        "    consistent shadow (shadow-lg or shadow-xl), and uniform internal padding (p-6).\n"
        "17. CHART ELEMENTS: Bar chart bars should have rounded tops (rx='4'). Pie/donut slices should have "
        "    distinct colors and a legend below. Line charts need axis labels and grid lines.\n"
        "18. RESPONSIVE: Use grid-cols-1 md:grid-cols-2 lg:grid-cols-3 for card grids. "
        "    Text should scale: text-2xl md:text-4xl for headings.\n\n"
        "RESPONSE FORMAT:\n"
        "TITLE: [Short descriptive title for the infographic]\n"
        "CODE: [Full HTML/Tailwind content starting with <!DOCTYPE html>]"
    )

    try:
        if not api_key:
            raise AIAgentError("Missing GROQ_API_KEY in environment. Get one free at https://console.groq.com")
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_requirement},
            ],
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        if _is_rate_limit_error(exc):
            print(f"AI Rate Limit: {exc}")
            retry_after = _extract_retry_after_seconds(str(exc))
            if retry_after is not None:
                raise AIAgentRateLimitError(f"{exc}||retry_after={retry_after}")
            raise AIAgentRateLimitError(str(exc))
        print(f"AI Error: {exc}")
        raise AIAgentError(str(exc))


if __name__ == "__main__":
    import sys
    test_requirement = sys.argv[1] if len(sys.argv) > 1 else "Create a space exploration blog"
    result = generate_blog_content(test_requirement)
    if result:
        print("\n--- GENERATED CODE ---\n")
        print(result)