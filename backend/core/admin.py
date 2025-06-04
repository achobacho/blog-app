from django.contrib import admin
from tinymce.widgets import TinyMCE
from django.db import models
from .models import User, Category, Tag, Blog, Menu, Comment


admin.site.register(Blog)
admin.site.register(User)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Menu)
admin.site.register(Comment)
