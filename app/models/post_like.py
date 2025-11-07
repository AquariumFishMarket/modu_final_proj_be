# app/models/post_like.py
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # --- 관계 설정 ---
    user = relationship("User", back_populates="post_likes")
    post = relationship("Post", back_populates="likes")

    # --- 한 유저가 같은 게시글에 중복 좋아요 방지 ---
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_user_post_like"),)

    def __repr__(self):
        return f"<PostLike(user_id={self.user_id}, post_id={self.post_id})>"
