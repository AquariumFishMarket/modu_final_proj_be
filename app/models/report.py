# app/models/report.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Enum,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TargetType(enum.Enum):
    post = "post"
    comment = "comment"
    product = "product"
    message = "message"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)

    # 신고자 정보
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reporter_username = Column(String(50), nullable=False)
    reporter_account_id = Column(String(50), nullable=False)

    # 신고 대상
    target_type = Column(Enum(TargetType), nullable=False)
    target_id = Column(Integer, nullable=True)  # 대상이 삭제되면 NULL 가능

    # 피신고자 정보
    reported_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reported_username = Column(String(50), nullable=True)
    reported_account_id = Column(String(50), nullable=True)

    # 신고 사유 및 원문
    reason = Column(Text, nullable=False)
    snapshot_context = Column(Text, nullable=True)

    # 상태 관리
    status = Column(String(20), default="pending", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 관계 설정
    reporter = relationship(
        "User",
        foreign_keys=[reporter_id],
        back_populates="reports_made",
    )
    reported_user = relationship(
        "User",
        foreign_keys=[reported_user_id],
        back_populates="reports_received",
    )

    def __repr__(self):
        return (
            f"<Report(id={self.id}, target_type='{self.target_type}', "
            f"target_id={self.target_id}, status='{self.status}')>"
        )
