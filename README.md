# BehaviourAI — Customer Behaviour Analytics Platform

[![CI](https://github.com/vishnuskandha/Behaviour.ai/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/vishnuskandha/Behaviour.ai/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![OpenAPI 3.0](https://img.shields.io/badge/OpenAPI-3.0.0-6BA539.svg)](docs/swagger.yaml)

BehaviourAI is a machine-learning-powered customer behaviour analytics platform. It classifies
customers into **Low / Medium / High value segments** from behavioural metrics (clicks, time spent,
purchase count, page views, cart additions) using a scikit-learn **Random Forest** model, exposes
the model through a **REST API** with API-key authentication, and renders everything in an
interactive dark-mode dashboard.

Built with **Flask 3** and **scikit-learn**, backed by **SQLAlchemy** persistence, and shipped with a
fully automated CI pipeline (lint, type-check, security scan, tests).

## Features

- **ML-powered segmentation** — Random Forest classifier (100 estimators) with `StandardScaler`
  preprocessing, wrapped in a single reusable `sklearn.Pipeline`.
- **Real-world data** — ships with 4,338 real customers derived from the
  [UCI Online Retail](https://archive.ics.uci.edu/ml/datasets/online+retail) dataset, plus a
  synthetic fallback (500 records) for offline development.
- **Versioned model registry** — every training run is persisted to `data/models/v{n}/`
  (pipeline + metadata) and tracked in a lightweight JSON registry
  (`data/models/registry.json`) with an active-version pointer.
- **K-Means clustering** — 3-cluster visualisation of the customer base for the dashboard.
- **REST API** — 8 endpoints (stats, trends, clusters, prediction, training, health, info,
  model-info) secured with an `X-API-Key` header.
- **Interactive dashboard** — `/dashboard`: overview KPIs, cluster scatter plot, monthly trends,
  live predictor, and a one-click "Train Model" action.
- **Portable storage** — SQLite out of the box; PostgreSQL and MySQL supported via `DB_TYPE`.
- **Production tooling** — Gunicorn + Nginx configs, structured logging, connection pooling,
  OpenAPI contract, and a 6-stage CI pipeline.

## Architecture

```
Browser (dashboard)                HTTP clients (curl, apps)
        │                                 │
        ▼                                 ▼
┌───────────────────────────────────────────────┐
│  Flask app (app.py)                            │
│  • X-API-Key auth (before_request hook)        │
│  • REST routes: /api/*, /dashboard, /          │
│  • request metrics + logging                   │
└──────┬──────────────────────┬──────────────────┘
       │                      │
       ▼                      ▼
┌──────────────┐      ┌────────────────────┐
│   ML layer   │      │   Persistence      │
│ ml/pipeline  │      │ data/database.py   │
│ ml/registry  │◄────►│ SQLAlchemy ORM     │
│ RandomForest │      │ SQLite / PG / MySQL│
│ + KMeans     │      └────────────────────┘
└──────┬───────┘
       │
       ▼
┌────────────────────┐
│ Model artifacts    │
│ data/models/       │
│ registry.json      │
└────────────────────┘
```

Served in production by **Gunicorn** (4 sync workers) on `127.0.0.1:5000`, fronted by **Nginx**
(see `nginx/nginx.conf` and [DEPLOYMENT.md](DEPLOYMENT.md)).

## Quick Start

### Windows

```bat
run.bat
```

The bootstrapper checks your Python version (3.11+ required), creates a local `.venv`, installs
dependencies (with change detection via `requirements.txt` hash), initializes the database, and
starts the server.

### Linux / macOS

```bash
bash scripts/run.sh
```

The script initializes the database (if needed) and starts the server with **Gunicorn**
(4 sync workers on `127.0.0.1:5000`).

### Manual

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows — or: source .venv/bin/activate  (Unix)
pip install -r requirements.txt
python scripts/init_db.py     # create + seed the database
python app.py                 # development server
```

Then open **http://localhost:5000/dashboard** (or **http://localhost:5000/** for the landing page).

> Tip: for hot-reload during development set `FLASK_DEBUG=true`. The default is `false` for safety.

## REST API

All `/api/*` endpoints except `/api/health` and `/api/info` require an API key:

```
X-API-Key: demo-secret-key
```

The key is configurable via the `API_KEY` environment variable — change it in any real deployment.

| Method | Path               | Auth     | Description                                           |
|--------|--------------------|----------|-------------------------------------------------------|
| GET    | `/api/health`      | public   | Health check (data/model load status)                 |
| GET    | `/api/info`        | public   | API capabilities, features, segments, endpoints       |
| GET    | `/api/stats`       | API key  | Aggregate statistics (totals, averages, segment mix)  |
| GET    | `/api/trends`      | API key  | Monthly behaviour trends                              |
| GET    | `/api/cluster`     | API key  | K-Means cluster coordinates (max 500 points)          |
| POST   | `/api/predict`     | API key  | Predict customer segment from behavioural metrics     |
| POST   | `/api/train`       | API key  | Train/retrain the model and register a new version    |
| GET    | `/api/model-info`  | API key  | Active model version, metrics, created-at              |

The full contract is available in [docs/swagger.yaml](docs/swagger.yaml).

### Predict a segment

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-secret-key" \
  -d '{"clicks":45,"time_spent":25,"purchase_count":5,"page_views":30,"cart_additions":7}'
```

```json
{
  "segment": "High Value",
  "confidence": 96.7,
  "recommendations": [
    "VIP membership offer",
    "Exclusive early access",
    "Premium customer support"
  ],
  "version": "v1"
}
```

Inputs are validated server-side: all five feature fields are required, must be numeric and
non-negative, and are capped at sane upper bounds (returns `400` on violation).

### Train / retrain the model

```bash
curl -X POST http://localhost:5000/api/train -H "X-API-Key: demo-secret-key"
```

```json
{
  "status": "success",
  "accuracy": 98.39,
  "precision_macro": 98.2,
  "recall_macro": 98.1,
  "f1_macro": 98.15,
  "message": "Model trained with 4338 records",
  "total_records": 4338,
  "train_size": 3470,
  "test_size": 868,
  "version": "v2"
}
```

Every training run is versioned: the pipeline is persisted to `data/models/`, metadata is written to
`data/models/registry.json`, and the `current` alias points to the newest model.

## Configuration

BehaviourAI is configured entirely through environment variables (see `config.py`).

| Variable              | Default            | Description                                            |
|-----------------------|--------------------|--------------------------------------------------------|
| `API_KEY`             | `demo-secret-key`  | API key required by protected endpoints                |
| `FLASK_DEBUG`         | `false`            | Development server debug mode (`true`/`1`/`yes`)       |
| `LOG_LEVEL`           | `INFO`             | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`     |
| `USE_REAL_DATA`       | `false`            | Seed the database from `real_behaviour_data.csv` (4,338 customers) |
| `DB_TYPE`             | `sqlite`           | `sqlite`, `postgresql`, or `mysql`                     |
| `DB_HOST`/`DB_PORT`/`DB_NAME` | —          | Database connection details (PostgreSQL/MySQL)         |
| `DB_USER`/`DB_PASSWORD`      | —          | Database credentials (PostgreSQL/MySQL)                |
| `DB_POOL_SIZE`        | `10`               | Connection pool size                                   |
| `DB_MAX_OVERFLOW`     | `20`               | Connection pool overflow allowance                     |
| `DB_POOL_RECYCLE`     | `3600`             | Connection recycle time (seconds)                      |
| `SQL_ECHO`            | `false`            | Log SQL statements (`true`/`1`)                        |
| `BEHAVIOURAI_URL`     | `http://localhost:5000/api` | Base URL for `scripts/demo.py`                 |

## Data

| File                         | Records | Description                                        |
|------------------------------|---------|----------------------------------------------------|
| `data/real_behaviour_data.csv` | 4,338 | Aggregated customer profiles derived from UCI Online Retail |
| `data/online_retail.csv`     | 541,909 | Raw UCI Online Retail transactions (source of the profiles) |
| `data/behaviour_data.csv`    | 500     | Synthetic fallback data for offline development    |

`scripts/preprocess_real_data.py` downloads the UCI dataset (or accepts any custom CSV), maps
columns to the BehaviourAI schema, generates segments, and validates data types:

```bash
python scripts/preprocess_real_data.py --n-users 5000
python scripts/preprocess_real_data.py --input path/to/your_data.csv
```

## Testing & Quality

```bash
pytest tests/ -v --cov=app --cov=ml     # unit/integration suite
python test_app.py                      # standalone end-to-end suite (5 groups)
```

The repository enforces a 5-stage quality gate in CI (`.github/workflows/ci.yml`):

| Stage           | Tool     | Command                                   |
|-----------------|----------|-------------------------------------------|
| Format          | black    | `black --check .`                         |
| Lint            | flake8   | `flake8 .` (config in `.flake8`, 88 cols) |
| Types           | mypy     | `mypy .` (config in `mypy.ini`)           |
| Security        | bandit   | `bandit -r app.py ml/ data/ -c .bandit`   |
| Tests           | pytest   | `pytest tests/ --cov=app --cov=ml`        |

Run the whole gate locally before pushing:

```bash
black . && flake8 . && mypy . && bandit -r app.py ml/ data/ -c .bandit && pytest tests/
```

## Project Structure

```
Behaviour.ai/
├── app.py                      # Flask application: routes, ML logic, auth
├── config.py                   # Configuration & constants (env-driven)
├── requirements.txt            # Pinned runtime + dev dependencies
├── gunicorn.conf.py            # Production WSGI server config
├── mypy.ini                    # mypy configuration
├── .flake8                     # flake8 configuration (black-compatible)
├── .bandit                     # bandit configuration
├── data/
│   ├── database.py             # SQLAlchemy ORM + DatabaseManager
│   ├── generate_data.py        # Synthetic data generator
│   ├── behaviour_data.csv      # Synthetic dataset (500 records)
│   ├── real_behaviour_data.csv # Real customer profiles (4,338 records)
│   └── online_retail.csv       # Raw UCI Online Retail transactions
├── ml/
│   ├── pipeline.py             # sklearn Pipeline (scaler + RandomForest)
│   └── registry.py             # Versioned model registry
├── scripts/
│   ├── init_db.py              # Database initialization & seeding
│   ├── preprocess_real_data.py # UCI/custom dataset preprocessing
│   ├── demo.py                 # API demo client (stdlib only)
│   └── run.sh                  # Unix bootstrap script
├── templates/                  # Jinja templates (landing + dashboard)
├── static/js/dashboard.js      # Dashboard front-end logic
├── tests/                      # pytest suite (fixtures, API, models, validation)
├── test_app.py                 # Standalone end-to-end test suite
├── nginx/nginx.conf            # Reverse-proxy configuration
├── docs/swagger.yaml           # OpenAPI 3.0 API contract
├── .github/workflows/ci.yml    # CI pipeline (lint/type/security/tests)
├── QUICKSTART.md               # Fast setup & daily commands
├── DEPLOYMENT.md               # Production deployment guide
├── CONTRIBUTING.md             # Contribution guidelines
└── LICENSE                     # MIT License
```

## Deployment

- **Windows**: `run.bat` (dev) — for production use a WSGI server such as Waitress.
- **Linux/macOS**: `bash scripts/run.sh` — initializes the database and starts **Gunicorn**:

  ```bash
  gunicorn -c gunicorn.conf.py app:app
  ```

- **Reverse proxy**: ship the included `nginx/nginx.conf` (adjust paths, then symlink into
  `/etc/nginx/sites-enabled`).

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full guide.

## Security Notes

- The default `API_KEY` (`demo-secret-key`) is **for local development only** — always set a strong
  key via the `API_KEY` environment variable in production.
- The dashboard embeds the demo key client-side for convenience; replace it with a server-side
  session/token mechanism for public deployments.
- The development server binds to `127.0.0.1` by default; reverse proxies and container deployments
  must bind deliberately (e.g. via Gunicorn config).

See [SECURITY.md](SECURITY.md) for the vulnerability disclosure process.

## Documentation

| Document                          | Purpose                                 |
|-----------------------------------|-----------------------------------------|
| `README.md`                       | This file — overview, API, configuration |
| [QUICKSTART.md](QUICKSTART.md)    | Fast setup, common commands, troubleshooting |
| [DEPLOYMENT.md](DEPLOYMENT.md)    | Production deployment (Gunicorn/Nginx)  |
| [docs/swagger.yaml](docs/swagger.yaml) | Machine-readable OpenAPI 3.0 contract |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development workflow & PR guidelines    |

## License

[MIT](LICENSE) — Copyright (c) 2024 BehaviourAI Contributors.
