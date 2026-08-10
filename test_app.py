"""
Basic integration tests for BehaviourAI application.
Run with: python test_app.py
"""

import sys
import json
import tempfile
from pathlib import Path


def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        import app as app_module
        import config as config_module

        assert hasattr(app_module, "BehaviourAnalyticsApp")
        assert hasattr(config_module, "FEATURES")
        assert hasattr(config_module, "SEGMENT_MAP")

        print("[PASS] Imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False


def test_config():
    """Test configuration values."""
    print("\nTesting configuration...")
    try:
        from config import FEATURES, SEGMENT_MAP

        assert len(FEATURES) == 5
        assert len(SEGMENT_MAP) == 3
        print(
            f"[PASS] Config valid: {len(FEATURES)} features, "
            f"{len(SEGMENT_MAP)} segments"
        )
        return True
    except Exception as e:
        print(f"[FAIL] Config validation failed: {e}")
        return False


def test_data_generation():
    """Test data generation."""
    print("\nTesting data generation...")
    try:
        from data.generate_data import generate_sample_data

        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "test.csv"
            df = generate_sample_data(test_path, n=50)
            assert len(df) == 50
            assert all(
                col in df.columns for col in ["clicks", "time_spent", "purchase_count"]
            )
        print("[PASS] Data generation works")
        return True
    except Exception as e:
        print(f"[FAIL] Data generation failed: {e}")
        return False


def test_app_initialization():
    """Test that app can be initialized."""
    print("\nTesting app initialization...")
    try:
        from app import BehaviourAnalyticsApp

        app_wrapper = BehaviourAnalyticsApp()
        assert hasattr(app_wrapper, "app")
        assert hasattr(app_wrapper, "df")
        print("[PASS] App initialization successful")
        return True
    except Exception as e:
        print(f"[FAIL] App initialization failed: {e}")
        return False


def _seed_database_if_empty() -> None:
    """Populate the SQLite database with sample data on first run."""
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


def test_api_endpoints():
    """Test API endpoints by starting the server."""
    print("\nTesting API endpoints...")
    try:
        _seed_database_if_empty()

        from app import app
        from config import API_KEY

        client = app.test_client()
        client.environ_base["HTTP_X_API_KEY"] = API_KEY

        # Test health endpoint
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "healthy"
        print("  [PASS] Health endpoint works")

        # Test info endpoint
        resp = client.get("/api/info")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "features" in data
        print("  [PASS] Info endpoint works")

        # Test stats endpoint
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "total_users" in data
        print(f"  [PASS] Stats endpoint works: {data['total_users']} users")

        # Test trends endpoint
        resp = client.get("/api/trends")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        print(f"  [PASS] Trends endpoint works: {len(data)} months")

        # Test cluster endpoint
        resp = client.get("/api/cluster")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "x" in data[0] and "y" in data[0] and "cluster" in data[0]
        print(f"  [PASS] Cluster endpoint works: {len(data)} points")

        # Test predict endpoint
        payload = {
            "clicks": 45,
            "time_spent": 25,
            "purchase_count": 5,
            "page_views": 30,
            "cart_additions": 7,
        }
        resp = client.post("/api/predict", json=payload)
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "segment" in data
        assert "confidence" in data
        assert "recommendations" in data
        print(
            f"  [PASS] Predict endpoint works: {data['segment']} "
            f"({data['confidence']}%)"
        )

        # Test train endpoint
        resp = client.post("/api/train")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "success"
        assert "accuracy" in data
        print(f"  [PASS] Train endpoint works: accuracy {data['accuracy']}%")

        return True
    except Exception as e:
        print(f"[FAIL] API tests failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("BehaviourAI - Integration Tests")
    print("=" * 60)

    results = [
        test_imports(),
        test_config(),
        test_data_generation(),
        test_app_initialization(),
        test_api_endpoints(),
    ]

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} test groups passed")
    print("=" * 60)

    if all(results):
        print("\n[SUCCESS] All tests passed! Application is ready to run.")
        print("\nTo start the application:")
        print("  python app.py")
        print("\nThen visit: http://localhost:5000/dashboard")
        return 0
    else:
        print("\n[FAIL] Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
