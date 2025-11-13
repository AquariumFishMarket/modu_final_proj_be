# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.schemas.auth import SignupRequest, SignupResponse, LoginRequest, LoginResponse, LogoutRequest, WithdrawRequest, RefreshRequest, TokenPayload
from app.models.user import User as UserModel
from app.models.session import Session as SessionModel
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, create_temp_token, decode_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# -----------------------------
# 회원가입
# -----------------------------
@router.post("/signup", response_model=SignupResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    # 이메일 중복 확인
    existing_user = db.query(UserModel).filter(UserModel.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 존재하는 이메일입니다.")

    hashed_password = hash_password(request.password)
    user = UserModel(email=request.email, password_hash=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return SignupResponse(user_id=user.id, email=user.email, created_at=user.created_at)


# -----------------------------
# 로그인
# -----------------------------
@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == request.email, UserModel.is_active == True).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    # 첫 로그인 판단: 계정ID 존재 여부
    if not user.account_id:
        temp_token = create_temp_token(user.id)
        return LoginResponse(
            is_initial_login=True,
            temporary_token=temp_token,
            user_id=user.id,
            account_id=user.account_id,
            username=user.username
        )
    
    # 기존 사용자의 경우
    # 사용자의 기존 세션 모두 무효화
    db.query(SessionModel).filter(SessionModel.user_id == user.id, SessionModel.is_valid == True).update(
    {SessionModel.is_valid: False}
    )
    db.commit()

    # 새 세션 생성
    session = SessionModel(
        user_id=user.id,
        refresh_token_hash="", # 나중에 업데이트
        is_valid=True,
        created_at=datetime.utcnow())
    db.add(session)
    db.commit()
    db.refresh(session)

    # Access/Refresh 토큰 발급
    access_token = create_access_token(user.id, session.id)
    refresh_token = create_refresh_token(user.id, session.id)

    # Refresh token 해시 DB에 저장
    refresh_token_hash = hash_password(refresh_token)
    session.refresh_token_hash = refresh_token_hash
    db.commit()

    return LoginResponse(
        is_initial_login=False,
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        account_id=user.account_id,
        username=user.username
    )


# -----------------------------
# 로그아웃
# -----------------------------
@router.post("/logout")
def logout(request: LogoutRequest, db: Session = Depends(get_db)):
    """
    Refresh Token 기반 로그아웃.
    - 전달된 refresh_token을 디코드하여 session_id(sid) 추출
    - 해당 세션만 is_valid=False로 처리
    """
    try:
        payload = decode_token(request.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )

    session_id = payload.get("sid")
    user_id = payload.get("sub")

    if not session_id or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="세션 정보가 누락되었습니다."
        )

    # 세션 조회
    session = db.query(SessionModel).filter(
        SessionModel.id == int(session_id),
        SessionModel.user_id == int(user_id),
        SessionModel.is_valid == True
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효한 세션이 없습니다."
        )
    
    # Refresh Token 검증
    if not verify_password(request.refresh_token, session.refresh_token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token이 일치하지 않습니다."
        )

    # 세션 무효화
    session.is_valid = False
    db.commit()

    return {"detail": "로그아웃이 완료되었습니다."}


# -----------------------------
# 회원 탈퇴
# -----------------------------
@router.delete("/withdraw")
def withdraw(
    request: WithdrawRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Access Token 기반 회원 탈퇴.
    - 비밀번호 확인 후 Soft Delete (is_active=False)
    - 해당 사용자의 모든 세션 무효화
    """
    # 비밀번호 검증
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 올바르지 않습니다."
        )

    # 모든 세션 무효화
    db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id,
        SessionModel.is_valid == True
    ).update({SessionModel.is_valid: False})

    # Soft delete (계정 비활성화)
    current_user.is_active = False
    db.commit()

    return {"detail": "회원 탈퇴가 완료되었습니다."}

# -----------------------------
# refresh 토큰을 이용한 access 토큰 재발급
# -----------------------------
@router.post("/refresh", response_model=TokenPayload)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """
    Refresh Token 기반 access token 재발급
    """
    try:
        payload = decode_token(request.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )

    session_id = payload.get("sid")
    user_id = payload.get("sub")

    if not session_id or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="세션 정보가 누락되었습니다."
        )

    # 기존 세션 조회
    session = db.query(SessionModel).filter(
        SessionModel.id == int(session_id),
        SessionModel.user_id == int(user_id),
        SessionModel.is_valid == True
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효한 세션이 없습니다."
        )

    # Refresh Token 검증
    if not verify_password(request.refresh_token, session.refresh_token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token이 일치하지 않습니다."
        )

    # 기존 세션 무효화
    session.is_valid = False
    db.commit()

    # 새 세션 생성 (refresh_token_hash 재사용)
    new_session = SessionModel(
        user_id=session.user_id,
        refresh_token_hash=session.refresh_token_hash,
        is_valid=True,
        created_at=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # 새 access token 발급
    new_access_token = create_access_token(session.user_id, new_session.id)

    return TokenPayload(
        access_token=new_access_token,        # 새 access token
        refresh_token=request.refresh_token,  # refresh token은 기존의 것을 그대로 유지
        token_type="bearer"
    )