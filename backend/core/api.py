import base64
from django.core.files.base import ContentFile
from ninja import NinjaAPI
from ninja.security import HttpBearer
from django.http import HttpRequest
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import check_password
from core.models import User, Comment, Blog, Tag, Category, Menu
from ninja import Router
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from core.schemas import (BlogIn, BlogOut, ErrorSchema, CommentIn, CommentOut, CommentEdit, CategoryOut, TagOut,
                          MenuOut, ProfileUpdateSchema, RegisterSchema, ChangePasswordSchema, ForgotPasswordSchema, ResetPasswordSchema)
from rest_framework_simplejwt.authentication import JWTAuthentication
from typing import List, Optional, Dict
from django.db.models import Q
from ninja.pagination import paginate, PageNumberPagination
from django.contrib.auth import get_user_model

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        validated_user = JWTAuthentication().authenticate(request)
        if validated_user:
            request.user, _ = validated_user
            return request.user


class AdminOnlyAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str):
        validated_user = JWTAuthentication().authenticate(request)
        if not validated_user:
            return None
        user = validated_user[0]

        if user.has_perm("core.view_api_docs"):
            request.user = user
            return user

        return None

api = NinjaAPI(
    title="Blog API",
    version="1.0.0",
    docs_url="/docs",
    csrf=False,
)

# Optional test route
@api.get("/ping")
def ping(request):
    return {"message": "pong"}

auth_router = Router()
blog_router = Router()
comment_router = Router()

@auth_router.post("/login")
def login(request, username: str, password: str):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return {"error": "Invalid credentials"}

    if not user.is_active:
        return {"error": "Account is not activated. Please check your email."}

    user = authenticate(username=username, password=password)
    if not user:
        return {"error": "Invalid credentials"}

    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

@auth_router.post("/register")
def register(request, data: RegisterSchema):
    if User.objects.filter(username=data.username).exists():
        return {"error": "Username already exists"}

    user = User.objects.create_user(
        username=data.username,
        password=data.password,
        email=data.email,
        is_active=False
    )

    if data.profile_image:
        try:
            format, imgstr = data.profile_image.split(";base64,")
            ext = format.split("/")[-1]
            user.profile_image.save(
                f"profile.{ext}",
                ContentFile(base64.b64decode(imgstr)),
                save=False
            )
        except Exception:
            return {"error": "Invalid image format"}

    user.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_link = f"http://localhost:8000/api/auth/activate/{uid}/{token}"

    send_mail(
        subject="Activate your account",
        message=f"Click to activate: {activation_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

    return {"success": "Check your email to activate your account."}


@auth_router.get("/activate/{uidb64}/{token}")
def activate_user(request, uidb64: str, token: str):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return {"error": "Invalid activation link"}

    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return {"message": "Account activated successfully."}
    else:
        return {"error": "Activation link is invalid or expired."}


@auth_router.put("/profile", auth=JWTAuth())
def update_profile(request, data: ProfileUpdateSchema):
    user = request.auth

    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.email is not None:
        user.email = data.email

    if data.profile_image:
        # Accept base64 string and save as image
        format, imgstr = data.profile_image.split(";base64,")
        ext = format.split("/")[-1]
        user.profile_image.save(f"profile.{ext}", ContentFile(base64.b64decode(imgstr)), save=False)

    user.save()
    return {"success": True}


@auth_router.put("/change-password", auth=JWTAuth())
def change_password(request, data: ChangePasswordSchema):
    user = request.auth

    if not check_password(data.old_password, user.password):
        return {"error": "Old password is incorrect"}

    user.set_password(data.new_password)
    user.save()
    return {"success": True}


User = get_user_model()


@auth_router.post("/forgot-password")
def forgot_password(request, data: ForgotPasswordSchema):
    try:
        user = User.objects.get(email=data.email)
    except User.DoesNotExist:
        return {"error": "User with this email does not exist"}

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_link = f"http://localhost:8000/api/auth/reset-password-confirm/{uid}/{token}"

    send_mail(
        subject="Reset your password",
        message=f"Click the link to reset your password: {reset_link}",
        from_email=None,
        recipient_list=[user.email],
    )

    return {"success": "Password reset link sent to your email"}


@auth_router.post("/reset-password-confirm/{uidb64}/{token}")
def reset_password_confirm(request, uidb64: str, token: str, data: ResetPasswordSchema):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        return {"error": "Invalid reset link"}

    if not default_token_generator.check_token(user, token):
        return {"error": "Invalid or expired token"}

    user.set_password(data.new_password)
    user.save()
    return {"success": "Password has been reset"}


@api.post("/blogs/", response=BlogOut, auth=JWTAuth())
def create_blog(request, data: BlogIn):
    blog = Blog.objects.create(
        title=data.title,
        description=data.description,
        category_id=data.category_id,
        author=request.user,
        is_active=data.is_active
    )
    blog.tags.set(data.tag_ids)
    return BlogOut(
        id=blog.id,
        title=blog.title,
        description=blog.description,
        category=blog.category.title if blog.category else "",
        tags=[tag.title for tag in blog.tags.all()],
        created_at=str(blog.created_at),
        is_active=blog.is_active,
        author=blog.author.username,
    )


@api.get("/blogs/", response=List[BlogOut])
@paginate(PageNumberPagination)
def list_blogs(
    request,
    q: Optional[str] = None,
    author: Optional[str] = None,
    category: Optional[int] = None,
    tag: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    blogs = Blog.objects.select_related('category', 'author').prefetch_related('tags').filter(is_active=True)

    if q:
        blogs = blogs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if author:
        blogs = blogs.filter(author__username__iexact=author)
    if category:
        blogs = blogs.filter(category_id=category)
    if tag:
        blogs = blogs.filter(tags__id=tag)
    if date_from:
        blogs = blogs.filter(created_at__date__gte=date_from)
    if date_to:
        blogs = blogs.filter(created_at__date__lte=date_to)

    return [
        BlogOut(
            id=blog.id,
            title=blog.title,
            description=blog.description,
            category=blog.category.title if blog.category else "",
            tags=[tag.title for tag in blog.tags.all()],
            created_at=blog.created_at,
            is_active=blog.is_active,
            author=blog.author.username,
        )
        for blog in blogs
    ]


@api.put("/blogs/{blog_id}", response={200: BlogOut, 403: ErrorSchema}, auth=JWTAuth())
def update_blog(request, blog_id: int, data: BlogIn):
    try:
        blog = Blog.objects.get(id=blog_id, author=request.user)
    except Blog.DoesNotExist:
        return 403, {"error": "You do not have permission to edit this blog."}

    blog.title = data.title
    blog.description = data.description
    blog.category_id = data.category_id
    blog.is_active = data.is_active
    blog.save()
    blog.tags.set(data.tag_ids)

    return BlogOut(
        id=blog.id,
        title=blog.title,
        description=blog.description,
        category=blog.category.title if blog.category else "",
        tags=[tag.title for tag in blog.tags.all()],
        created_at=blog.created_at,
        is_active=blog.is_active,
        author=blog.author.username,
    )


@api.delete("/blogs/{blog_id}", response={200: Dict[str, bool], 403: ErrorSchema},auth=JWTAuth())
def delete_blog(request, blog_id: int):
    try:
        blog = Blog.objects.get(id=blog_id, author=request.user)
    except Blog.DoesNotExist:
        return 403, {"error": "You do not have permission to delete this blog."}

    blog.delete()
    return {"success": True}


@api.get("/comments/", response=List[CommentOut])
def list_comments(request, blog: int):
    comments = Comment.objects.filter(blog_id=blog).select_related("author", "parent")
    return [
        CommentOut(
            id=c.id,
            content=c.content,
            blog_id=c.blog_id,
            author=c.author.username,
            parent_id=c.parent.id if c.parent else None,
            like=c.like,
            dislike=c.dislike,
        ) for c in comments
    ]


@api.post("/comments/", response={200: CommentOut, 400: ErrorSchema}, auth=JWTAuth())
def create_comment(request, data: CommentIn):
    parent_id = data.parent_id if data.parent_id != 0 else None
    if not Blog.objects.filter(id=data.blog_id).exists():
        return 400, {"error": "Blog does not exist."}
    if parent_id:
        try:
            parent = Comment.objects.get(id=parent_id)
            if parent.blog_id != data.blog_id:
                return 400, {"error": "Parent comment does not belong to the same blog."}
        except Comment.DoesNotExist:
            return 400, {"error": "Parent comment does not exist."}
    comment = Comment.objects.create(
        blog_id=data.blog_id,
        author=request.user,
        content=data.content,
        parent_id=parent_id
    )
    return CommentOut(
        id=comment.id,
        content=comment.content,
        blog_id=comment.blog_id,
        author=comment.author.username,
        parent_id=comment.parent.id if comment.parent else None,
        like=comment.like,
        dislike=comment.dislike,
    )


@api.put("/comments/{comment_id}", response={200: CommentOut, 403: ErrorSchema, 404: ErrorSchema}, auth=JWTAuth())
def update_comment(request, comment_id: int, data: CommentEdit):
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        return 404, {"error": "Comment not found"}

    if comment.author != request.user:
        return 403, {"error": "You do not have permission to edit this comment."}

    comment.content = data.content
    comment.save()

    return CommentOut(
        id=comment.id,
        content=comment.content,
        blog_id=comment.blog_id,
        author=comment.author.username,
        parent_id=comment.parent.id if comment.parent else None,
        like=comment.like,
        dislike=comment.dislike,
    )


@api.delete("/comments/{comment_id}", response={200: Dict[str, bool], 403: ErrorSchema, 404: ErrorSchema}, auth=JWTAuth())
def delete_comment(request, comment_id: int):
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        return 404, {"error": "Comment not found"}

    if comment.author != request.user:
        return 403, {"error": "You do not have permission to delete this comment."}

    comment.delete()
    return {"success": True}


@api.get("/categories/", response=List[CategoryOut])
def get_categories(request):
    return Category.objects.all()


@api.get("/tags/", response=List[TagOut])
def get_tags(request):
    return Tag.objects.all()


@api.get("/menus/", response=List[MenuOut])
def get_menus(request):
    return Menu.objects.order_by("order")


api.add_router("/auth", auth_router)
api.add_router("/blogs", blog_router)
api.add_router("/comments", comment_router)