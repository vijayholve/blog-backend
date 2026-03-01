from posts.models import Category, Tag
from django.utils.text import slugify

# Define a mapping of Categories to relevant Sub-Tags
tag_data = {
    'Technology': ['Python', 'Django', 'React', 'AI', 'Cybersecurity', 'Web Development'],
    'Business': ['Startup', 'Marketing', 'Investing', 'Freelancing', 'Finance'],
    'Lifestyle': ['Productivity', 'Minimalism', 'Mental Health', 'Personal Growth'],
    'Travel': ['Backpacking', 'Solo Travel', 'Pune Diary', 'Budget Travel'],
    'Food': ['Recipes', 'Street Food', 'Vegan', 'Healthy Eating'],
    'Health': ['Fitness', 'Yoga', 'Nutrition', 'Workout']
}

for cat_name, tags in tag_data.items():
    # Find the category object (case-insensitive)
    category = Category.objects.filter(name__iexact=cat_name).first()
    
    if category:
        for tag_name in tags:
            # get_or_create ensures uniqueness and prevents IntegrityErrors
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                category=category,
                defaults={'slug': slugify(tag_name)}
            )
            if created:
                print(f"Created Tag: {tag_name} under {cat_name}")
            else:
                print(f"Tag: {tag_name} already exists.")

print("\n--- All tags created successfully ---")