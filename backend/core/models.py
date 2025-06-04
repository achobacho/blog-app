# backend/core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# --- Custom User ---
class User(AbstractUser):
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

# --- Category ---
class Category(models.Model):
    title = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.title

# --- Tag ---
class Tag(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

# --- Blog ---
class Blog(models.Model):
    title = models.CharField(max_length=255)
    main_image = models.ImageField(upload_to='blog_images/')
    description = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

# --- Menu ---
class Menu(models.Model):
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

# --- Comment ---
class Comment(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    like = models.PositiveIntegerField(default=0)
    dislike = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Comment by {self.author} on {self.blog}"
