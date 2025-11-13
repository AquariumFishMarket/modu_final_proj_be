# app/routers/user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.schemas.user import InitialProfileRequest, InitialProfileResponse
from app.models.user import User as UserModel
from app.models.session import Session as SessionModel
from app.core.security import get_current_user_from_temp_token, create_access_token, create_refresh_token, hash_password
from app.utils.s3_bucket import upload_image_to_s3

router = APIRouter(prefix="/api/users", tags=["User"])

# -----------------------------
# 초기 프로필 설정 API
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
