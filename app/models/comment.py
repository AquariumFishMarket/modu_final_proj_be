# app/models/comment.py
from sqlalchemy import (
    Column,
    Integer,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)

    content = Column(Text, nullable=False)

    # 신고 / 블러 / 삭제 플래그
    report_count = Column(Integer, default=0, nullable=False)
    is_blurred = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 설정
    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")

    # 자기참조: 부모/자식 관계
    parent_comment = relationship(
        "Comment",
        remote_side=[id],
        back_populates="child_comments",
    )
    child_comments = relationship(
        "Comment",
        back_populates="parent_comment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # 신고 관계
    # reports = relationship("Report", back_populates="comment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id}, user_id={self.user_id})>"
