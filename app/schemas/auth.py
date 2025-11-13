# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# -----------------------------
# Requests
# -----------------------------
class SignupRequest(BaseModel):
    """
    POST /api/auth/signup
    회원가입: 이메일 + 비밀번호만 받음 (초기 프로필은 별도 API로 처리)
    """
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """
    POST /api/auth/login
    이메일 + 비밀번호로 로그인 시도
    """
    email: EmailStr
    password: str


class LogoutRequest(BaseModel):
    """
    POST /api/auth/logout
    로그아웃 처리에 사용 (refresh token 무효화 등)
    """
    refresh_token: str


class WithdrawRequest(BaseModel):
    """
    DELETE /api/auth/withdraw
    회원 탈퇴 요청 (본인 확인용 비밀번호 등 필요하면 포함)
    """
    password: str

class RefreshRequest(BaseModel):
    """
    POST /api/auth/refresh
    access 토큰 재발급 요청
    """
    refresh_token: str

# -----------------------------
# Responses
# -----------------------------
class TokenPayload(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """
    로그인 응답.
    - 일반 로그인(정상): access_token/refresh_token 반환
    - 첫 로그인(초기 프로필 필요): is_initial_login=True와 함께
      임시 인증용 토큰(temporary_token)을 발급해 초기 프로필 API 인증에 사용.
    """
    # basic token fields (one of access_token or temporary_token will be present depending on flow)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    temporary_token: Optional[str] = None  # 임시 JWT (첫 로그인 흐름 시 사용)
    token_type: str = "bearer"

    # flags + user info
    is_initial_login: bool = False
    user_id: Optional[int] = None
    account_id: Optional[str] = None
    username: Optional[str] = None

    class Config:
        orm_mode = True


class SignupResponse(BaseModel):
    """
    회원가입 성공 응답: 간단한 확인용 정보 반환.
    일반적인 흐름에서는 가입 후 클라이언트가 로그인 화면으로 이동.
    """
    user_id: int
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True
