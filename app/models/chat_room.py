from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_message_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 관계 설정
    members = relationship("ChatMember", back_populates="chatroom", cascade="all, delete-orphan", passive_deletes=True)
    messages = relationship("Message", back_populates="chatroom", cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self):
        return f"<ChatRoom(id={self.id}, created_at={self.created_at})>"
