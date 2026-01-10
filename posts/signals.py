from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Author


@receiver(post_save, sender=User)
def create_author_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create an Author profile when a User is created
    """
    if created:
        Author.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_author_profile(sender, instance, **kwargs):
    """
    Signal to save the Author profile when the User is saved
    """
    if hasattr(instance, 'author_profile'):
        instance.author_profile.save()
