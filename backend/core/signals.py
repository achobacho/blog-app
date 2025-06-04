from django.db.models.signals import post_save, post_delete
from core.models import Blog, Category, Tag, Menu, Comment, User
from pymongo import MongoClient
from django.conf import settings
from core.thread_locals import get_admin_request_flag
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.db.models.signals import post_migrate
from django.dispatch import receiver

# Setup Mongo connection
mongo_client = MongoClient(settings.MONGO_URL)
mongo_db = mongo_client[settings.MONGO_DB_NAME]
mongo_collection = mongo_db["blogs"]


@receiver(post_migrate)
def create_api_docs_permission(sender, **kwargs):
    User = apps.get_model('core', 'User')
    content_type = ContentType.objects.get_for_model(User)

    Permission.objects.get_or_create(
        codename='view_api_docs',
        name='Can view API documentation',
        content_type=content_type,
    )


def serialize_blog(blog):
    return {
        "id": blog.id,
        "title": blog.title,
        "description": blog.description,
        "category": blog.category.title if blog.category else None,
        "tags": [tag.title for tag in blog.tags.all()],
        "author": blog.author.username,
        "is_active": blog.is_active,
    }

@receiver(post_save, sender=Blog)
def sync_blog_to_mongo(sender, instance, **kwargs):
    print('POST edit SIGNAL:')
    # Only sync from Django admin
    if hasattr(instance, "_from_admin") and instance._from_admin:
        mongo_collection.update_one(
            {"id": instance.id},
            {"$set": serialize_blog(instance)},
            upsert=True
        )

@receiver(post_delete, sender=Blog)
def delete_blog_from_mongo(sender, instance, **kwargs):
    print(f"POST DELETE SIGNAL: blog {instance.id}, from_admin={get_admin_request_flag()}")
    if get_admin_request_flag():
        mongo_collection.delete_one({"id": instance.id})


@receiver(post_save, sender=Category)
def sync_category_to_mongo(sender, instance, **kwargs):
    if get_admin_request_flag():
        mongo_db["categories"].update_one(
            {"id": instance.id},
            {"$set": {
                "id": instance.id,
                "title": instance.title,
                "parent_id": instance.parent.id if instance.parent else None
            }},
            upsert=True
        )

@receiver(post_delete, sender=Category)
def delete_category_from_mongo(sender, instance, **kwargs):
    if get_admin_request_flag():
        mongo_db["categories"].delete_one({"id": instance.id})


@receiver(post_save, sender=Tag)
def sync_tag_to_mongo(sender, instance, **kwargs):
    if get_admin_request_flag():
        mongo_db["tags"].update_one(
            {"id": instance.id},
            {"$set": {
                "id": instance.id,
                "title": instance.title
            }},
            upsert=True
        )

@receiver(post_delete, sender=Tag)
def delete_tag_from_mongo(sender, instance, **kwargs):
    if get_admin_request_flag():
        mongo_db["tags"].delete_one({"id": instance.id})


@receiver(post_save, sender=Menu)
def sync_menu_to_mongo(sender, instance, **kwargs):
    if get_admin_request_flag():
        mongo_db["menus"].update_one(
            {"id": instance.id},
            {"$set": {
                "id": instance.id,
                "title": instance.title,
                "order": instance.order,
                "category_id": instance.category.id if instance.category else None,
                "url": instance.url
            }},
            upsert=True
        )

@receiver(post_delete, sender=Menu)
def delete_menu_from_mongo(sender, instance, **kwargs):
    if get_admin_request_flag():
        mongo_db["menus"].delete_one({"id": instance.id})


@receiver(post_save, sender=Comment)
def sync_comment_to_mongo(sender, instance, **kwargs):
    if get_admin_request_flag():
        mongo_db["comments"].update_one(
            {"id": instance.id},
            {"$set": {
                "id": instance.id,
                "blog_id": instance.blog.id,
                "author_id": instance.author.id,
                "content": instance.content,
                "parent_id": instance.parent.id if instance.parent else None,
                "like": instance.like,
                "dislike": instance.dislike
            }},
            upsert=True
        )

@receiver(post_delete, sender=Comment)
def delete_comment_from_mongo(sender, instance, **kwargs):
    if get_admin_request_flag():
        mongo_db["comments"].delete_one({"id": instance.id})

@receiver(post_save, sender=User)
def sync_user_to_mongo(sender, instance, **kwargs):
    if get_admin_request_flag():
        mongo_db["users"].update_one(
            {"id": instance.id},
            {"$set": {
                "id": instance.id,
                "username": instance.username,
                "email": instance.email,
                "is_staff": instance.is_staff,
                "is_active": instance.is_active,
                "profile_image": instance.profile_image.url if instance.profile_image else None,
            }},
            upsert=True
        )

@receiver(post_delete, sender=User)
def delete_user_from_mongo(sender, instance, **kwargs):
    if get_admin_request_flag():
        mongo_db["users"].delete_one({"id": instance.id})
