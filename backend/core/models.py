from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
