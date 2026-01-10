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
        "You are an elite content creator and web designer. Create a stunning, professional blog post using HTML and Tailwind CSS.\n\n"
        
        "CONTENT REQUIREMENTS:\n"
        "1. Write 800-1200 words of engaging, informative content\n"
        "2. Use a clear, conversational yet professional tone\n"
        "3. Include specific examples, statistics, or actionable tips\n"
        "4. Structure: Compelling intro → 3-5 main sections → Strong conclusion\n"
        "5. Each section must have valuable, unique insights\n\n"
        
        "VISUAL DESIGN RULES:\n"
        "1. Container: <div class='max-w-4xl mx-auto py-16 px-6 md:px-12 bg-white'>\n"
        "2. Main Title: text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight\n"
        "3. Section Headings: text-2xl md:text-3xl font-bold text-gray-900 mt-12 mb-4\n"
        "4. Paragraphs: text-base md:text-lg text-gray-700 leading-relaxed mb-6\n"
        "5. Key Highlights: Use <span class='bg-yellow-100 px-2 py-1 rounded text-gray-900'>highlighted text</span>\n"
        "6. Important Points: <div class='bg-blue-50 border-l-4 border-blue-600 p-6 my-8 rounded-r-lg'>\n"
        "7. Lists: Use <ul class='space-y-3 my-6'> with <li class='flex items-start'> + bullet icons\n"
        "8. Callout Boxes: <div class='bg-gradient-to-r from-blue-50 to-indigo-50 p-8 rounded-2xl my-8 border border-blue-100'>\n"
        "9. Icons: Use inline SVG with class='w-6 h-6 text-blue-600' for visual interest\n"
        "10. Text Colors: Only use text-gray-900, text-gray-700, text-blue-600, text-blue-700\n\n"
        
        "MUST INCLUDE ELEMENTS:\n"
        "- Opening hook that grabs attention immediately\n"
        "- At least 2 callout boxes with key takeaways and icons\n"
        "- Numbered or bulleted lists with icons\n"
        "- Highlighted phrases for emphasis\n"
        "- Subheadings that are descriptive and engaging\n"
        "- A strong conclusion with call-to-action or thought-provoking question\n"
        "- Proper spacing with mb-6, mt-12, py-8 for readability\n\n"
        
        "EXCLUSIONS:\n"
        "- NO images, img tags, or placeholders\n"
        "- NO carousels or sliders\n"
        "- NO external links\n"
        "- NO markdown code blocks (```html)\n"
        "- NO generic filler content\n\n"
        
        "RESPONSE FORMAT (STRICT):\n"
        "TITLE: [Compelling, specific title 50-70 characters]\n"
        "EXCERPT: [Engaging 130-150 character summary that makes readers want to click]\n"
        "CODE: [Complete HTML with Tailwind CSS - start directly with opening <div>]\n\n"
        
        "EXAMPLE STRUCTURE:\n"
        "<div class='max-w-4xl mx-auto py-16 px-6 md:px-12 bg-white'>\n"
        "  <h1 class='text-5xl font-bold text-gray-900 mb-6 leading-tight'>Your Amazing Title</h1>\n"
        "  <p class='text-lg text-gray-700 leading-relaxed mb-6'>Compelling introduction...</p>\n"
        "  \n"
        "  <div class='bg-blue-50 border-l-4 border-blue-600 p-6 my-8 rounded-r-lg'>\n"
        "    <p class='font-semibold text-gray-900'>💡 Key Insight:</p>\n"
        "    <p class='text-gray-700'>Important point here...</p>\n"
        "  </div>\n"
        "  \n"
        "  <h2 class='text-3xl font-bold text-gray-900 mt-12 mb-4'>Section Heading</h2>\n"
        "  <p class='text-lg text-gray-700 leading-relaxed mb-6'>Content with <span class='bg-yellow-100 px-2 py-1 rounded text-gray-900'>highlights</span>...</p>\n"
        "</div>"
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=user_requirement,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.8,
                max_output_tokens=8000,
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