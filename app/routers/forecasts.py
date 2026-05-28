from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.product import ForecastResult
from app.services.demand_forecasting_service import run_forecast
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/forecasts", tags=["forecasts"])

@router.post("/{product_id}", status_code=201)
async def create_forecast(product_id: str, horizon: int = Query(90, le=365), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        records = await run_forecast(product_id, horizon, db)
        return {"product_id": product_id, "horizon_days": horizon, "records_generated": len(records)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{product_id}")
async def get_forecast(product_id: str, limit: int = Query(30, le=365), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(
        select(ForecastResult).where(ForecastResult.product_id == product_id)
        .order_by(ForecastResult.forecast_date).limit(limit)
    )
    records = result.scalars().all()
    if not records:
        raise HTTPException(status_code=404, detail="No forecast found. Run POST first.")
    return records
