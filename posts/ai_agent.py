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
        "You are a world-class editorial web designer. Generate a blog post using HTML and Tailwind CSS. "
        "STRICT VISUAL REQUIREMENTS:\n"
        "1. Layout: Use a white background (bg-white). Ensure generous white space using 'py-20 px-6 md:px-20'.\n"
        "2. Typography: All text must be high contrast. Allowed text colors: dark (text-slate-950), blue (text-blue-800), yellow (text-yellow-800), red (text-red-800).\n"
        "3. Hierarchy: Use massive, bold headings (text-5xl to text-7xl) for titles. Highlight important words using 'bg-yellow-100 px-1 rounded' or 'text-blue-700 font-black'.\n"
        "4. Professionalism: Use modern 'rounded-3xl' or 'rounded-[3rem]' for containers. Add subtle 'border border-slate-100' for sections.\n"
        "5. Responsive Design: Use Tailwind prefixing (e.g., 'text-3xl md:text-6xl') to ensure the blog looks perfect on both mobile and desktop.\n"
        "6. Content Structure: Include an intro, key takeaway boxes with 'Lucide-style' SVGs (hardcoded), and a summary.\n"
        "7. Images: Use royalty-free images from Unsplash URLs only if they are relevant. Otherwise use colored placeholders.\n"
        "8. EXCLUSIONS: Output ONLY the raw HTML code inside the CODE section. Do NOT use markdown code blocks (```html).\n\n"
        "9. dont use a image slider or carousel and dont give image as well in code \n\n"
        "RESPONSE FORMAT - YOU MUST FOLLOW THIS EXACTLY:\n"
        "Text color must be dark so it can visible back of bg color white color "
        "TITLE: [Catchy Title]\n"
        "EXCERPT: [Short SEO Summary]\n"
        "CODE: [Full HTML/Tailwind content]"
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