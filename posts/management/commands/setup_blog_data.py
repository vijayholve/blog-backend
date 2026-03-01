from django.core.management.base import BaseCommand
from posts.models import Category, Tag

class Command(BaseCommand):
    help = 'Populates the database with initial Categories and Tags'

    def handle(self, *args, **kwargs):
        # Data Structure: { Category_Name: [List_of_Tags] }
        blog_data = {
            "Programming & Tech": [
                "Python", "Django", "React", "Next.js", "Tailwind CSS", 
                "API Development", "Database Management", "Frontend", "Backend", "JavaScript"
            ],
            "Artificial Intelligence": [
                "Generative AI", "Gemini AI", "Machine Learning", "LLMs", "AI Agents", 
                "Natural Language Processing", "Prompt Engineering", "Automation", "Future of Tech", "AI Tools"
            ],
            "Design & UI/UX": [
                "Swiss Design", "Digital Minimalism", "Typography", "User Experience", "Responsive Design", 
                "Modern UI", "Web Aesthetics", "Layout Design", "Tailwind Patterns", "Visual Hierarchy"
            ],
            "Software Engineering": [
                "System Architecture", "Agile Methodology", "Code Review", "Open Source", "DevOps", 
                "Testing", "Scalability", "Clean Code", "Version Control", "Security"
            ],
            "Digital Marketing & SEO": [
                "Content Strategy", "SEO Tips", "Blogging Tips", "Growth Hacking", "Social Media", 
                "Engagement", "Keywords", "Newsletter", "Monetization", "Analytics"
            ]
        }

        for cat_name, tags in blog_data.items():
            # Create or get the Category
            category, cat_created = Category.objects.get_or_create(name=cat_name)
            if cat_created:
                self.stdout.write(self.style.SUCCESS(f'Created Category: "{cat_name}"'))
            else:
                self.stdout.write(f'Category already exists: "{cat_name}"')

            for tag_name in tags:
                # Create or get the Tag, and ensure it's linked to this category
                tag, tag_created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'category': category}
                )
                if tag_created:
                    self.stdout.write(self.style.SUCCESS(f'  - Created Tag: "{tag_name}"'))
                else:
                    # Update category if it was missing or different
                    if tag.category != category:
                        tag.category = category
                        tag.save()
                        self.stdout.write(f'  - Updated Tag: "{tag_name}" -> {cat_name}')
                    else:
                        self.stdout.write(f'  - Tag already exists: "{tag_name}"')

        self.stdout.write(self.style.SUCCESS('Successfully populated blog data!'))