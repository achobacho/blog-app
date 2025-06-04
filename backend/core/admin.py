from django.contrib import admin
from tinymce.widgets import TinyMCE
from django.db import models
from .models import User, Category, Tag, Blog, Menu, Comment
from core.thread_locals import set_admin_request_flag
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


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

    def save_model(self, request, obj, form, change):
        print("ADMIN edit TRIGGERED")
        obj._from_admin = True
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        print("ADMIN DELETE TRIGGERED")
        obj._from_admin = True
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        print("DELETE QUERYSET (bulk)")
        set_admin_request_flag(True)
        for obj in queryset:
            obj._from_admin = True
            obj.delete()

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        set_admin_request_flag(True)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        set_admin_request_flag(True)
        super().delete_model(request, obj)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        set_admin_request_flag(True)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        set_admin_request_flag(True)
        super().delete_model(request, obj)

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        set_admin_request_flag(True)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        set_admin_request_flag(True)
        super().delete_model(request, obj)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        set_admin_request_flag(True)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        set_admin_request_flag(True)
        super().delete_model(request, obj)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("profile_image",)}),
    )

    def save_model(self, request, obj, form, change):
        set_admin_request_flag(True)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        set_admin_request_flag(True)
        super().delete_model(request, obj)

