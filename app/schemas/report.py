# app/schemas/report.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


# -----------------------------
# Enum
# -----------------------------
class TargetType(str, Enum):
    post = "post"
    comment = "comment"
    product = "product"
    message = "message"


# -----------------------------
# 요청 스키마
# -----------------------------
class ReportCreateRequest(BaseModel):
    """
    POST /api/reports
    신고 생성 요청
    """
    target_type: TargetType
    target_id: Optional[int] = None  # 대상 삭제 시 NULL 가능
    reason: str
    snapshot_context: Optional[str] = None


# -----------------------------
# 응답 스키마
# -----------------------------
class ReportResponse(BaseModel):
    """
    신고 상세 정보 응답
    """
    id: int
    reporter_id: int
    reporter_username: str
    reporter_account_id: str

    target_type: TargetType
    target_id: Optional[int] = None

    reported_user_id: Optional[int] = None
    reported_username: Optional[str] = None
    reported_account_id: Optional[str] = None

    reason: str
    snapshot_context: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
