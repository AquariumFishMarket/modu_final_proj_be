# routers/post.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.post import Post as PostModel
from app.models.post_like import PostLike
from app.models.post_image import PostImage
from app.models.post_hashtag import PostHashtag
from app.models.hashtag import Hashtag
from app.schemas.user import UserListItem
from app.schemas.post import PostCreate, PostUpdate, PostDetailResponse
from app.schemas.hashtag import HashtagResponse
from app.core.security import get_current_user
from app.models.user import User as UserModel
from app.utils.s3_bucket import upload_image_to_s3

router = APIRouter(prefix="/api/posts", tags=["Posts"])

# -----------------------------
# ORM 모델 -> Pydantic 스키마 변환 메서드
# -----------------------------
def map_post_to_response(post: PostModel) -> PostDetailResponse:
    return PostDetailResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        image_urls=[img.image_url for img in post.images],
        author_id=post.user.id,
        author_account_id=post.user.account_id,
        author_username=post.user.username,
        author_image_url=post.user.profile_image_url,
        hashtags=[HashtagResponse(id=ph.hashtag.id, name=ph.hashtag.name) for ph in post.hashtags],
        like_count=post.like_count,
        comment_count=post.comment_count,
        view_count=post.view_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
        is_blurred=post.is_blurred,
        is_deleted=post.is_deleted,
        report_count=post.report_count
    )


# -----------------------------
# 홈 피드 조회
# -----------------------------
@router.get("/feed", response_model=List[PostDetailResponse])
def get_feed(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    팔로우한 유저들의 게시글 최신순으로 조회
    """
    # 팔로잉 유저 ID 조회
    following_ids = [f.following_id for f in current_user.followings]
    posts = db.query(PostModel).filter(
        PostModel.user_id.in_(following_ids),
        PostModel.is_deleted == False
    ).order_by(PostModel.created_at.desc()).all()
    
    return [map_post_to_response(post) for post in posts]


# -----------------------------
# 게시글 작성
# -----------------------------
@router.post("", response_model=PostDetailResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post_in: PostCreate = Depends(PostCreate.as_form),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    새 게시글 작성
    이미지 최대 10장 업로드 가능
    """
    
    # Post 객체 생성
    post = PostModel(
        user_id=current_user.id,
        title=post_in.title,
        content=post_in.content
    )
    db.add(post)
    db.flush()  # id 생성

    # 이미지 업로드 처리
    image_urls = []
    if post_in.images:
        for img in post_in.images[:10]:  # 최대 10장
            url = upload_image_to_s3(img, folder="posts")
            post_image = PostImage(post_id=post.id, image_url=url)
            db.add(post_image)
            image_urls.append(url)

    # 해시태그 처리
    hashtags = []
    if post_in.hashtags:
        for tag_name in post_in.hashtags:
            hashtag = db.query(Hashtag).filter_by(name=tag_name).first()
            if not hashtag:
                hashtag = Hashtag(name=tag_name)
                db.add(hashtag)
                db.flush()
            post_hashtag = PostHashtag(post_id=post.id, hashtag_id=hashtag.id)
            db.add(post_hashtag)
            hashtags.append(hashtag)

    db.commit()
    db.refresh(post)
    return map_post_to_response(post)


# -----------------------------
# 게시글 상세 조회
# -----------------------------
@router.get("/{post_id}", response_model=PostDetailResponse)
def get_post_detail(post_id: int, db: Session = Depends(get_db)):
    """
    게시글 상세 조회
    api 호출 시 조회수 1 증가
    """
    
    
    post = db.query(PostModel).filter(PostModel.id == post_id, PostModel.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    # 조회수 증가
    post.view_count += 1
    db.commit()
    db.refresh(post)
    return map_post_to_response(post)


# -----------------------------
# 게시글 수정
# -----------------------------
@router.patch("/{post_id}", response_model=PostDetailResponse)
def update_post(
    post_id: int,
    post_in: PostUpdate = Depends(PostUpdate.as_form),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    게시글 수정
    """
    
    post = db.query(PostModel).filter(PostModel.id == post_id, PostModel.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인의 게시글만 수정 가능합니다.")

    if post_in.title is not None:
        post.title = post_in.title
    if post_in.content is not None:
        post.content = post_in.content

    # 이미지 업로드 처리 (기존 이미지 삭제 후 새 이미지 추가)
    if post_in.images is not None:
        # 기존 이미지 삭제
        for img in post.images:
            db.delete(img)
        db.flush()

        # 새 이미지 업로드
        for img in post_in.images[:10]:
            url = upload_image_to_s3(img, folder="posts")
            post_image = PostImage(post_id=post.id, image_url=url)
            db.add(post_image)

    # 해시태그 처리 (기존 삭제 후 새로 추가)
    if post_in.hashtags is not None:
        for ph in post.hashtags:
            db.delete(ph)
        db.flush()
        for tag_name in post_in.hashtags:
            hashtag = db.query(Hashtag).filter_by(name=tag_name).first()
            if not hashtag:
                hashtag = Hashtag(name=tag_name)
                db.add(hashtag)
                db.flush()
            post_hashtag = PostHashtag(post_id=post.id, hashtag_id=hashtag.id)
            db.add(post_hashtag)

    db.commit()
    db.refresh(post)
    return map_post_to_response(post)


# -----------------------------
# 게시글 삭제
# -----------------------------
@router.delete("/{post_id}", response_model=dict)
def delete_post(post_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    게시글 삭제
    soft delete 방식 (is_deleted 필드 True로 변경)
    본인의 게시글만 삭제 가능
    """
    
    post = db.query(PostModel).filter(PostModel.id == post_id, PostModel.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인의 게시글만 삭제 가능합니다.")
    
    post.is_deleted = True
    db.commit()
    return {"detail": "게시글이 삭제되었습니다."}


# -----------------------------
# 게시글 좋아요 등록
# -----------------------------
@router.post("/{post_id}/likes", status_code=status.HTTP_201_CREATED)
def like_post(post_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    게시글 좋아요 등록
    로그인한 사용자가 이미 좋아요한 게시글은 중복 좋아요 불가
    """
    
    post = db.query(PostModel).filter(PostModel.id == post_id, PostModel.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    # 이미 좋아요했는지 확인
    existing_like = db.query(PostLike).filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing_like:
        raise HTTPException(status_code=400, detail="이미 좋아요를 눌렀습니다.")

    like = PostLike(user_id=current_user.id, post_id=post.id)
    post.like_count += 1
    db.add(like)
    db.commit()
    db.refresh(post)
    return {"detail": "게시글 좋아요가 등록되었습니다."}


# -----------------------------
# 게시글 좋아요 취소
# -----------------------------
@router.delete("/{post_id}/likes", status_code=status.HTTP_200_OK)
def unlike_post(post_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    게시글 좋아요 취소
    로그인한 사용자가 좋아요하지 않은 게시글은 취소 불가
    """
    
    post = db.query(PostModel).filter(PostModel.id == post_id, PostModel.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    # 좋아요 여부 확인
    like = db.query(PostLike).filter(PostLike.user_id == current_user.id, PostLike.post_id == post_id).first()
    if not like:
        raise HTTPException(status_code=404, detail="좋아요가 존재하지 않습니다.")
    
    db.delete(like)
    if post.like_count > 0:
        post.like_count -= 1
    db.commit()
    return {"detail": "게시글 좋아요가 취소되었습니다."}


# -----------------------------
# 게시글 좋아요한 사용자 목록 조회
# -----------------------------
@router.get("/{post_id}/likes", response_model=List[UserListItem])
def get_post_likes(post_id: int, db: Session = Depends(get_db)):
    """
    특정 게시글을 좋아요한 사용자 목록 조회
    """
    post = db.query(PostModel).filter(PostModel.id == post_id, PostModel.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    liked_users = [like.user for like in post.likes]  # PostLike.relationship(user)
    return liked_users
