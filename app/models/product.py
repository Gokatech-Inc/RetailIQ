from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid, enum
from datetime import datetime
from app.database import Base

class ProductCategory(str, enum.Enum):
    GROCERY = "GROCERY"
    ELECTRONICS = "ELECTRONICS"
    APPAREL = "APPAREL"
    HOME = "HOME"
    BEAUTY = "BEAUTY"
    SPORTS = "SPORTS"

class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(SAEnum(ProductCategory), nullable=False)
    unit_price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    current_stock = Column(Integer, default=0)
    reorder_point = Column(Integer, default=0)
    lead_time_days = Column(Integer, default=7)
    ordering_cost = Column(Float, default=50.0)
    holding_cost_pct = Column(Float, default=0.25)
    created_at = Column(DateTime, default=datetime.utcnow)

class SalesRecord(Base):
    __tablename__ = "sales_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    store_id = Column(String, nullable=False, index=True)
    quantity_sold = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    sale_date = Column(DateTime, nullable=False, index=True)
    promotion_active = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ForecastResult(Base):
    __tablename__ = "forecast_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    forecast_date = Column(DateTime, nullable=False)
    predicted_demand = Column(Float, nullable=False)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    model_used = Column(String)
    mae = Column(Float)
    mape = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
