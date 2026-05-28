# RetailIQ — AI-Powered Retail Demand Intelligence Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/XGBoost-2.1-FF6600?style=flat-square" />
  <img src="https://img.shields.io/badge/Prophet-Forecasting-0A1931?style=flat-square" />
  <img src="https://img.shields.io/badge/Apache_Kafka-231F20?style=flat-square&logo=apachekafka&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-22C55E?style=flat-square" />
</p>

> **Enterprise Retail Demand Intelligence Platform** — SKU-level demand forecasting using an XGBoost + Prophet ensemble, inventory optimization (EOQ, safety stock, reorder point), RFM customer segmentation, pricing intelligence, and real-time sales event streaming via Apache Kafka.

---

## Overview

RetailIQ gives retail operations and merchandising teams AI-driven demand intelligence across every SKU, store, and customer segment. The platform ingests historical sales data, trains a two-model ensemble (XGBoost for feature-rich short-term signals + Prophet for seasonality and trend), generates 30/60/90-day forecasts, and automatically recommends optimal reorder quantities and safety stock levels. Real-time POS events stream through Kafka to update inventory positions and trigger automated reorder alerts.

Designed for **retail chains, e-commerce operators, and CPG brands** managing thousands of SKUs across multiple locations.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                       RetailIQ Platform                        │
│                                                                │
│  ┌──────────┐  ┌────────────┐  ┌───────────┐  ┌──────────┐   │
│  │ Products │  │  Forecasts │  │ Inventory │  │  Auth    │   │
│  │   API    │  │    API     │  │   API     │  │  API     │   │
│  └────┬─────┘  └─────┬──────┘  └─────┬─────┘  └──────────┘   │
│       │               │              │                         │
│  ┌────▼───────────────▼──────────────▼──────────────────┐     │
│  │                  Service Layer                        │     │
│  │  ┌──────────────────────────┐  ┌───────────────────┐ │     │
│  │  │  Demand Forecasting      │  │ Inventory         │ │     │
│  │  │  XGBoost + Prophet       │  │ Optimization      │ │     │
│  │  │  Ensemble                │  │ EOQ · Safety Stock│ │     │
│  │  └──────────────────────────┘  └───────────────────┘ │     │
│  └──────────────────────────────────────────────────────┘     │
│             │                    │                             │
│  ┌──────────▼────────┐  ┌────────▼──────────────────────┐    │
│  │  Apache Kafka     │  │  PostgreSQL 15  ·  Redis 7     │    │
│  │  Sales Events     │  │  products · sales · forecasts  │    │
│  └───────────────────┘  └────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

---

## Features

### 1. XGBoost + Prophet Demand Forecasting Ensemble
Two-model ensemble for robust demand forecasting at the SKU-store level. XGBoost captures feature-rich signals (promotions, holidays, price changes, lag features). Prophet handles seasonality decomposition (weekly, monthly, yearly trends). Final forecast is a weighted average based on recent validation MAE.

### 2. Inventory Optimization Engine
Automated reorder recommendations using proven inventory science formulas:

| Metric | Formula |
|--------|---------|
| **EOQ** | √(2 × Annual Demand × Ordering Cost / Holding Cost) |
| **Safety Stock** | Z-score × σ(demand) × √Lead Time |
| **Reorder Point** | Avg Daily Demand × Lead Time + Safety Stock |
| **Days of Supply** | Current Stock / Avg Daily Demand |

### 3. RFM Customer Segmentation
Segment customers into Champions, Loyal, At-Risk, Lost, and New based on Recency (days since last purchase), Frequency (purchase count), and Monetary (total spend). Scores are computed nightly and cached in Redis.

### 4. Real-Time Sales Event Streaming
POS transactions publish to a Kafka topic (`retail.sales.events`). A consumer updates inventory positions in real-time and triggers reorder alerts when stock falls below the reorder point.

### 5. Pricing Intelligence
Elasticity modeling estimates price sensitivity per SKU. Markdown optimization surfaces SKUs with excess aging inventory and recommends discount levels that maximize revenue recovery while clearing stock.

### 6. Forecast Accuracy Reporting
Track MAE, MAPE, and RMSE per SKU over rolling 30-day windows. Identify SKUs with degrading forecast accuracy for model retraining.

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | Public | Register user |
| POST | `/api/v1/auth/login` | Public | Login, receive JWT |
| POST | `/api/v1/products` | Manager/Admin | Create SKU |
| GET | `/api/v1/products` | Required | List products with filters |
| POST | `/api/v1/products/{id}/sales` | Required | Record a sales event |
| POST | `/api/v1/forecasts/{product_id}` | Required | Run demand forecast (30/60/90 days) |
| GET | `/api/v1/forecasts/{product_id}` | Required | Get latest forecast |
| GET | `/api/v1/forecasts/{product_id}/accuracy` | Required | Forecast accuracy metrics |
| POST | `/api/v1/inventory/optimize/{product_id}` | Required | Run EOQ + reorder optimization |
| GET | `/api/v1/inventory/alerts` | Required | Get low-stock / reorder alerts |
| GET | `/health` | Public | Health check |

---

## Getting Started

```bash
git clone https://github.com/Gokatech-Inc/RetailIQ.git
cd RetailIQ

cp .env.example .env
docker-compose up -d

# API:  http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Local Development
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
docker-compose up -d db redis kafka zookeeper
uvicorn app.main:app --reload
```

### Running Tests
```bash
pytest tests/ -v
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `SECRET_KEY` | (required) | JWT signing secret |
| `REDIS_URL` | `redis://localhost:6379` | Cache connection |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker |
| `FORECAST_HORIZON_DAYS` | `90` | Default forecast horizon |
| `REORDER_SERVICE_LEVEL` | `0.95` | Target service level (Z = 1.645) |

---

## License

MIT License — **Gokatech Inc** · Retail Technology
