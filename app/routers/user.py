# app/routers/user.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import get_db
from app.schemas.user import InitialProfileRequest, InitialProfileResponse, UserDetailResponse, UserUpdateRequest, UserListItem, FollowResponse
from app.schemas.product import ProductDetailResponse
from app.models.user import User as UserModel
from app.models.follow import Follow as FollowModel
from app.models.session import Session as SessionModel
from app.models.product import Product as ProductModel
from app.models.product_like import ProductLike as ProductLikeModel
from app.core.security import get_current_user, get_current_user_from_temp_token, create_access_token, create_refresh_token, hash_password
from app.utils.s3_bucket import upload_image_to_s3

router = APIRouter(prefix="/api/users", tags=["User"])

# -----------------------------
# 초기 프로필 설정
# -----------------------------
@router.post("/initial-profile", response_model=InitialProfileResponse)
def set_initial_profile(
    request: InitialProfileRequest = Depends(InitialProfileRequest.as_form),
    current_user: UserModel = Depends(get_current_user_from_temp_token),
    db: Session = Depends(get_db)
):
    """
    첫 로그인 시 초기 프로필 설정
    - username, account_id 필수
    - bio, profile_image 선택
    - profile_image는 S3 업로드 후 image_url 저장
    - 프로필 설정 완료 후 access token / refresh token 발급
    """
    # username / account_id 필수 검증
    if not request.username or not request.account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username과 account_id는 필수입니다."
        )

    # account_id 중복 확인
    existing_user = db.query(UserModel).filter(
        UserModel.account_id == request.account_id,
        UserModel.id != current_user.id
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 account_id입니다."
        )

    # 프로필 이미지 업로드 및 업데이트
    image_url = None
    if request.profile_image:
        try:
            image_url = upload_image_to_s3(request.profile_image, folder="profile-images")
            current_user.profile_image_url = image_url
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"프로필 이미지 업로드 실패: {str(e)}"
            )

    # 프로필 정보 업데이트
    current_user.username = request.username
    current_user.account_id = request.account_id
    if request.bio:
        current_user.bio = request.bio
    
    # DB에 프로필 정보 저장
    db.commit()
    db.refresh(current_user)

    # 새 세션 생성
    new_session = SessionModel(
        user_id=current_user.id,
        refresh_token_hash="",  # 나중에 refresh_token 해시 업데이트
        is_valid=True,
        created_at=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    # access / refresh 토큰 발급
    access_token = create_access_token(current_user.id, new_session.id)
    refresh_token = create_refresh_token(current_user.id, new_session.id)
    
    # refresh token 해시 DB에 저장
    refresh_token_hash = hash_password(refresh_token)
    new_session.refresh_token_hash = refresh_token_hash
    db.commit()
    
    return InitialProfileResponse(
        id=current_user.id,
        account_id=current_user.account_id,
        username=current_user.username,
        email=current_user.email,
        bio=current_user.bio,
        profile_image_url=current_user.profile_image_url,
        is_active=current_user.is_active,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


# -----------------------------
# 내 프로필 조회
# -----------------------------
@router.get("/me", response_model=UserDetailResponse)
def get_my_profile(current_user: UserModel = Depends(get_current_user)):
    """
    로그인된 사용자의 프로필 조회
    """
    
    return UserDetailResponse(
        id=current_user.id,
        account_id=current_user.account_id,
        username=current_user.username,
        email=current_user.email,
        bio=current_user.bio,
        profile_image_url=current_user.profile_image_url,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        follower_count=len(current_user.followers),
        following_count=len(current_user.followings),
    )
    
    
# -----------------------------
# 내 프로필 수정
# -----------------------------
@router.patch("/me", response_model=UserDetailResponse)
def update_my_profile(
    request: UserUpdateRequest = Depends(UserUpdateRequest.as_form),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    로그인된 사용자의 프로필 수정
    - username, account_id, bio, profile_image (optional)
    """
    # account_id 중복 확인
    if request.account_id:
        existing_user = db.query(UserModel).filter(
            UserModel.account_id == request.account_id,
            UserModel.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 account_id입니다."
            )

    # 프로필 이미지 업로드
    if request.profile_image:
        try:
            image_url = upload_image_to_s3(request.profile_image, folder="profile-images")
            current_user.profile_image_url = image_url
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"프로필 이미지 업로드 실패: {str(e)}"
            )

    # 필드 업데이트
    if request.username:
        current_user.username = request.username
    if request.account_id:
        current_user.account_id = request.account_id
    if request.bio is not None:
        current_user.bio = request.bio

    db.commit()
    db.refresh(current_user)

    return UserDetailResponse(
        id=current_user.id,
        account_id=current_user.account_id,
        username=current_user.username,
        email=current_user.email,
        bio=current_user.bio,
        profile_image_url=current_user.profile_image_url,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        follower_count=len(current_user.followers),
        following_count=len(current_user.followings),
    )


# -----------------------------
# 사용자 검색
# -----------------------------
@router.get("/search", response_model=List[UserListItem])
def search_users(
    name: str = Query(..., min_length=1, max_length=50, description="검색할 사용자 이름"),
    db: Session = Depends(get_db),
):
    """
    username에 name이 포함된 사용자를 검색.
    대소문자 구분 없이 부분 일치 검색 수행.
    """
    users = db.query(UserModel).filter(
        UserModel.is_active == True,
        UserModel.username.ilike(f"%{name}%")
    ).all()

    return [
        UserListItem(
            id=u.id,
            account_id=u.account_id,
            username=u.username,
            profile_image_url=u.profile_image_url
        )
        for u in users
    ]


# -----------------------------
# 특정 사용자 프로필 조회
# -----------------------------
@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """
    특정 사용자 프로필 조회
    """
    
    user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    
    return UserDetailResponse(
        id=user.id,
        account_id=user.account_id,
        username=user.username,
        email=user.email,
        bio=user.bio,
        profile_image_url=user.profile_image_url,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        follower_count=len(user.followers),
        following_count=len(user.followings),
    )


# -----------------------------
# 사용자 팔로우
# -----------------------------
@router.post("/{user_id}/follow", response_model=dict)
def follow_user(user_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    특정 사용자 팔로우
    """
    
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="자기 자신을 팔로우할 수 없습니다.")

    # 이미 팔로우 중인지 확인
    existing_follow = db.query(FollowModel).filter(
        FollowModel.follower_id == current_user.id,
        FollowModel.following_id == user_id
    ).first()

    if existing_follow:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 팔로우한 사용자입니다.")

    # 팔로우 생성 후 DB에 저장
    follow = FollowModel(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    db.commit()
    db.refresh(follow)
    
    return {"detail": "사용자를 팔로우했습니다."}


# -----------------------------
# 사용자 언팔로우
# -----------------------------
@router.delete("/{user_id}/follow", response_model=dict)
def unfollow_user(user_id: int, current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    특정 사용자 언팔로우
    """
    
    # 팔로우 중인지 확인
    follow = db.query(FollowModel).filter(
        FollowModel.follower_id == current_user.id,
        FollowModel.following_id == user_id
    ).first()
    if not follow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="팔로우 관계가 없습니다.")
    
    # 언팔로우 처리 후 DB 저장
    db.delete(follow)
    db.commit()
    
    return {"detail": "사용자 언팔로우 완료."}


# -----------------------------
# 팔로워 목록
# -----------------------------
@router.get("/{user_id}/followers", response_model=List[FollowResponse])
def get_followers(user_id: int, db: Session = Depends(get_db)):
    """
    특정 사용자의 팔로워 목록 조회.
    즉, 해당 user_id의 사용자를 팔로잉하는 사용자들 조회.
    """
    
    followers = db.query(FollowModel).filter(FollowModel.following_id == user_id).all()
    result = [
        FollowResponse(
            id=f.follower_user.id,
            account_id=f.follower_user.account_id,
            username=f.follower_user.username,
            profile_image_url=f.follower_user.profile_image_url
        )
        for f in followers
    ]
    return result


# -----------------------------
# 팔로잉 목록
# -----------------------------
@router.get("/{user_id}/followings", response_model=List[FollowResponse])
def get_followings(user_id: int, db: Session = Depends(get_db)):
    """
    특정 사용자의 팔로잉 목록 조회.
    즉, 해당 user_id의 사용자가 팔로우하는 사용자들 조회.
    """
    
    followings = db.query(FollowModel).filter(FollowModel.follower_id == user_id).all()
    result = [
        FollowResponse(
            id=f.following_user.id,
            account_id=f.following_user.account_id,
            username=f.following_user.username,
            profile_image_url=f.following_user.profile_image_url
        )
        for f in followings
    ]
    return result


# -----------------------------
# 특정 사용자의 상품 목록 조회
# -----------------------------
@router.get("/{user_id}/products", response_model=List[ProductDetailResponse])
def get_user_products(user_id: int, db: Session = Depends(get_db)):
    """
    특정 사용자가 판매 중인 상품 목록 조회
    """
    
    user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

    products = db.query(ProductModel).filter(
        ProductModel.seller_id == user_id,
        ProductModel.is_deleted == False
    ).all()

    result = []
    for product in products:
        image_urls = [img.image_url for img in product.images]
        result.append(ProductDetailResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            product_url=product.product_url,
            image_urls=image_urls,
            seller_id=user.id,
            seller_account_id=user.account_id,
            seller_username=user.username,
            seller_image_url=user.profile_image_url or "",
            like_count=product.like_count,
            view_count=product.view_count,
            created_at=product.created_at,
            updated_at=product.updated_at,
            is_blurred=product.is_blurred,
            is_deleted=product.is_deleted,
            report_count=product.report_count,
        ))
    return result


# -----------------------------
# 특정 사용자가 좋아요한 상품 목록 조회
# -----------------------------
@router.get("/{user_id}/likes/products", response_model=List[ProductDetailResponse])
def get_user_liked_products(user_id: int, db: Session = Depends(get_db)):
    """
    특정 사용자가 좋아요한 상품 목록 조회
    """
    
    user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

    likes = db.query(ProductLikeModel).filter(ProductLikeModel.user_id == user_id).all()
    result = []

    for like in likes:
        product = like.product
        if product.is_deleted:
            continue
        image_urls = [img.image_url for img in product.images]
        seller = product.seller
        result.append(ProductDetailResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            product_url=product.product_url,
            image_urls=image_urls,
            seller_id=seller.id,
            seller_account_id=seller.account_id,
            seller_username=seller.username,
            seller_image_url=seller.profile_image_url or "",
            like_count=product.like_count,
            view_count=product.view_count,
            created_at=product.created_at,
            updated_at=product.updated_at,
            is_blurred=product.is_blurred,
            is_deleted=product.is_deleted,
            report_count=product.report_count,
        ))
    return result
