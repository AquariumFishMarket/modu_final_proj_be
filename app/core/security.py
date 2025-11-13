# app/core/security.py
import os
from typing import Optional
from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User as UserModel
from app.models.session import Session as SessionModel

# -----------------------------
# 환경변수 로드
# -----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
TEMP_TOKEN_EXPIRE_MINUTES = int(os.getenv("TEMP_TOKEN_EXPIRE_MINUTES", 20))
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", 12))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# -----------------------------
# 비밀번호 해시 / 검증
# -----------------------------
def hash_password(password: str) -> str:
    trimmed = password[:72]
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(trimmed.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    trimmed = plain_password[:72]
    return bcrypt.checkpw(trimmed.encode("utf-8"), hashed_password.encode("utf-8"))

# -----------------------------
# JWT 토큰 생성 / 검증
# -----------------------------
def create_access_token(user_id: int, session_id: int) -> str:
    """
    Access Token 생성 (유효기간: ACCESS_TOKEN_EXPIRE_MINUTES)
    """
    payload = {
        "sub": str(user_id),         # 사용자 식별자
        "sid": str(session_id),      # 세션 식별자
        "type": "access",            # 토큰 타입
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),    # 토큰 발급 시간
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, session_id: int) -> str:
    """
    Refresh Token 생성 (유효기간: REFRESH_TOKEN_EXPIRE_DAYS)
    """
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_temp_token(user_id: int) -> str:
    """
    Temporary Token 생성 (유효기간: TEMP_TOKEN_EXPIRE_MINUTES)
    - 첫 로그인(초기 프로필 설정용)
    """
    payload = {
        "sub": str(user_id),
        "type": "temp",
        "exp": datetime.utcnow() + timedelta(minutes=TEMP_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )

# -----------------------------
# 현재 로그인 사용자 조회
# -----------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
    """
    FastAPI 라우터에서 Depends로 사용 가능.
    - 토큰에서 user_id를 추출하고 DB에서 실제 User 객체 조회
    - is_active=False인 경우, 즉 탈퇴한 유저는 인증 실패 처리
    - 토큰에서 session_id를 추출하고 DB에서 실제 Session 객체 조회
    - is_vaild=False인 경우, 즉 로그아웃된 세션은 인증 실패 처리
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    session_id = payload.get("sid")
    if user_id is None or session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )

    # user 존재 확인 및 is_active 체크
    user = db.query(UserModel).filter(UserModel.id == int(user_id), UserModel.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 사용자입니다."
        )
        
    # session 존재 확인 및 is_vaild 체크
    session = db.query(SessionModel).filter(SessionModel.id == int(session_id), SessionModel.user_id == int(user.id), SessionModel.is_valid == True).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 세션입니다."
        )
    
    return user

# -----------------------------
# 임시 토큰 기반 현재 사용자 조회
# -----------------------------
def get_current_user_from_temp_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
    """
    초기 로그인 시 발급된 임시 토큰 기반 유저 조회
    - 세션 체크 없음
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )

    user = db.query(UserModel).filter(UserModel.id == int(user_id), UserModel.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 사용자입니다."
        )

    return user


# -----------------------------
# 토큰에서 user_id, session_id 추출 (optional)
# -----------------------------
def get_user_from_token(token: str) -> dict:
    """
    유틸용: 토큰 payload에서 user_id와 session_id 추출
    """
    payload = decode_token(token)
    return {
        "user_id": int(payload.get("sub")) if payload.get("sub") else None,
        "session_id": int(payload.get("sid")) if payload.get("sid") else None,
        "token_type": payload.get("type")
    }
