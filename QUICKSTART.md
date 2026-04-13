# BehaviourAI - Quick Start Guide

**Last Updated:** 2025-03-18
**Current Status:** Phase 1 & 2 Complete (Real Data + Database)
**Next:** Phase 3 - ML Pipeline Refactoring

---

## What Is This?

BehaviourAI is a Flask API that predicts customer value segments (Low/Medium/High) using machine learning on e-commerce behavior data.

**Current Stats:**
- 4,338 real customers (UCI Online Retail dataset)
- 98.39% prediction accuracy
- SQLite database with optimized queries
- 8 RESTful API endpoints

---

## 30-Second Startup

```bash
# 1. Start the app bootstrapper
run.bat

# 2. Open browser: http://localhost:5000/dashboard
```

---

## Project Structure (Key Files)

```
behaviour_analytics/
├── app.py                    # Main Flask app - routes, ML logic
├── config.py                # Configuration (DB, ML params)
├── data/
│   ├── real_behaviour_data.csv  # 4,338 real customers
│   ├── behaviour_ai.db          # SQLite database (auto-created)
│   ├── database.py              # DatabaseManager (SQLAlchemy)
│   └── generate_data.py         # Synthetic data generator (fallback)
├── scripts/
│   ├── preprocess_real_data.py  # Download & transform UCI dataset
│   └── init_db.py               # Initialize database
├── requirements.txt
└── README.md                    # Primary project documentation
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/info` | GET | API documentation |
| `/api/stats` | GET | Aggregate statistics (total users, averages, segment counts) |
| `/api/trends` | GET | Monthly trend data |
| `/api/cluster` | GET | K-Means clustering results (max 500 points) |
| `/api/predict` | POST | Predict customer segment |
| `/api/train` | POST | Retrain model |

**Example prediction:**
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"clicks":45,"time_spent":25,"purchase_count":5,"page_views":30,"cart_additions":7}'
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_REAL_DATA` | false | Use real UCI data instead of synthetic |
| `DB_TYPE` | sqlite | Database type: sqlite, postgresql, mysql |
| `LOG_LEVEL` | INFO | Logging: DEBUG, INFO, WARNING, ERROR |

---

## What's Done (Phases 1-2)

✅ **Phase 1: Real Data Integration**
- UCI Online Retail dataset integrated (4,338 customers)
- Preprocessing script automatically downloads and transforms raw transactions
- Real data loads with `USE_REAL_DATA=true`
- Model accuracy: 98.39%

✅ **Phase 2: Database Migration**
- SQLAlchemy ORM with `DatabaseManager` class
- SQLite database with proper schema and indexes
- Optimized SQL queries for statistics and trends
- Chunked inserts to handle large datasets
- All app code now uses database instead of CSV

---

## What's Next (Phase 3: ML Pipeline)

Next major updates:

1. **sklearn Pipeline** - Combine scaler + model into single artifact
2. **Model Versioning** - Save models to `data/models/v1/`, `v2/`, etc.
3. **Model Registry** - Lightweight JSON registry to track versions
4. **Enhanced Metrics** - Add precision, recall, F1, confusion matrix
5. **ML Tests** - Unit tests for pipeline and data quality

---

## Testing

```bash
# Run integration tests
python test_app.py

# Expected output: "5/5 test groups passed"

Tests include:
- Imports & configuration
- Data generation
- App initialization
- All 7 API endpoints
```

---

## Common Commands

```bash
# Development (with auto-reload)
python app.py

# Production (Gunicorn - coming Phase 4)
gunicorn -c gunicorn.conf.py app:app

# Database
python scripts/init_db.py          # Initialize/seed DB
rm data/behaviour_ai.db            # Delete DB (will be recreated)

# Data preprocessing
python scripts/preprocess_real_data.py --n-users 5000

# Environment
export USE_REAL_DATA=true         # Use real data (Linux/Mac)
set USE_REAL_DATA=true            # Use real data (Windows)
```

---

## Documentation

Use these files for day-to-day work:
- `README.md` - Project overview and API endpoints
- `QUICKSTART.md` - Fast setup and common commands
- `DEPLOYMENT.md` - Deployment instructions
- `docs/swagger.yaml` - API contract

---

## Troubleshooting

**Database errors:**
```bash
# Delete and recreate
rm data/behaviour_ai.db
python scripts/init_db.py
```

**Import errors:**
```bash
pip install -r requirements.txt
```

**Real data not loading:**
```bash
# Check file exists
ls data/real_behaviour_data.csv

# If missing, regenerate
python scripts/preprocess_real_data.py
```

**Tests fail:**
```bash
# Ensure real data is used
export USE_REAL_DATA=true  # Linux/Mac
set USE_REAL_DATA=true     # Windows
python test_app.py
```

---

## Seeking Help

1. Read `README.md` first
2. Follow setup steps in `QUICKSTART.md`
3. Check API details in `docs/swagger.yaml`
4. Run tests to validate local changes
