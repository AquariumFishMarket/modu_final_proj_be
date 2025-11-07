from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chatroom_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    content = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)

    report_count = Column(Integer, default=0, nullable=False)
    is_blurred = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 관계
    chatroom = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", back_populates="messages_sent")
    reads = relationship("MessageRead", back_populates="message", cascade="all, delete-orphan", passive_deletes=True)
    # reports = relationship("Report", back_populates="message", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Message(id={self.id}, chatroom_id={self.chatroom_id}, sender_id={self.sender_id})>"
