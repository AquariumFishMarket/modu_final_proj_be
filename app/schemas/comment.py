# schemas/comment.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# --- 공통 스키마 ---
class CommentBase(BaseModel):
    content: str
    parent_comment_id: Optional[int] = None  # 대댓글일 경우 상위 댓글 ID


# --- 요청 스키마 ---
class CommentCreate(CommentBase):
    """
    POST /api/comments/
    - 게시글에 댓글 작성 시 사용
    """
    post_id: int


class CommentUpdate(BaseModel):
    """
    PATCH /api/comments/{comment_id}
    - 댓글 내용 수정 시 사용
    """
    content: Optional[str] = None


# --- 응답 스키마 ---
class CommentResponse(BaseModel):
    """
    댓글 조회 시 반환되는 데이터 구조
    """
    id: int
    post_id: int
    user_id: int
    username: str
    account_id: str
    profile_image_url: Optional[str]
    content: str
    parent_comment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_blurred: bool = False
    is_deleted: bool = False
    report_count: int = 0
    replies: Optional[List["CommentResponse"]] = [] # 대댓글 목록

    class Config:
        orm_mode = True