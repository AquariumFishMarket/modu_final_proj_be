from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class PostImage(Base):
    __tablename__ = "post_images"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(Text, nullable=False)

    # --- 관계 정의 ---
    post = relationship("Post", back_populates="images")

    def __repr__(self):
        return f"<PostImage(id={self.id}, post_id={self.post_id})>"
