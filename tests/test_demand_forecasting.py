import pytest
import pandas as pd
import numpy as np
from app.services.demand_forecasting_service import _create_lag_features, _xgboost_forecast

def test_create_lag_features_adds_columns():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=30), "quantity": np.random.randint(10, 50, 30)})
    result = _create_lag_features(df.copy())
    assert "lag_1" in result.columns
    assert "lag_7" in result.columns
    assert "rolling_7_mean" in result.columns
    assert "day_of_week" in result.columns

def test_xgboost_forecast_returns_nonnegative():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=60), "quantity": np.random.randint(10, 100, 60).astype(float)})
    preds = _xgboost_forecast(df, horizon=14)
    assert len(preds) == 14
    assert all(p >= 0 for p in preds)

def test_xgboost_forecast_insufficient_data_fallback():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=5), "quantity": [10.0, 12.0, 11.0, 13.0, 10.0]})
    preds = _xgboost_forecast(df, horizon=7)
    assert len(preds) == 7
