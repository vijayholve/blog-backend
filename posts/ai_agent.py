# posts/ai_agent.py
import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from .prompts import (
    BLOG_SYSTEM_INSTRUCTION,
    GRAPHICAL_SYSTEM_INSTRUCTION,
    ENHANCE_BLOG_SYSTEM_INSTRUCTION,
    ENHANCE_SECTION_SYSTEM_INSTRUCTION,
    ENHANCE_GRAPHICAL_SYSTEM_INSTRUCTION,
    ENHANCE_GRAPHICAL_SECTION_SYSTEM_INSTRUCTION,
    REFINE_COMMANDS,
)

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
    system_instruction = BLOG_SYSTEM_INSTRUCTION
    
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
    system_instruction = GRAPHICAL_SYSTEM_INSTRUCTION

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


# REFINE_COMMANDS imported from prompts.py


def enhance_blog_design(html_content, content_type="blog"):
    """Take full HTML content and return an enhanced version with improved visual design."""
    if content_type == "graphical":
        return enhance_graphical_design(html_content)

    system_instruction = ENHANCE_BLOG_SYSTEM_INSTRUCTION

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

    system_instruction = ENHANCE_SECTION_SYSTEM_INSTRUCTION

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
    system_instruction = ENHANCE_GRAPHICAL_SYSTEM_INSTRUCTION

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
    system_instruction = ENHANCE_GRAPHICAL_SECTION_SYSTEM_INSTRUCTION

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