import pytest
import math
from unittest.mock import AsyncMock, MagicMock, patch

def test_eoq_formula():
    annual_demand = 1000
    ordering_cost = 50
    unit_cost = 10
    holding_cost_pct = 0.25
    eoq = math.sqrt(2 * annual_demand * ordering_cost / (unit_cost * holding_cost_pct))
    assert abs(eoq - 200) < 1

def test_safety_stock_formula():
    z_score = 1.645
    std_daily = 5.0
    lead_time = 7
    safety_stock = z_score * std_daily * math.sqrt(lead_time)
    assert safety_stock > 0
    assert abs(safety_stock - 21.77) < 0.1

def test_reorder_point_formula():
    avg_daily = 10
    lead_time = 7
    safety_stock = 22
    rop = avg_daily * lead_time + safety_stock
    assert rop == 92
