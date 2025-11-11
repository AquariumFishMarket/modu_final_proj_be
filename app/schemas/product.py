# app/schemas/product.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# -----------------------------
# 공통 스키마
# -----------------------------
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    product_url = Optional[str] = None
    image_urls: Optional[List[str]] = None  # 이미지 최소 1~최대 5장


# -----------------------------
# 요청 스키마
# -----------------------------
class ProductCreate(ProductBase):
    """
    POST /api/products
    상품 등록
    """
    pass


class ProductUpdate(BaseModel):
    """
    PUT /api/products/{product_id}
    상품 수정 (부분 수정 허용)
    """
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    product_url: Optional[str] = None
    image_urls: Optional[List[str]] = None


# -----------------------------
# 응답 스키마
# -----------------------------
class ProductDetailResponse(BaseModel):
    """
    상품 상세 조회 응답
    """
    id: int
    name: str
    description: Optional[str]
    price: float
    product_url: Optional[str]
    image_urls: Optional[List[str]]
    seller_id: int
    seller_account_id: str
    seller_username: str
    seller_image_url: str
    like_count: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    is_blurred: bool
    is_deleted: bool
    report_count: int

    class Config:
        orm_mode = True


class ProductListItem(BaseModel):
    """
    상품 목록 조회용 (판매중인 상품 리스트)
    """
    id: int
    name: str
    price: float
    image_urls: Optional[List[str]]
    seller_id: int
    seller_username: str
    like_count: int

    class Config:
        orm_mode = True
