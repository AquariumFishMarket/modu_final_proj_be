# schemas/post.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from hashtag import HashtagResponse
from fastapi import UploadFile, Form

# --- 공통 스키마 ---
class PostBase(BaseModel):
    title: str
    content: str
    image_urls: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None  # 해시태그 내용 직접 받음


# --- 요청 스키마 ---
class PostCreate(BaseModel):
    """
    POST /api/posts
    게시물 작성
    """
    title: str
    content: str
    images: Optional[List[UploadFile]] = None
    hashtags: Optional[List[str]] = None
    
    @classmethod
    def as_form(
        cls,
        title: str = Form(...),
        content: str = Form(...),
        images: Optional[List[UploadFile]] = None,
        hashtags: Optional[List[str]] = None
    ):
        return cls(title=title, content=content, images=images, hashtags=hashtags)


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    images: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None


# --- 응답 스키마 ---
class PostDetailResponse(BaseModel):
    id: int
    title: str
    content: str
    image_urls: Optional[List[str]]
    author_id: int
    author_account_id: str
    author_username: str
    author_image_url: str
    hashtags: List[HashtagResponse] = []
    like_count: int
    comment_count: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    is_blurred: bool
    is_deleted: bool
    report_count: int

    class Config:
        orm_mode = True


# 관리자 전용 (선택)
class PostAdminResponse(PostDetailResponse):
    pass
