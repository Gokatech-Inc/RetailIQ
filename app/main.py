from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import auth, products, forecasts, inventory

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="RetailIQ", description="AI-Powered Retail Demand Intelligence Platform", version="1.0.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(forecasts.router)
app.include_router(inventory.router)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "RetailIQ"}
