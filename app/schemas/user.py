# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# -----------------------------
# Common / Base
# -----------------------------
class UserBase(BaseModel):
    """
    공통 유저 필드 (읽기용). ORM -> Pydantic 변환을 위해 orm_mode = True 포함.
    """
    id: int
    account_id: Optional[str] = None
    username: Optional[str] = None
    email: EmailStr
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: bool

    class Config:
        orm_mode = True


# -----------------------------
# Requests
# -----------------------------
class InitialProfileRequest(BaseModel):
    """
    POST /api/users/initial-profile
    - 첫 로그인 시 사용 (임시 JWT로 인증)
    - username, account_id는 필수
    """
    username: str
    account_id: str
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """
    PATCH /api/users/me
    - 일반 프로필 수정 API (로그인 세션 필요)
    - 모든 필드는 optional (부분 수정 허용)
    """
    username: Optional[str] = None
    account_id: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None


# (Optional) 서버 내부에서 새 유저 생성용 스키마가 따로 필요하면 추가.
# 회원가입은 auth.SignupRequest를 사용하므로 여기서는 생략 가능.


# -----------------------------
# Responses
# -----------------------------
class UserDetailResponse(UserBase):
    """
    GET /api/users/me 또는 GET /api/users/{user_id}
    필요한 모든 조회용 필드를 포함.
    """
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # 선택적으로 팔로워/팔로잉 수를 포함하면 프론트에서 편리합니다.
    follower_count: Optional[int] = 0
    following_count: Optional[int] = 0

    class Config:
        orm_mode = True


class UserListItem(BaseModel):
    """
    사용자 검색 / 리스트 응답(피드나 팔로워 리스트 등)
    """
    id: int
    account_id: Optional[str] = None
    username: Optional[str] = None
    profile_image_url: Optional[str] = None

    class Config:
        orm_mode = True


class FollowResponse(BaseModel):
    """
    팔로워 / 팔로잉 목록 항목에 사용
    """
    id: int
    account_id: Optional[str] = None
    username: Optional[str] = None
    profile_image_url: Optional[str] = None

    class Config:
        orm_mode = True
