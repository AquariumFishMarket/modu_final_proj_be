# app/routers/comment.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from typing import List

from app.database import get_db
from app.models.comment import Comment as CommentModel
from app.models.post import Post as PostModel
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from app.core.security import get_current_user
from app.models.user import User as UserModel

router = APIRouter(
    prefix="/api/posts/{post_id}/comments",
    tags=["Comment"]
)

# -----------------------------
# ORM 모델 -> Pydantic 변환 유틸
# -----------------------------
def map_comment_to_response(comment: CommentModel, include_replies: bool = True) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        username=comment.user.username,
        account_id=comment.user.account_id,
        profile_image_url=comment.user.profile_image_url,
        content=comment.content,
        parent_comment_id=comment.parent_comment_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        is_blurred=comment.is_blurred,
        is_deleted=comment.is_deleted,
        report_count=comment.report_count,
        replies=[map_comment_to_response(child) for child in comment.child_comments if not child.is_deleted] if include_replies else []
    )


# -----------------------------
# 댓글 작성
# -----------------------------
@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    post = db.query(PostModel).filter(PostModel.id == post_id, PostModel.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    new_comment = CommentModel(
        post_id=post_id,
        user_id=current_user.id,
        content=comment_in.content,
        parent_comment_id=None
    )
    db.add(new_comment)
    post.comment_count += 1
    db.commit()
    db.refresh(new_comment)
    return map_comment_to_response(new_comment, include_replies=False)


# -----------------------------
# 댓글 목록 조회 (최적화 적용)
# -----------------------------
@router.get("", response_model=List[CommentResponse])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    post = db.query(PostModel).filter(PostModel.id == post_id, PostModel.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    comments = (
        db.query(CommentModel)
        .options(
            selectinload(CommentModel.user),         # 작성자 미리 로드
            selectinload(CommentModel.child_comments).selectinload(CommentModel.user)  # 대댓글 + 작성자 로드
        )
        .filter(CommentModel.post_id == post_id, CommentModel.parent_comment_id == None, CommentModel.is_deleted == False)
        .order_by(CommentModel.created_at.asc())
        .all()
    )

    return [map_comment_to_response(c) for c in comments]


# -----------------------------
# 댓글 수정
# -----------------------------
@router.patch("/{comment_id}", response_model=CommentResponse)
def update_comment(
    post_id: int,
    comment_id: int,
    comment_in: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    comment = db.query(CommentModel).filter(CommentModel.id == comment_id, CommentModel.post_id == post_id, CommentModel.is_deleted == False).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="댓글 수정 권한이 없습니다.")

    if comment_in.content is not None:
        comment.content = comment_in.content

    db.commit()
    db.refresh(comment)
    return map_comment_to_response(comment, include_replies=False)


# -----------------------------
# 댓글 삭제 (soft delete)
# -----------------------------
@router.delete("/{comment_id}", response_model=dict)
def delete_comment(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    comment = db.query(CommentModel).filter(CommentModel.id == comment_id, CommentModel.post_id == post_id, CommentModel.is_deleted == False).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="댓글 삭제 권한이 없습니다.")

    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if post:
        post.comment_count = max(post.comment_count - 1, 0)

    comment.is_deleted = True
    # 대댓글도 soft delete
    for child in comment.child_comments:
        child.is_deleted = True

    db.commit()
    return {"detail": "댓글이 삭제되었습니다."}


# -----------------------------
# 대댓글 작성
# -----------------------------
@router.post("/{comment_id}/replies", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_reply(
    post_id: int,
    comment_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    parent_comment = db.query(CommentModel).filter(CommentModel.id == comment_id, CommentModel.post_id == post_id, CommentModel.is_deleted == False).first()
    if not parent_comment:
        raise HTTPException(status_code=404, detail="부모 댓글을 찾을 수 없습니다.")

    new_reply = CommentModel(
        post_id=post_id,
        user_id=current_user.id,
        content=comment_in.content,
        parent_comment_id=parent_comment.id
    )
    db.add(new_reply)

    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if post:
        post.comment_count += 1

    db.commit()
    db.refresh(new_reply)
    return map_comment_to_response(new_reply, include_replies=False)
