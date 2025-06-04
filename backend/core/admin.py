from django.contrib import admin
from tinymce.widgets import TinyMCE
from django.db import models
from .models import User, Category, Tag, Blog, Menu, Comment

class CustomTinyMCE(TinyMCE):
    def use_required_attribute(self, *args):
        return False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mce_attrs = {
            'plugins': 'image media link code',
            'toolbar': 'undo redo | styleselect | bold italic | alignleft aligncenter alignright | image media link code',
            'automatic_uploads': True,
            'images_upload_url': '/upload-image/',
            'file_picker_types': 'image',
        }

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': CustomTinyMCE()},
    }

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Menu)
admin.site.register(Comment)
