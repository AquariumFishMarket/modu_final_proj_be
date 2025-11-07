# app/models/product_like.py
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


class ProductLike(Base):
    __tablename__ = "product_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # --- 관계 설정 ---
    user = relationship("User", back_populates="product_likes")
    product = relationship("Product", back_populates="likes")

    # --- 한 유저가 같은 상품에 중복 좋아요 방지 ---
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_user_product_like"),)

    def __repr__(self):
        return f"<ProductLike(user_id={self.user_id}, product_id={self.product_id})>"
