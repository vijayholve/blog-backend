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


# ── Post-processing sanitizer ──────────────────────────────────────────────
def _sanitize_blog_html(html):
    """Force-fix common bad patterns the LLM produces despite instructions."""
    if not html:
        return html

    # 1. Remove <style>...</style> blocks entirely
    html = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html, flags=re.IGNORECASE)

    # 2. Fix body class — ensure bg-white, remove bg-gray-*
    html = re.sub(
        r"<body[^>]*class=['\"]([^'\"]*)['\"]" ,
        lambda m: m.group(0).replace(m.group(1), re.sub(r'bg-gray-\S+', 'bg-white', m.group(1)))
        if 'bg-gray' in m.group(1)
        else m.group(0),
        html,
    )

    # 3. Remove h-screen from ALL elements
    html = re.sub(r'\bh-screen\b', '', html)

    # 4. Remove hover:scale-* and scale-* transforms
    html = re.sub(r'\bhover:scale-\S+', '', html)
    html = re.sub(r'\bscale-\S+', '', html)
    # Also remove inline transform: scale(...) from style attrs
    html = re.sub(r'transform:\s*scale\([^)]*\);?', '', html)

    # 5. Replace the generic empty circle SVG that LLMs love to reuse
    generic_circle = r"d=['\"]M12 2C6\.5 2 2 6\.5 2 12s4\.5 10 10 10 10-4\.5 10-10S17\.5 2 12 2[^'\"]*['\"]"
    unique_icons = [
        "d='M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z'",
        "d='M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z'",
        "d='M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z'",
        "d='M13 10V3L4 14h7v7l9-11h-7z'",
        "d='M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z'",
        "d='M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253'",
        "d='M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'",
        "d='M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z'",
    ]
    icon_idx = [0]

    def _replace_icon(m):
        replacement = unique_icons[icon_idx[0] % len(unique_icons)]
        icon_idx[0] += 1
        return replacement

    html = re.sub(generic_circle, _replace_icon, html)

    # 6. Clean up stray double-spaces from class removals
    html = re.sub(r"  +", " ", html)

    return html


def generate_blog_content(user_requirement):
    system_instruction = (
        "You are a premium web designer. Create a visually stunning blog post as a COMPLETE standalone HTML page "
        "using Tailwind CSS CDN + Google Fonts. The design should look like a high-end editorial magazine.\n\n"

        "CRITICAL RULES (violating ANY = failure):\n"
        "1. Body MUST be: <body class='bg-white font-[Inter]'>. No bg-gray anything.\n"
        "2. NO <style> blocks. Tailwind utility classes ONLY.\n"
        "3. NO h-screen on ANY element. Sections sized by content + padding only.\n"
        "4. NO hover:scale-105 or transform scale. Use hover:shadow-xl instead.\n"
        "5. NO identical SVG icons. Every card icon must be a DIFFERENT recognizable shape.\n"
        "6. NO external images or JavaScript (except Tailwind CDN).\n\n"

        "HTML SKELETON (use exactly):\n"
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "  <meta charset='UTF-8'>\n"
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
        "  <script src='https://cdn.tailwindcss.com'></script>\n"
        "  <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@400;500;600;700;800;900&display=swap' rel='stylesheet'>\n"
        "</head>\n"
        "<body class='bg-white font-[Inter]'>\n"
        "</body></html>\n\n"

        "MANDATORY SECTIONS (include ALL in this order):\n\n"

        "1. HERO: <section class='bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900 py-24 md:py-32 px-6 text-center'>\n"
        "   Title: font-['Playfair_Display'] text-5xl md:text-7xl font-black text-white. Subtitle: text-indigo-200.\n\n"

        "2. INTRO: max-w-3xl mx-auto py-16 px-6. Heading text-3xl font-extrabold + 1-2 paragraphs text-slate-700 text-lg.\n\n"

        "3. CARD GRID (3+ cards): <div class='grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto'>.\n"
        "   Each card: bg-white rounded-2xl shadow-lg hover:shadow-xl transition-shadow p-6 border border-slate-100.\n"
        "   Each card MUST have a DIFFERENT SVG icon (lightbulb, star, shield, bolt, heart, book, chart, globe — NOT circles).\n"
        "   Use viewBox='0 0 24 24' stroke='currentColor' fill='none' stroke-width='2'.\n\n"

        "4. PULL QUOTE: bg-gradient-to-r from-indigo-50 to-purple-50 border-l-4 border-indigo-500 px-8 py-6 rounded-r-2xl max-w-3xl mx-auto.\n\n"

        "5. NUMBERED STEPS (3-5 items): Each with a w-10 h-10 rounded-full bg-indigo-600 text-white number badge + title + description.\n\n"

        "6. STAT ROW: flex flex-wrap justify-center gap-12 py-8. Each stat: text-4xl font-black text-indigo-600 number + text-sm label.\n\n"

        "7. DETAIL SECTION: Another text section or second card grid.\n\n"

        "8. CTA: <section class='max-w-5xl mx-auto bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900 rounded-3xl text-center py-16 px-8 mb-12'>\n"
        "   White heading + subtitle + <button class='px-8 py-4 bg-white text-indigo-700 font-bold rounded-full shadow-lg hover:shadow-xl transition-shadow'>.\n\n"

        "SPACING: Alternate section backgrounds bg-white / bg-slate-50. Each section: py-16 md:py-24 px-6.\n"
        "TEXT: Body text-slate-700 (never lighter). Headings text-slate-900.\n"
        "DIVIDERS: <div class='max-w-24 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full mx-auto my-4'></div> between sections.\n\n"

        "OUTPUT FORMAT:\n"
        "TITLE: [Creative title different from the hero H1]\n"
        "EXCERPT: [2-3 sentence SEO summary]\n"
        "CODE: [Complete HTML starting with <!DOCTYPE html>]\n\n"
        "Start with TITLE: immediately. No markdown code fences."
    )
    
    try:
        if not api_key:
            raise AIAgentError("Missing GROQ_API_KEY in environment. Get one free at https://console.groq.com")
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_requirement},
            ],
        )
        raw = response.choices[0].message.content or ""
        # Post-process: extract HTML then sanitize
        html_match = re.search(r'CODE:\s*(.+)', raw, re.DOTALL)
        if html_match:
            prefix = raw[:html_match.start()]
            cleaned_html = _sanitize_blog_html(html_match.group(1).strip())
            return prefix + "CODE: " + cleaned_html
        # Fallback: sanitize the whole thing if no CODE: marker
        return _sanitize_blog_html(raw)
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
        "You are an elite infographic designer. Create a Dribbble-quality data dashboard using HTML + Tailwind CSS CDN + inline SVG.\n\n"

        "CRITICAL RULES (violating ANY = failure):\n"
        "1. Body MUST be: <body class='bg-white font-[Inter]'>. No bg-gray.\n"
        "2. NO <style> blocks. Tailwind utility classes ONLY.\n"
        "3. NO h-screen. Sections sized by content only.\n"
        "4. NO hover:scale or transform scale. Use hover:shadow-xl.\n"
        "5. NO external images, chart.js, or JavaScript libraries.\n"
        "6. ALL data and charts MUST be about the USER'S TOPIC. Do NOT make up unrelated topics.\n"
        "7. Do NOT put HTML <div> elements inside <svg> tags. Legends go OUTSIDE the SVG.\n\n"

        "HTML SKELETON:\n"
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "  <meta charset='UTF-8'>\n"
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
        "  <script src='https://cdn.tailwindcss.com'></script>\n"
        "  <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap' rel='stylesheet'>\n"
        "</head>\n"
        "<body class='bg-white font-[Inter]'>\n"
        "</body></html>\n\n"

        "LAYOUT: max-w-6xl mx-auto px-6 md:px-12 py-12. Grid: grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6.\n\n"

        "MANDATORY PANELS (include ALL):\n\n"

        "1. TITLE BANNER (full-width): bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 md:p-12 col-span-full.\n"
        "   Title: text-3xl md:text-4xl font-extrabold text-white. Subtitle: text-indigo-200.\n\n"

        "2. STAT CARDS (3-4 in a row): text-4xl font-black bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent + text-sm label.\n\n"

        "3. BAR CHART: <svg viewBox='0 0 400 200'> with <rect> bars (different heights/colors), axis <line>, and <text> labels.\n\n"

        "4. DONUT CHART: <svg width='180' height='180' viewBox='0 0 180 180'> with stroke-dasharray circles. Legend OUTSIDE svg as HTML <span> elements.\n\n"

        "5. PROGRESS BARS: CSS-based. <div class='bg-slate-100 rounded-full h-3'><div class='bg-gradient-to-r from-indigo-500 to-purple-500 h-3 rounded-full' style='width: 85%'></div></div>.\n\n"

        "6. TABLE: <thead class='bg-slate-900 text-white'> with rounded corners. Rows: even:bg-slate-50. Best values: text-emerald-600 font-bold.\n\n"

        "CARD STYLE: bg-white rounded-2xl shadow-lg border border-slate-100 p-6. Title dot: <span class='w-3 h-3 rounded-full bg-indigo-600 inline-block mr-2'></span>.\n"
        "SVG RULES: Every <svg> needs width, height, viewBox. Use fill='#hex' for text. No Tailwind text-* inside SVG.\n"
        "COLORS: indigo-500/600, purple-500, emerald-500, amber-500, rose-500. Text: text-slate-900 headings, text-slate-600 body.\n\n"

        "OUTPUT FORMAT:\n"
        "TITLE: [Short title about the user's topic]\n"
        "CODE: [Complete HTML]\n\n"
        "Start with TITLE: immediately. No markdown fences."
    )

    try:
        if not api_key:
            raise AIAgentError("Missing GROQ_API_KEY in environment. Get one free at https://console.groq.com")
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": (
                        f"Create an infographic about: {user_requirement}\n\n"
                        "IMPORTANT: All chart data, stat numbers, labels, titles, and table content "
                        "must be specifically about the topic above. Do NOT use placeholder or unrelated data."
                    ),
                },
            ],
        )
        raw = response.choices[0].message.content or ""
        # Post-process: sanitize the HTML portion
        html_match = re.search(r'CODE:\s*(.+)', raw, re.DOTALL)
        if html_match:
            prefix = raw[:html_match.start()]
            cleaned_html = _sanitize_blog_html(html_match.group(1).strip())
            return prefix + "CODE: " + cleaned_html
        return _sanitize_blog_html(raw)
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


def enhance_blog_design(html_content, content_type="blog"):
    """Take full HTML content and return an enhanced version with improved visual design."""
    if content_type == "graphical":
        return enhance_graphical_design(html_content)

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


def enhance_section_design(html_section, instructions=None, content_type="blog"):
    """Take an HTML SECTION/FRAGMENT (not a full page) and return an enhanced version."""
    if content_type == "graphical":
        return enhance_graphical_section_design(html_section, instructions=instructions)

    system_instruction = (
        "You are a WORLD-CLASS web designer who transforms boring HTML into stunning, modern designs.\n\n"
        "You will receive an HTML FRAGMENT (a section, div, or component). "
        "Your job is to DRAMATICALLY ENHANCE its visual design. Make it look like a premium, "
        "professional website — not just small tweaks, but a REAL visual upgrade.\n\n"
        "MANDATORY ENHANCEMENTS (apply ALL that are relevant):\n"
        "1. LAYOUT: Restructure with CSS Grid or Flexbox for better alignment. Add proper gaps.\n"
        "2. SPACING: Generous padding (p-8, p-12), proper margins, breathing room between elements.\n"
        "3. COLORS: Replace plain colors with gradients (bg-gradient-to-r, from-X-500 to-Y-600). "
        "Use modern color combos like indigo→purple, blue→cyan, emerald→teal.\n"
        "4. CARDS: Wrap items in card-like containers with bg-white, rounded-2xl, shadow-lg, p-6.\n"
        "5. TYPOGRAPHY: Use text-4xl/5xl for headings with font-extrabold. "
        "Use text-lg for body with text-gray-600 and leading-relaxed.\n"
        "6. BORDERS & SHADOWS: Add shadow-xl, ring-1 ring-gray-100, rounded-2xl or rounded-3xl.\n"
        "7. HOVER EFFECTS: Add hover:shadow-2xl, hover:scale-105, hover:-translate-y-1 with transition-all duration-300.\n"
        "8. ICONS/BADGES: Add decorative elements like colored number badges, gradient accent bars, "
        "small colored dots, or icon containers with rounded backgrounds.\n"
        "9. BACKGROUNDS: Add subtle gradient backgrounds (bg-gradient-to-br from-gray-50 to-white) "
        "or light pattern overlays.\n"
        "10. DIVIDERS: Replace plain hrs with gradient lines or decorative separators.\n\n"
        "COMMENT REQUIREMENT — THIS IS MANDATORY:\n"
        "Add HTML comments (<!-- ... -->) ABOVE each changed element explaining WHAT you changed and WHY.\n"
        "Format: <!-- ENHANCED: [what was changed] → [what it is now] | WHY: [reason] -->\n"
        "Examples:\n"
        "  <!-- ENHANCED: plain div → card with shadow + rounded corners | WHY: creates depth and visual separation -->\n"
        "  <!-- ENHANCED: text-xl → text-4xl font-extrabold gradient text | WHY: stronger visual hierarchy -->\n"
        "  <!-- ENHANCED: added hover:scale-105 transition | WHY: interactive feedback for users -->\n\n"
        "CRITICAL RULES:\n"
        "- Keep ALL text content EXACTLY the same — only change CSS classes, styles, and wrapper structure.\n"
        "- The design MUST look noticeably different and better than the input.\n"
        "- Return ONLY the enhanced HTML fragment. NOT a full page.\n"
        "- Do NOT add <!DOCTYPE html>, <html>, <head>, <body> tags.\n"
        "- Do NOT add <script> or <link> tags.\n"
        "- Do NOT wrap in markdown code fences.\n"
        "- Use Tailwind CSS classes only.\n"
        "- The output must be the enhanced fragment with comments, nothing else."
    )

    try:
        if not api_key:
            raise AIAgentError("Missing GROQ_API_KEY in environment.")
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": (
                    f"ENHANCE THIS HTML SECTION — make it look dramatically better:\n\n{html_section}"
                    + (f"\n\nUSER INSTRUCTIONS (follow these closely):\n{instructions}" if instructions else "")
                )},
            ],
        )
        result = response.choices[0].message.content or ""
        result = result.replace("```html", "").replace("```", "").strip()
        # Strip any accidental full-page wrapper the AI may have added
        result = re.sub(r'<!DOCTYPE[^>]*>', '', result, flags=re.IGNORECASE).strip()
        result = re.sub(r'</?html[^>]*>', '', result, flags=re.IGNORECASE).strip()
        result = re.sub(r'<head[\s\S]*?</head>', '', result, flags=re.IGNORECASE).strip()
        result = re.sub(r'</?body[^>]*>', '', result, flags=re.IGNORECASE).strip()
        return result
    except Exception as exc:
        if _is_rate_limit_error(exc):
            retry_after = _extract_retry_after_seconds(str(exc))
            if retry_after is not None:
                raise AIAgentRateLimitError(f"{exc}||retry_after={retry_after}")
            raise AIAgentRateLimitError(str(exc))
        raise AIAgentError(str(exc))


def enhance_graphical_design(html_content):
    """Take full HTML graphical/infographic content and return an enhanced version."""
    system_instruction = (
        "You are a WORLD-CLASS data visualization and infographic designer.\n"
        "You will receive a complete HTML page containing charts, graphs, tables, stat cards, "
        "progress bars, and other data visualization elements.\n\n"
        "Your job is to DRAMATICALLY ENHANCE its visual design to look like a premium analytics dashboard.\n\n"
        "WHAT TO IMPROVE:\n"
        "1. CHART COLORS: Replace plain fills with rich gradients. Use vibrant color palettes: "
        "indigo→purple, blue→cyan, emerald→teal, amber→orange, rose→pink. "
        "Apply gradients via SVG <linearGradient> or <radialGradient> defs.\n"
        "2. SVG STYLING: Add drop-shadow filters, rounded stroke-linecap='round', smooth transitions. "
        "Make bars/slices more visually distinct with better spacing.\n"
        "3. CARD CONTAINERS: Wrap each chart/panel in premium cards with bg-white rounded-2xl shadow-xl "
        "border border-slate-100 p-6. Add subtle hover:shadow-2xl transition-all duration-300.\n"
        "4. STAT CARDS: Make numbers text-4xl font-black with gradient text (bg-gradient-to-r bg-clip-text text-transparent). "
        "Add colored accent bars or dots. Use from-indigo-600 to-purple-600 style combos.\n"
        "5. TABLE STYLING: Header bg-gradient-to-r from-slate-800 to-slate-900 text-white rounded-t-xl. "
        "Alternating rows even:bg-slate-50. Best values: text-emerald-600 font-semibold. Hover: hover:bg-indigo-50.\n"
        "6. PROGRESS BARS: Make taller (h-3 or h-4), use gradient fills from-indigo-500 to-purple-500, "
        "add rounded-full, animate with transition-all. Add percentage labels.\n"
        "7. DONUT/PIE CHARTS: Increase stroke width, add drop-shadow, use vibrant gradients per segment.\n"
        "8. LAYOUT: Use grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 for cards. "
        "Ensure proper max-w-6xl mx-auto px-6 py-12 for the page container.\n"
        "9. TITLE BANNER: Make the header section a stunning gradient banner with "
        "bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-8 col-span-full. "
        "Title: text-4xl font-extrabold text-white.\n"
        "10. BACKGROUNDS: Section bg should alternate between bg-white and bg-slate-50. "
        "Add bg-gradient-to-br from-slate-50 to-white for subtle depth.\n"
        "11. LEGENDS: Style legend items with small colored circles (w-3 h-3 rounded-full), "
        "proper spacing gap-4, font-medium text-slate-600.\n"
        "12. DIVIDERS: Add gradient dividers between sections: "
        "h-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full max-w-24 mx-auto.\n\n"
        "SVG-SPECIFIC RULES (CRITICAL):\n"
        "- NEVER change SVG path d='...' data, viewBox values, or data point coordinates.\n"
        "- NEVER change text content, number values, or labels.\n"
        "- You CAN change: fill colors, stroke colors, opacity, filters, gradients, stroke-width.\n"
        "- You CAN add: <defs> with <linearGradient>, <filter> for shadows, <animate> for subtle effects.\n"
        "- You CAN change: Tailwind classes on wrapper divs around SVGs.\n\n"
        "OUTPUT RULES:\n"
        "- Keep ALL text content, numbers, and data EXACTLY the same.\n"
        "- Keep the Tailwind CDN script tag and Google Fonts link.\n"
        "- Return ONLY the complete enhanced HTML starting with <!DOCTYPE html>.\n"
        "- Do NOT wrap in markdown code fences.\n"
        "- Do NOT add external images or JavaScript libraries.\n"
        "- The result MUST look noticeably more polished and premium than the input."
    )

    try:
        if not api_key:
            raise AIAgentError("Missing GROQ_API_KEY in environment.")
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.6,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"ENHANCE this infographic/dashboard HTML to look stunning and premium:\n\n{html_content}"},
            ],
        )
        result = response.choices[0].message.content or ""
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


def enhance_graphical_section_design(html_section, instructions=None):
    """Take a graphical/infographic HTML FRAGMENT and return an enhanced version."""
    system_instruction = (
        "You are a WORLD-CLASS data visualization and infographic designer.\n\n"
        "You will receive an HTML FRAGMENT from an infographic or dashboard — it could be a chart, "
        "a stat card, a table, a progress bar section, or a visualization panel.\n\n"
        "Your job is to DRAMATICALLY ENHANCE its visual design. Make it look like a premium "
        "analytics dashboard — not small tweaks, but a REAL visual upgrade.\n\n"
        "MANDATORY ENHANCEMENTS (apply ALL that are relevant):\n"
        "1. CHART COLORS: Replace flat fills with rich SVG gradients (<linearGradient>). "
        "Use indigo→purple, blue→cyan, emerald→teal, amber→orange, rose→pink.\n"
        "2. SVG STYLING: Add drop-shadow filters via <filter>, use stroke-linecap='round', "
        "increase stroke-width for visibility. Add spacing between chart elements.\n"
        "3. CARD WRAPPERS: Wrap in bg-white rounded-2xl shadow-xl border border-slate-100/50 p-6. "
        "Add hover:shadow-2xl transition-all duration-300.\n"
        "4. STAT NUMBERS: text-4xl font-black bg-gradient-to-r from-indigo-600 to-purple-600 "
        "bg-clip-text text-transparent. Add colored accent dots or bars.\n"
        "5. TABLE ENHANCEMENTS: Gradient header, alternating row colors, hover:bg-indigo-50, "
        "rounded corners on container, ring-1 ring-slate-100.\n"
        "6. PROGRESS BARS: Taller (h-3/h-4), gradient fills, rounded-full, transition-all. "
        "Add labels with font-semibold.\n"
        "7. BACKGROUNDS: Add bg-gradient-to-br from-slate-50 to-white or subtle colored tints.\n"
        "8. TYPOGRAPHY: Headings text-2xl font-bold text-slate-900. Labels text-sm text-slate-500 font-medium.\n"
        "9. LEGENDS: Colored dots (w-3 h-3 rounded-full bg-COLOR-500) with gap-3 flex items.\n"
        "10. SPACING: Generous p-6 to p-8, gap-4 to gap-6 between items.\n\n"
        "SVG-SPECIFIC RULES (CRITICAL):\n"
        "- NEVER change SVG path d='...' data, viewBox values, or coordinate numbers.\n"
        "- NEVER change text content, labels, or numeric data.\n"
        "- You CAN add/change: fill, stroke, opacity, <defs> with gradients/filters, stroke-width.\n"
        "- You CAN change: Tailwind classes on wrapper elements around SVGs.\n\n"
        "COMMENT REQUIREMENT — MANDATORY:\n"
        "Add <!-- ENHANCED: [what] → [new] | WHY: [reason] --> comments above each change.\n\n"
        "OUTPUT RULES:\n"
        "- Keep ALL text, numbers, and data EXACTLY the same.\n"
        "- Return ONLY the enhanced HTML fragment. NOT a full page.\n"
        "- Do NOT add <!DOCTYPE html>, <html>, <head>, <body>, <script>, or <link> tags.\n"
        "- Do NOT wrap in markdown code fences.\n"
        "- Use Tailwind CSS classes. The design MUST look noticeably better."
    )

    try:
        if not api_key:
            raise AIAgentError("Missing GROQ_API_KEY in environment.")
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": (
                    f"ENHANCE this infographic/dashboard section — make it look stunning:\n\n{html_section}"
                    + (f"\n\nUSER INSTRUCTIONS (follow these closely):\n{instructions}" if instructions else "")
                )},
            ],
        )
        result = response.choices[0].message.content or ""
        result = result.replace("```html", "").replace("```", "").strip()
        result = re.sub(r'<!DOCTYPE[^>]*>', '', result, flags=re.IGNORECASE).strip()
        result = re.sub(r'</?html[^>]*>', '', result, flags=re.IGNORECASE).strip()
        result = re.sub(r'<head[\s\S]*?</head>', '', result, flags=re.IGNORECASE).strip()
        result = re.sub(r'</?body[^>]*>', '', result, flags=re.IGNORECASE).strip()
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