# posts/models.py
from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

class Post(models.Model):
    title = models.CharField(max_length=200)
    # db_index=True makes searching by slug much faster
    slug = models.SlugField(unique=True, db_index=True, blank=True)
    content = CKEditor5Field('Text', config_name='default')    
    excerpt = models.CharField(max_length=500, help_text="Short summary for SEO description")
    cover_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Automatically generate slug from title if it doesn't exist
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title