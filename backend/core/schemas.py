from typing import List
from ninja import Schema
from datetime import datetime
from typing import Optional
from pydantic import EmailStr


class ErrorSchema(Schema):
    error: str


class CommentIn(Schema):
    blog_id: int
    content: str
    parent_id: Optional[int] = None


class CommentOut(Schema):
    id: int
    content: str
    blog_id: int
    author: str
    parent_id: Optional[int]
    like: int
    dislike: int


class CommentEdit(Schema):
    content: str


class BlogIn(Schema):
    title: str
    description: str
    category_id: int
    tag_ids: List[int]
    is_active: bool


class BlogOut(Schema):
    id: int
    title: str
    description: str
    category: str
    tags: List[str]
    created_at: datetime
    is_active: bool
    author: str


class CategoryOut(Schema):
    id: int
    title: str
    parent_id: Optional[int]


class TagOut(Schema):
    id: int
    title: str


class MenuOut(Schema):
    id: int
    title: str
    order: int
    category_id: Optional[int]
    url: Optional[str]


class ProfileUpdateSchema(Schema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    profile_image: Optional[str] = None


class RegisterSchema(Schema):
    username: str
    password: str
    email: EmailStr
    profile_image: Optional[str] = None


class ChangePasswordSchema(Schema):
    old_password: str
    new_password: str


class ForgotPasswordSchema(Schema):
    email: EmailStr


class ResetPasswordSchema(Schema):
    new_password: str

