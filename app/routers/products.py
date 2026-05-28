from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.product import Product, ProductCategory, SalesRecord
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/products", tags=["products"])

class ProductCreate(BaseModel):
    sku: str
    name: str
    category: ProductCategory
    unit_price: float
    unit_cost: float
    current_stock: int = 0
    lead_time_days: int = 7
    ordering_cost: float = 50.0
    holding_cost_pct: float = 0.25

class SalesCreate(BaseModel):
    store_id: str
    quantity_sold: int
    unit_price: float
    sale_date: datetime
    promotion_active: bool = False

@router.post("", status_code=201)
async def create_product(req: ProductCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    product = Product(**req.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

@router.get("")
async def list_products(category: Optional[ProductCategory] = None, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    q = select(Product)
    if category:
        q = q.where(Product.category == category)
    return (await db.execute(q)).scalars().all()

@router.post("/{product_id}/sales", status_code=201)
async def record_sale(product_id: str, req: SalesCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.current_stock = max(0, product.current_stock - req.quantity_sold)
    sale = SalesRecord(product_id=product_id, **{**req.model_dump(), "promotion_active": int(req.promotion_active)})
    db.add(sale)
    await db.commit()
    return {"message": "Sale recorded", "remaining_stock": product.current_stock}
