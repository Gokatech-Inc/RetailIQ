import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.product import Product, SalesRecord, ForecastResult
from app.core.config import settings


def _create_lag_features(df: pd.DataFrame, lags: List[int] = [1, 7, 14, 28]) -> pd.DataFrame:
    for lag in lags:
        df[f"lag_{lag}"] = df["quantity"].shift(lag)
    df["rolling_7_mean"] = df["quantity"].rolling(7, min_periods=1).mean()
    df["rolling_14_mean"] = df["quantity"].rolling(14, min_periods=1).mean()
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    return df.dropna()


def _xgboost_forecast(history_df: pd.DataFrame, horizon: int) -> np.ndarray:
    try:
        from xgboost import XGBRegressor
    except ImportError:
        return np.full(horizon, history_df["quantity"].mean())

    df = history_df.copy().sort_values("date")
    df = _create_lag_features(df)
    if len(df) < 10:
        return np.full(horizon, history_df["quantity"].mean())

    feature_cols = [c for c in df.columns if c not in ["date", "quantity"]]
    X, y = df[feature_cols].values, df["quantity"].values
    split = max(1, int(len(X) * 0.8))
    model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    model.fit(X[:split], y[:split])

    preds = []
    last_row = df.iloc[-1].copy()
    for _ in range(horizon):
        feat = np.array([[last_row[c] for c in feature_cols]])
        pred = float(model.predict(feat)[0])
        preds.append(max(0, pred))
        last_row["lag_1"] = pred
        last_row["rolling_7_mean"] = (last_row["rolling_7_mean"] * 6 + pred) / 7
    return np.array(preds)


def _prophet_forecast(history_df: pd.DataFrame, horizon: int) -> np.ndarray:
    try:
        from prophet import Prophet
    except ImportError:
        return np.full(horizon, history_df["quantity"].mean())

    df = history_df.rename(columns={"date": "ds", "quantity": "y"})[["ds", "y"]]
    if len(df) < 10:
        return np.full(horizon, df["y"].mean())

    model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False, interval_width=0.8)
    model.fit(df)
    future = model.make_future_dataframe(periods=horizon)
    forecast = model.predict(future)
    return forecast["yhat"].values[-horizon:].clip(min=0)


async def run_forecast(product_id: str, horizon: int, db: AsyncSession) -> List[ForecastResult]:
    result = await db.execute(select(Product).where(Product.id == product_id))
    if not result.scalar_one_or_none():
        raise ValueError(f"Product {product_id} not found")

    sales_result = await db.execute(
        select(SalesRecord).where(SalesRecord.product_id == product_id).order_by(SalesRecord.sale_date)
    )
    sales = sales_result.scalars().all()
    if not sales:
        raise ValueError("No historical sales data for this product")

    daily = {}
    for s in sales:
        d = s.sale_date.date()
        daily[d] = daily.get(d, 0) + s.quantity_sold

    start = min(daily.keys())
    end = max(daily.keys())
    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    quantities = [daily.get(d, 0) for d in dates]

    history_df = pd.DataFrame({"date": pd.to_datetime(dates), "quantity": quantities})

    xgb_preds = _xgboost_forecast(history_df, horizon)
    prophet_preds = _prophet_forecast(history_df, horizon)

    avg_demand = history_df["quantity"].mean()
    xgb_mae = float(np.mean(np.abs(xgb_preds[:len(quantities)] - np.array(quantities[-len(xgb_preds[:len(quantities)]):])))) if len(quantities) >= len(xgb_preds) else avg_demand
    prophet_mae = float(np.mean(np.abs(prophet_preds[:len(quantities)] - np.array(quantities[-len(prophet_preds[:len(quantities)]):])))) if len(quantities) >= len(prophet_preds) else avg_demand

    w_xgb = (1 / (xgb_mae + 1e-6)) / ((1 / (xgb_mae + 1e-6)) + (1 / (prophet_mae + 1e-6)))
    ensemble = w_xgb * xgb_preds + (1 - w_xgb) * prophet_preds

    forecast_start = datetime.combine(end + timedelta(days=1), datetime.min.time())
    records = []
    for i, pred in enumerate(ensemble):
        rec = ForecastResult(
            product_id=product_id,
            forecast_date=forecast_start + timedelta(days=i),
            predicted_demand=round(float(pred), 2),
            lower_bound=round(float(pred) * 0.85, 2),
            upper_bound=round(float(pred) * 1.15, 2),
            model_used="XGBoost+Prophet Ensemble",
            mae=round(min(xgb_mae, prophet_mae), 4),
            mape=round(min(xgb_mae, prophet_mae) / (avg_demand + 1e-6) * 100, 2),
        )
        db.add(rec)
        records.append(rec)

    await db.commit()
    return records
