import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.product import Product, SalesRecord, ForecastResult
from app.core.config import settings


async def optimize_inventory(product_id: str, db: AsyncSession) -> dict:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise ValueError(f"Product {product_id} not found")

    sales_result = await db.execute(
        select(SalesRecord).where(SalesRecord.product_id == product_id).order_by(SalesRecord.sale_date)
    )
    sales = sales_result.scalars().all()

    if not sales:
        return {"error": "No sales history to compute optimization metrics"}

    daily_demands = {}
    for s in sales:
        d = s.sale_date.date()
        daily_demands[d] = daily_demands.get(d, 0) + s.quantity_sold

    demands = list(daily_demands.values())
    avg_daily_demand = sum(demands) / len(demands)
    std_daily_demand = math.sqrt(sum((d - avg_daily_demand) ** 2 for d in demands) / len(demands))

    annual_demand = avg_daily_demand * 365
    eoq = math.sqrt(2 * annual_demand * product.ordering_cost / (product.unit_cost * product.holding_cost_pct)) if annual_demand > 0 else 0

    z_score = 1.645
    safety_stock = z_score * std_daily_demand * math.sqrt(product.lead_time_days)
    reorder_point = avg_daily_demand * product.lead_time_days + safety_stock
    days_of_supply = product.current_stock / avg_daily_demand if avg_daily_demand > 0 else 999
    needs_reorder = product.current_stock <= reorder_point

    product.reorder_point = round(reorder_point)
    await db.commit()

    return {
        "product_id": product_id,
        "sku": product.sku,
        "current_stock": product.current_stock,
        "avg_daily_demand": round(avg_daily_demand, 2),
        "std_daily_demand": round(std_daily_demand, 2),
        "eoq": round(eoq),
        "safety_stock": round(safety_stock),
        "reorder_point": round(reorder_point),
        "days_of_supply": round(days_of_supply, 1),
        "needs_reorder": needs_reorder,
        "recommended_order_qty": round(eoq) if needs_reorder else 0,
        "service_level": settings.REORDER_SERVICE_LEVEL,
    }
