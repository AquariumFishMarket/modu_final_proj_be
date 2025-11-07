# app/models/hashtag.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Hashtag(Base):
    __tablename__ = "hashtags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    posts = relationship("PostHashtag", back_populates="hashtag", cascade="all, delete")

    def __repr__(self):
        return f"<Hashtag(id={self.id}, name='{self.name}')>"