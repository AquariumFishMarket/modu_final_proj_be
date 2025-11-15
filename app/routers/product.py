# app/routers/product.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_like import ProductLike
from app.schemas.product import ProductCreate, ProductUpdate, ProductDetailResponse
from app.core.security import get_current_user
from app.utils.s3_bucket import upload_image_to_s3

router = APIRouter(prefix="/api/products", tags=["Product"])


# -----------------------------
# 상품 등록
# -----------------------------
@router.post("", response_model=ProductDetailResponse)
async def create_product(
    product_in: ProductCreate = Depends(ProductCreate.as_form),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    판매할 상품 등록
    상품 이미지는 최소 1장 ~ 최대 5장 업로드 가능
    """
    
    # if not product_in.images or len(product_in.images) < 1:
    #     raise HTTPException(status_code=400, detail="최소 1장의 이미지를 업로드해야 합니다.")
    if product_in.images and len(product_in.images) > 5:
        raise HTTPException(status_code=400, detail="최대 5장까지 업로드 가능합니다.")

    # 상품 생성
    product = Product(
        seller_id=current_user.id,
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        product_url=product_in.product_url,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # 이미지 업로드 및 DB 저장
    image_urls = []
    if product_in.images:
        for image_file in product_in.images:
            url = upload_image_to_s3(image_file, folder="products")
            product_image = ProductImage(product_id=product.id, image_url=url)
            db.add(product_image)
            image_urls.append(url)
        db.commit()
        db.refresh(product)

    return ProductDetailResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        product_url=product.product_url,
        image_urls=image_urls,
        seller_id=current_user.id,
        seller_account_id=current_user.account_id,
        seller_username=current_user.username,
        seller_image_url=current_user.profile_image_url or "",
        like_count=product.like_count,
        view_count=product.view_count,
        created_at=product.created_at,
        updated_at=product.updated_at,
        is_blurred=product.is_blurred,
        is_deleted=product.is_deleted,
        report_count=product.report_count,
    )


# -----------------------------
# 상품 상세 조회
# -----------------------------
@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    """
    상품 정보 상세 조회
    api 호출 시 조회수 1 증가
    """
    
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    image_urls = [img.image_url for img in product.images]

    # 조회수 증가
    product.view_count += 1
    db.commit()
    db.refresh(product)

    seller = product.seller

    return ProductDetailResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        product_url=product.product_url,
        image_urls=image_urls,
        seller_id=seller.id,
        seller_account_id=seller.account_id,
        seller_username=seller.username,
        seller_image_url=seller.profile_image_url or "",
        like_count=product.like_count,
        view_count=product.view_count,
        created_at=product.created_at,
        updated_at=product.updated_at,
        is_blurred=product.is_blurred,
        is_deleted=product.is_deleted,
        report_count=product.report_count,
    )


# -----------------------------
# 상품 수정
# -----------------------------
@router.put("/{product_id}", response_model=ProductDetailResponse)
async def update_product(
    product_id: int,
    product_in: ProductUpdate = Depends(ProductUpdate.as_form),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    상품 정보 수정
    본인이 등록한 상품만 수정 가능
    name, description, price, product_url, images 필드 수정 가능 (부분 수정 허용)
    """
    
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인의 상품만 수정 가능합니다.")

    # 필드 업데이트
    if product_in.name:
        product.name = product_in.name
    if product_in.description is not None:
        product.description = product_in.description
    if product_in.price is not None:
        product.price = product_in.price
    if product_in.product_url is not None:
        product.product_url = product_in.product_url

    # 이미지 수정: 기존 이미지 삭제 후 새로 업로드
    if product_in.images is not None:
        # 기존 이미지 삭제
        for img in product.images:
            db.delete(img)
        db.commit()
        # 새 이미지 업로드
        new_image_urls = []
        for image_file in product_in.images:
            url = upload_image_to_s3(image_file, folder="products")
            product_image = ProductImage(product_id=product.id, image_url=url)
            db.add(product_image)
            new_image_urls.append(url)
        db.commit()

    db.refresh(product)
    image_urls = [img.image_url for img in product.images]

    seller = product.seller
    return ProductDetailResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        product_url=product.product_url,
        image_urls=image_urls,
        seller_id=seller.id,
        seller_account_id=seller.account_id,
        seller_username=seller.username,
        seller_image_url=seller.profile_image_url or "",
        like_count=product.like_count,
        view_count=product.view_count,
        created_at=product.created_at,
        updated_at=product.updated_at,
        is_blurred=product.is_blurred,
        is_deleted=product.is_deleted,
        report_count=product.report_count,
    )


# -----------------------------
# 상품 삭제
# -----------------------------
@router.delete("/{product_id}", response_model=dict)
def delete_product(
    product_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    상품 삭제
    soft delete 처리 (is_deleted 필드 True로 변경)
    본인이 등록한 상품만 삭제 가능
    """
    
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인의 상품만 삭제 가능합니다.")

    product.is_deleted = True
    db.commit()
    return {"detail": "상품이 삭제되었습니다."}


# -----------------------------
# 상품 좋아요 등록
# -----------------------------
@router.post("/{product_id}/likes", status_code=status.HTTP_201_CREATED)
def like_product(
    product_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    상품 좋아요 등록
    로그인한 사용자가 이미 좋아요한 상품은 중복 좋아요 불가
    """
    
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # 이미 좋아요했는지 확인
    existing_like = db.query(ProductLike).filter(
        ProductLike.user_id == current_user.id,
        ProductLike.product_id == product_id
    ).first()
    if existing_like:
        raise HTTPException(status_code=400, detail="이미 좋아요한 상품입니다.")

    like = ProductLike(user_id=current_user.id, product_id=product_id)
    db.add(like)
    product.like_count += 1
    db.commit()
    return {"detail": "좋아요가 등록되었습니다."}


# -----------------------------
# 상품 좋아요 취소
# -----------------------------
@router.delete("/{product_id}/likes", response_model=dict)
def unlike_product(
    product_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    상품 좋아요 취소
    로그인한 사용자가 좋아요하지 않은 상품은 취소 불가
    """
    
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # 좋아요 여부 확인
    like = db.query(ProductLike).filter(
        ProductLike.user_id == current_user.id,
        ProductLike.product_id == product_id
    ).first()
    if not like:
        raise HTTPException(status_code=400, detail="좋아요하지 않은 상품입니다.")

    db.delete(like)
    if product.like_count > 0:
        product.like_count -= 1
    db.commit()
    return {"detail": "좋아요가 취소되었습니다."}
