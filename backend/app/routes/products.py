"""Product and product variant routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_active_user
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductUpdate,
    VariantCreate,
    VariantOut,
    VariantUpdate,
)
from app.services.product_service import (
    create_product,
    create_variant,
    delete_product,
    delete_variant,
    get_product,
    get_variant,
    list_products,
    list_variants,
    update_product,
    update_variant,
)

router = APIRouter(prefix="/api/products", tags=["Products"])


# ---------- Products ----------


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product_route(
    data: ProductCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Create a new product."""
    product = create_product(db, data)
    return ProductOut.model_validate(product)


@router.get("", response_model=list[ProductOut])
def list_products_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """List all products."""
    products = list_products(db, skip=skip, limit=limit, active_only=active_only)
    return [ProductOut.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductOut)
def get_product_route(
    product_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Retrieve a product by ID."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductOut.model_validate(product)


@router.put("/{product_id}", response_model=ProductOut)
@router.patch("/{product_id}", response_model=ProductOut)
def update_product_route(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Update a product."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    updated = update_product(db, product, data)
    return ProductOut.model_validate(updated)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_route(
    product_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Deactivate a product (soft-delete)."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    delete_product(db, product)


# ---------- Variants ----------


@router.post(
    "/{product_id}/variants",
    response_model=VariantOut,
    status_code=status.HTTP_201_CREATED,
)
def create_variant_route(
    product_id: int,
    data: VariantCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Create a variant under a product."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    try:
        variant = create_variant(db, product_id, data)
        return VariantOut.model_validate(variant)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Variant name or SKU conflict",
        )


@router.get("/{product_id}/variants", response_model=list[VariantOut])
def list_variants_route(
    product_id: int,
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """List variants for a product."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    variants = list_variants(db, product_id, active_only=active_only)
    return [VariantOut.model_validate(v) for v in variants]


@router.put("/{product_id}/variants/{variant_id}", response_model=VariantOut)
@router.patch("/{product_id}/variants/{variant_id}", response_model=VariantOut)
def update_variant_route(
    product_id: int,
    variant_id: int,
    data: VariantUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Update a product variant."""
    variant = get_variant(db, variant_id)
    if variant is None or variant.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    try:
        updated = update_variant(db, variant, data)
        return VariantOut.model_validate(updated)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Variant name or SKU conflict",
        )


@router.delete(
    "/{product_id}/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_variant_route(
    product_id: int,
    variant_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
):
    """Deactivate a product variant (soft-delete)."""
    variant = get_variant(db, variant_id)
    if variant is None or variant.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
    delete_variant(db, variant)
