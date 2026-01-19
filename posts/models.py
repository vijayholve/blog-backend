from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone

class Author(models.Model):
    """
    Extends the default User model to include specific author details.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='author_profile'
    )
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='authors/', blank=True, null=True)
    website = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=200)
    # db_index=True is critical for production searching performance
    slug = models.SlugField(max_length=200, unique=True, db_index=True, blank=True)
    
    # Author Integration: Links the post to the Author model
    author = models.ForeignKey(
        Author, 
        on_delete=models.CASCADE, 
        null=True,
        related_name='posts'
    )
    
    # Categorization
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='posts'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')

    # Content
    content = models.TextField() 
    excerpt = models.CharField(
        max_length=500, 
        help_text="Short summary for SEO description"
    )
    is_html = models.BooleanField(
        default=False, 
        help_text="Check if the content is in HTML format"
    )
    
    # Media: Organized by date for production scalability
    cover_image = models.ImageField(
        upload_to='blog_images/%Y/%m/%d/', 
        blank=True, 
        null=True
    )

    # Status & Timeline
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Metrics
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def save(self, *args, **kwargs):
        # Automatically generate slug from title if it doesn't exist
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-set published date when moving from draft to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title