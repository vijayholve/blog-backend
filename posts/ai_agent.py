# posts/ai_agent.py
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))



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
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=user_requirement,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )
        )
        return response.text if response.text else ""
    except Exception as e:
        print(f"AI Error: {e}")
        raise e
if __name__ == "__main__":
    import sys
    test_requirement = sys.argv[1] if len(sys.argv) > 1 else "Create a space exploration blog"
    result = generate_blog_content(test_requirement)
    if result:
        print("\n--- GENERATED CODE ---\n")
        print(result)