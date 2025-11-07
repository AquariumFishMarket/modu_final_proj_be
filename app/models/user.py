from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    # 기본 PK
    id = Column(Integer, primary_key=True, index=True)

    # 계정 관련
    account_id = Column(String(50), unique=True, nullable=False, index=True)  # 로그인용 고유 계정 ID
    username = Column(String(50), nullable=False)                            # 닉네임 (중복 허용)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # 프로필
    profile_image_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)

    # 상태
    is_active = Column(Boolean, default=True, nullable=False)

    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --- 관계 정의 (다른 모델 파일에서 대응되는 back_populates를 맞춰줘야 함) ---
    # 세션: User 1 -- N Session
    sessions = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # 게시글, 댓글, 상품 등
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan", passive_deletes=True)

    # 좋아요 (역참조)
    post_likes = relationship("PostLike", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    product_likes = relationship("ProductLike", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

    # 팔로우: follower/following (self-referential Follow 테이블)
    # Note: Follow 모델에서 foreign_keys를 설정해야 양방향이 잘 동작합니다.
    followers = relationship(
        "Follow",
        foreign_keys="[Follow.following_id]",
        back_populates="following_user",
        cascade="all, delete-orphan",
    )
    followings = relationship(
        "Follow",
        foreign_keys="[Follow.follower_id]",
        back_populates="follower_user",
        cascade="all, delete-orphan",
    )

    # 채팅 관련
    chat_memberships = relationship("ChatMember", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    messages_sent = relationship("Message", back_populates="sender", cascade="all, delete-orphan", passive_deletes=True)

    # 신고: 신고한 기록 / 피신고자 기록
    reports_made = relationship(
        "Report",
        foreign_keys="[Report.reporter_id]",
        back_populates="reporter",
        cascade="all, delete-orphan",
    )
    reports_received = relationship(
        "Report",
        foreign_keys="[Report.reported_user_id]",
        back_populates="reported_user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User(id={self.id}, account_id='{self.account_id}', username='{self.username}', email='{self.email}')>"
