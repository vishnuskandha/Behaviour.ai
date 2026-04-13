# BehaviourAI

[![Tests](https://github.com/yourusername/behaviour_analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/behaviour_analytics/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

BehaviourAI is a robust Customer Behaviour Analytics Platform using Flask and scikit-learn.

## Quick Start
```bash
run.bat
```
The launcher checks your Python version, creates a local `.venv`, installs dependencies, initializes the database, and then starts the app.

Navigate to `http://localhost:5000/dashboard`

## Endpoints
- `GET /api/health`: Health check
- `GET /api/info`: API documentation
- `GET /api/stats`: Aggregate demographics
- `GET /api/trends`: Monthly patterns
- `GET /api/cluster`: Customer segments
- `POST /api/predict`: Model prediction
- `POST /api/train`: Re-train model
- `GET /api/model-info`: Current model version
