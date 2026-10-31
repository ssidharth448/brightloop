"""Product and product variant service — CRUD operations."""

from sqlalchemy.orm import Session

from app.models.product import Product, ProductVariant
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)


# ---------- Products ----------

def create_product(db: Session, data: ProductCreate) -> Product:
    dump = data.model_dump(exclude={"base_price", "active"}, exclude_unset=True)
    product = Product(**dump)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def list_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[Product]:
    q = db.query(Product)
    if active_only:
        q = q.filter(Product.is_active.is_(True))
    return q.order_by(Product.id).offset(skip).limit(limit).all()


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def update_product(
    db: Session, product: Product, data: ProductUpdate
) -> Product:
    update_data = data.model_dump(exclude={"base_price", "active"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    """Soft-delete by deactivating the product."""
    product.is_active = False
    db.commit()


# ---------- Variants ----------

def create_variant(
    db: Session, product_id: int, data: VariantCreate
) -> ProductVariant:
    dump = data.model_dump(exclude={"extra_price", "active"}, exclude_unset=True)
    variant = ProductVariant(product_id=product_id, **dump)
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant


def list_variants(
    db: Session,
    product_id: int,
    active_only: bool = False,
) -> list[ProductVariant]:
    q = db.query(ProductVariant).filter(ProductVariant.product_id == product_id)
    if active_only:
        q = q.filter(ProductVariant.is_active.is_(True))
    return q.order_by(ProductVariant.id).all()


def get_variant(db: Session, variant_id: int) -> ProductVariant | None:
    return db.get(ProductVariant, variant_id)


def update_variant(
    db: Session, variant: ProductVariant, data: VariantUpdate
) -> ProductVariant:
    update_data = data.model_dump(exclude={"extra_price", "active"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(variant, field, value)
    db.commit()
    db.refresh(variant)
    return variant


def delete_variant(db: Session, variant: ProductVariant) -> None:
    """Soft-delete by deactivating the variant."""
    variant.is_active = False
    db.commit()
