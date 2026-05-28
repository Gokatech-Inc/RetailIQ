from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.product import Product
from app.services.inventory_optimization_service import optimize_inventory
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

@router.post("/optimize/{product_id}")
async def run_optimization(product_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        return await optimize_inventory(product_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Product))
    products = result.scalars().all()
    alerts = [
        {"product_id": str(p.id), "sku": p.sku, "name": p.name, "current_stock": p.current_stock, "reorder_point": p.reorder_point}
        for p in products if p.current_stock <= p.reorder_point
    ]
    return {"alerts": alerts, "count": len(alerts)}
