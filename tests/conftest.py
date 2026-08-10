"""Shared pytest fixtures for BehaviourAI."""

import sys
from pathlib import Path

import pytest

# Ensure the repository root is importable regardless of how pytest is invoked
# (bare `pytest` vs `python -m pytest`).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_API_KEY = "demo-secret-key"


def _seed_database_if_empty() -> None:
    """Populate the SQLite database with sample data on first run."""
    from pathlib import Path

    import pandas as pd

    from config import DATA_FILE, REAL_DATA_FILE, USE_REAL_DATA
    from data.database import DatabaseManager
    from data.generate_data import generate_sample_data

    db = DatabaseManager()
    if db.row_count() > 0:
        return

    source = (
        Path(REAL_DATA_FILE)
        if USE_REAL_DATA and Path(REAL_DATA_FILE).exists()
        else Path(DATA_FILE)
    )
    if not source.exists():
        generate_sample_data(DATA_FILE, n=500)
        source = Path(DATA_FILE)

    db.insert_sample_data(pd.read_csv(source))


# Seed the database *before* importing the application: `app.application` is
# created at module import time and reads from the configured SQLite database
# on first use, so tests must not depend on local state left behind by run.bat.
_seed_database_if_empty()

from app import application, app as flask_app  # noqa: E402


@pytest.fixture
def app():
    yield flask_app


@pytest.fixture
def client(app):
    client = app.test_client()
    client.environ_base["HTTP_X_API_KEY"] = _API_KEY
    return client


@pytest.fixture
def manager():
    return application
