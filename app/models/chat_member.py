from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class ChatMember(Base):
    __tablename__ = "chat_members"

    id = Column(Integer, primary_key=True, index=True)
    chatroom_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("chatroom_id", "user_id", name="uq_chatroom_user"),)

    # 관계
    chatroom = relationship("ChatRoom", back_populates="members")
    user = relationship("User", back_populates="chat_memberships")

    def __repr__(self):
        return f"<ChatMember(chatroom_id={self.chatroom_id}, user_id={self.user_id})>"
