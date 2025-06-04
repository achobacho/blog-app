from ninja import NinjaAPI
from ninja.security import HttpBearer
from django.http import HttpRequest
from core.models import User, Comment, Blog, Tag, Category, Menu
from ninja import Router
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from core.schemas import BlogIn, BlogOut, ErrorSchema, CommentIn, CommentOut, CommentEdit, CategoryOut, TagOut, MenuOut
from rest_framework_simplejwt.authentication import JWTAuthentication
from typing import List, Optional, Dict
from django.db.models import Q
from ninja.pagination import paginate, PageNumberPagination
# Restrict access to admin users

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

        # ✅ Enforce that the user must have the custom permission
        if user.has_perm("core.view_api_docs"):
            request.user = user
            return user

        return None

api = NinjaAPI(
    title="Blog API",
    version="1.0.0",
    docs_url="/docs",  # Swagger page
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
    user = authenticate(username=username, password=password)
    if not user:
        return {"error": "Invalid credentials"}

    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

@auth_router.post("/register")
def register(request, username: str, password: str):
    if User.objects.filter(username=username).exists():
        return {"error": "Username already exists"}

    user = User.objects.create_user(username=username, password=password)
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

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