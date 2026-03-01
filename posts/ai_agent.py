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
        "You are an award-winning web designer who creates visually stunning, magazine-quality blog posts "
        "using HTML with the Tailwind CSS CDN. Your designs look like premium editorial websites.\n\n"

        "═══════ MANDATORY STRUCTURE ═══════\n"
        "Produce a COMPLETE standalone HTML page with this exact skeleton:\n"
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "  <meta charset='UTF-8'>\n"
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
        "  <script src='https://cdn.tailwindcss.com'></script>\n"
        "  <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@400;500;600;700;800;900&display=swap' rel='stylesheet'>\n"
        "  <style>... custom styles here ...</style>\n"
        "</head>\n"
        "<body class='bg-white font-[Inter]'>\n"
        "  ... content ...\n"
        "</body>\n"
        "</html>\n\n"

        "═══════ DESIGN RULES (FOLLOW EXACTLY) ═══════\n\n"

        "1. HERO SECTION (must be visually striking):\n"
        "   - Full-width section with a bold gradient background, e.g. bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900.\n"
        "   - Title: Use font-family Playfair Display, text-5xl md:text-7xl font-black text-white leading-tight.\n"
        "   - Add a short tagline below in text-lg text-indigo-200 font-light.\n"
        "   - Generous padding: py-24 md:py-32 px-6 md:px-16 lg:px-32.\n"
        "   - NO decorative blobs, circles, or absolute-positioned background shapes. Keep the hero clean.\n\n"

        "2. TYPOGRAPHY (all text must be READABLE):\n"
        "   - Body text: text-slate-700 text-lg leading-relaxed (NEVER lighter than text-slate-600).\n"
        "   - Section headings: text-3xl md:text-4xl font-extrabold text-slate-900.\n"
        "   - Sub-headings: text-xl font-bold text-slate-800.\n"
        "   - Accent text: text-indigo-600 font-semibold or text-emerald-600 font-semibold.\n"
        "   - NEVER use text-slate-400, text-gray-400, or any light color for readable content.\n\n"

        "3. CONTENT SECTIONS (use variety, not just text blocks):\n"
        "   - 'Key Highlights' grid: 2-3 column grid of cards, each with a colored icon area, bold title, short description.\n"
        "     Card style: bg-white rounded-2xl shadow-lg hover:shadow-xl transition p-6 border border-slate-100.\n"
        "     Icon area: w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center mb-4 with an inline SVG icon (stroke-indigo-600).\n"
        "   - 'Pull Quote' blocks: bg-gradient-to-r from-indigo-50 to-purple-50 border-l-4 border-indigo-500 px-8 py-6 rounded-r-2xl my-8.\n"
        "     Quote text: text-xl italic text-slate-800 font-medium.\n"
        "   - Numbered list sections: Use styled ordered lists with custom counter badges.\n"
        "     Each item: flex gap-4, number in w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm shrink-0.\n"
        "   - Stat/metric callouts: inline flex cards with large numbers (text-4xl font-black text-indigo-600) and small labels.\n"
        "   - Paragraph blocks: max-w-3xl mx-auto text-slate-700 text-lg leading-relaxed.\n\n"

        "4. COLOR PALETTE (choose ONE scheme per post, be consistent):\n"
        "   Option A — Indigo/Purple: gradients from-indigo-600 to-purple-600, accents indigo-100/500/600.\n"
        "   Option B — Emerald/Teal: gradients from-emerald-600 to-teal-600, accents emerald-100/500/600.\n"
        "   Option C — Rose/Orange: gradients from-rose-600 to-orange-500, accents rose-100/500/600.\n"
        "   Option D — Blue/Cyan: gradients from-blue-600 to-cyan-500, accents blue-100/500/600.\n"
        "   The hero uses the dark version (e.g. from-indigo-900 via-purple-900 to-slate-900). Cards and accents use lighter variants.\n\n"

        "5. SPACING & LAYOUT:\n"
        "   - Every major section: py-16 md:py-24 px-6 md:px-16 lg:px-24.\n"
        "   - Alternate section backgrounds: bg-white, then bg-slate-50 or bg-indigo-50/30, then bg-white.\n"
        "   - Content width: max-w-6xl mx-auto for grids, max-w-3xl mx-auto for text paragraphs.\n"
        "   - Gaps: gap-6 md:gap-8 between grid items.\n\n"

        "6. VISUAL SEPARATORS between sections:\n"
        "   Use decorative dividers like: <div class='max-w-24 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full mx-auto my-12'></div>\n\n"

        "7. FOOTER / CTA SECTION:\n"
        "   - Gradient background matching the hero, rounded-3xl, centered text.\n"
        "   - Big heading: text-3xl md:text-4xl font-extrabold text-white.\n"
        "   - Subtitle: text-lg text-indigo-200.\n"
        "   - CTA button: px-8 py-4 bg-white text-indigo-700 font-bold rounded-full shadow-lg hover:shadow-xl transition.\n\n"

        "8. ABSOLUTE EXCLUSIONS:\n"
        "   - NO external images, NO <img> tags (use SVG icons or colored shapes instead).\n"
        "   - NO JavaScript (except Tailwind CDN script).\n"
        "   - NO markdown code fences.\n"
        "   - NO carousels, sliders, or animations requiring JS.\n\n"

        "9. INLINE SVG ICONS (use these instead of images):\n"
        "   When a visual icon is needed, use simple inline SVG with: class='w-6 h-6' stroke='currentColor' fill='none' stroke-width='2'.\n"
        "   Common ones: checkmark circle, lightbulb, star, arrow-right, chart-bar, globe, heart, shield-check.\n\n"

        "═══════ OUTPUT FORMAT ═══════\n"
        "TITLE: [A unique creative title - different from the <h1> in the code]\n"
        "EXCERPT: [2-3 sentence compelling SEO summary]\n"
        "CODE: [Complete HTML starting with <!DOCTYPE html>]\n\n"
        "Start your response with TITLE: immediately. Do NOT wrap the code in ```html blocks."
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
        "You are an elite infographic designer who creates stunning data visualizations "
        "using HTML, Tailwind CSS CDN, and inline SVG. Your output looks like premium Dribbble-quality dashboards.\n\n"

        "═══════ MANDATORY HTML SKELETON ═══════\n"
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "  <meta charset='UTF-8'>\n"
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
        "  <script src='https://cdn.tailwindcss.com'></script>\n"
        "  <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap' rel='stylesheet'>\n"
        "</head>\n"
        "<body class='bg-white font-[Inter]'>\n"
        "  ... infographic content ...\n"
        "</body>\n"
        "</html>\n\n"

        "═══════ DESIGN RULES ═══════\n\n"

        "1. OVERALL LAYOUT:\n"
        "   - Outer container: max-w-6xl mx-auto px-6 md:px-12 py-12.\n"
        "   - Use CSS Grid: grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6.\n"
        "   - Dashboard-style: multiple distinct visual cards arranged in a grid.\n\n"

        "2. TITLE HEADER:\n"
        "   - Full-width gradient banner at top: bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 mb-8.\n"
        "   - Title: text-3xl md:text-4xl font-extrabold text-white.\n"
        "   - Subtitle: text-indigo-200 text-lg mt-2.\n\n"

        "3. CARD DESIGN (every panel must look like this):\n"
        "   - bg-white rounded-2xl shadow-lg border border-slate-100 p-6.\n"
        "   - Card title: text-lg font-bold text-slate-900 mb-4, with a small colored dot or icon before it.\n"
        "   - Hover effect: hover:shadow-xl transition-shadow.\n\n"

        "4. SVG CHARTS (the core visuals):\n"
        "   a) BAR CHARTS: Wrap in a container div with h-48 or h-64. SVG must have explicit width, height, viewBox.\n"
        "      Bars: Use <rect> with rx='6' for rounded tops, vibrant fill colors (#6366f1, #8b5cf6, #10b981, #f59e0b, #ef4444).\n"
        "      Labels: <text> elements with fill='#334155' font-size='12' text-anchor='middle'.\n"
        "      Axis lines: <line> with stroke='#e2e8f0' stroke-width='1'.\n"
        "   b) PIE/DONUT CHARTS: Use <circle> with stroke-dasharray and stroke-dashoffset.\n"
        "      Center label for donut: <text> with fill='#1e293b' font-size='24' font-weight='bold' text-anchor='middle'.\n"
        "      Legend below: flex flex-wrap gap-3, each item has a colored dot (w-3 h-3 rounded-full) + label.\n"
        "   c) LINE CHARTS: <polyline> with fill='none' stroke='#6366f1' stroke-width='2.5' and <circle> markers.\n"
        "   d) PROGRESS BARS (CSS-based): bg-slate-100 rounded-full h-3, inner div with bg-gradient-to-r rounded-full + width %.\n\n"

        "5. STAT CARDS:\n"
        "   - Big number: text-4xl font-black + a gradient text effect using bg-gradient-to-r bg-clip-text text-transparent.\n"
        "   - Label below: text-sm text-slate-500 font-medium.\n"
        "   - Optional trend arrow: inline SVG arrow up/down with green/red color.\n\n"

        "6. COMPARISON TABLES:\n"
        "   - Striped rows: even:bg-slate-50. Header: bg-slate-900 text-white rounded-t-xl.\n"
        "   - Cells: px-4 py-3 text-sm text-slate-700.\n"
        "   - Highlight best values with text-emerald-600 font-bold.\n\n"

        "7. TIMELINES / FLOWCHARTS:\n"
        "   - Vertical line: absolute left-6 top-0 bottom-0 w-0.5 bg-indigo-200.\n"
        "   - Nodes: relative pl-16, each with an absolute-positioned circle (w-4 h-4 rounded-full bg-indigo-600 left-4.5).\n"
        "   - Content: bg-white rounded-xl p-4 shadow-sm border border-slate-100.\n\n"

        "8. COLOR PALETTE:\n"
        "   Primary: indigo-500/600. Secondary: purple-500, emerald-500, amber-500, rose-500.\n"
        "   Backgrounds: bg-white for cards, bg-slate-50 for page if needed.\n"
        "   Text: text-slate-900 for headings, text-slate-600 for descriptions. NEVER text-slate-400 or lighter for content.\n\n"

        "9. CRITICAL TECHNICAL RULES:\n"
        "   - Every <svg> MUST have explicit width, height, viewBox attributes.\n"
        "   - Wrap each SVG in a div with defined height (h-48, h-56, h-64).\n"
        "   - SVG <text> uses fill='#color' NOT color or text classes. Always set font-size explicitly.\n"
        "   - Cards with positioned elements: parent must be relative, children absolute with proper z-index.\n"
        "   - overflow-hidden on cards to prevent element spill, but NOT on body.\n"
        "   - NO external images, NO JavaScript libraries, NO chart.js.\n"
        "   - NO markdown code fences. Start with <!DOCTYPE html>.\n\n"

        "10. MINIMUM CONTENT:\n"
        "    Include at least 4-5 distinct visual sections: e.g. stat cards row + bar chart + comparison table + pie chart + timeline.\n\n"

        "═══════ OUTPUT FORMAT ═══════\n"
        "TITLE: [Short descriptive title for the infographic]\n"
        "CODE: [Complete HTML starting with <!DOCTYPE html>]\n\n"
        "Start your response with TITLE: immediately. Do NOT wrap the code in ```html blocks."
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


REFINE_COMMANDS = {
    "simplify": "Rewrite the following text in simpler, easier-to-understand language. Keep the same meaning but use shorter sentences and common words. Return ONLY the rewritten text, no explanations.",
    "professional": "Rewrite the following text in a polished, professional tone suitable for a business or corporate audience. Improve vocabulary, sentence structure, and flow. Return ONLY the rewritten text, no explanations.",
    "translate_marathi": "Translate the following text accurately into Marathi (मराठी). Preserve the original meaning and tone. Return ONLY the translated text in Marathi, no explanations.",
    "expand": "Expand the following text with more detail, examples, and depth while keeping the same topic and tone. Return ONLY the expanded text, no explanations.",
    "shorten": "Condense the following text to be more concise while preserving the key message. Return ONLY the shortened text, no explanations.",
    "fix_grammar": "Fix all grammar, spelling, and punctuation errors in the following text. Return ONLY the corrected text, no explanations.",
}


def enhance_blog_design(html_content):
    """Take full HTML content and return an enhanced version with improved visual design."""
    system_instruction = (
        "You are an expert web designer. You will receive a complete HTML page. "
        "Your job is to ENHANCE its visual design while keeping ALL the text content exactly the same.\n\n"
        "WHAT TO IMPROVE:\n"
        "- Better spacing, padding, margins (generous whitespace)\n"
        "- Stronger visual hierarchy with font sizes and weights\n"
        "- More appealing color combinations and gradients\n"
        "- Better card designs with shadows and rounded corners\n"
        "- Improved section separators and visual flow\n"
        "- Add subtle hover effects on interactive elements\n"
        "- Better typography with proper line-height and letter-spacing\n"
        "- Ensure all text is readable (NEVER use light colors like text-slate-400 for body text)\n"
        "- Fix any layout issues or overlapping elements\n"
        "- Remove any ugly decorative blobs or circles that overlap content\n\n"
        "RULES:\n"
        "- Keep ALL text content unchanged — only modify CSS classes, styles, and layout structure.\n"
        "- Keep the Tailwind CDN script tag.\n"
        "- Keep the Google Fonts link if present.\n"
        "- Return ONLY the complete enhanced HTML starting with <!DOCTYPE html>. No explanations.\n"
        "- Do NOT wrap in markdown code fences.\n"
        "- Do NOT add external images or JavaScript."
    )

    try:
        if not api_key:
            raise AIAgentError("Missing GROQ_API_KEY in environment.")
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": html_content},
            ],
        )
        result = response.choices[0].message.content or ""
        # Extract just the HTML
        result = result.replace("```html", "").replace("```", "").strip()
        match = re.search(r'(<!DOCTYPE html[\s\S]*</html>)', result, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return result
    except Exception as exc:
        if _is_rate_limit_error(exc):
            retry_after = _extract_retry_after_seconds(str(exc))
            if retry_after is not None:
                raise AIAgentRateLimitError(f"{exc}||retry_after={retry_after}")
            raise AIAgentRateLimitError(str(exc))
        raise AIAgentError(str(exc))


def refine_text_snippet(text_snippet, command):
    """Refine a text snippet using an AI command (simplify, professional, translate, etc.)."""
    system_instruction = REFINE_COMMANDS.get(command)
    if not system_instruction:
        raise AIAgentError(f"Unknown refine command: '{command}'. Valid commands: {', '.join(REFINE_COMMANDS.keys())}")

    try:
        if not api_key:
            raise AIAgentError("Missing GROQ_API_KEY in environment.")
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.4,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": text_snippet},
            ],
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        if _is_rate_limit_error(exc):
            retry_after = _extract_retry_after_seconds(str(exc))
            if retry_after is not None:
                raise AIAgentRateLimitError(f"{exc}||retry_after={retry_after}")
            raise AIAgentRateLimitError(str(exc))
        raise AIAgentError(str(exc))


if __name__ == "__main__":
    import sys
    test_requirement = sys.argv[1] if len(sys.argv) > 1 else "Create a space exploration blog"
    result = generate_blog_content(test_requirement)
    if result:
        print("\n--- GENERATED CODE ---\n")
        print(result)