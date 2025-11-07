from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.database import Base


class Follow(Base):
    __tablename__ = "follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 중복 팔로우 방지
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follower_following"),
    )

    # 관계 설정 (User 모델과 연결)
    follower_user = relationship(
        "User",
        foreign_keys=[follower_id],
        back_populates="followings",
    )
    following_user = relationship(
        "User",
        foreign_keys=[following_id],
        back_populates="followers",
    )

    def __repr__(self):
        return f"<Follow(follower_id={self.follower_id}, following_id={self.following_id})>"
