"""
Basic integration tests for BehaviourAI application.
Run with: python test_app.py
"""
import sys
import json
import tempfile
import subprocess
import time
from pathlib import Path

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from app import BehaviourAnalyticsApp
        from config import FEATURES, SEGMENT_MAP
        print("[PASS] Imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_config():
    """Test configuration values."""
    print("\nTesting configuration...")
    try:
        from config import FEATURES, SEGMENT_MAP, DATA_FILE
        assert len(FEATURES) == 5
        assert len(SEGMENT_MAP) == 3
        print(f"[PASS] Config valid: {len(FEATURES)} features, {len(SEGMENT_MAP)} segments")
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
            assert all(col in df.columns for col in ['clicks', 'time_spent', 'purchase_count'])
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
        assert hasattr(app_wrapper, 'app')
        assert hasattr(app_wrapper, 'df')
        print("[PASS] App initialization successful")
        return True
    except Exception as e:
        print(f"[FAIL] App initialization failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints by starting the server."""
    print("\nTesting API endpoints...")
    try:
        from app import app
        client = app.test_client()

        # Test health endpoint
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'healthy'
        print("  [PASS] Health endpoint works")

        # Test info endpoint
        resp = client.get('/api/info')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'features' in data
        print("  [PASS] Info endpoint works")

        # Test stats endpoint
        resp = client.get('/api/stats')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'total_users' in data
        print(f"  [PASS] Stats endpoint works: {data['total_users']} users")

        # Test trends endpoint
        resp = client.get('/api/trends')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        print(f"  [PASS] Trends endpoint works: {len(data)} months")

        # Test cluster endpoint
        resp = client.get('/api/cluster')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) > 0
        assert 'x' in data[0] and 'y' in data[0] and 'cluster' in data[0]
        print(f"  [PASS] Cluster endpoint works: {len(data)} points")

        # Test predict endpoint
        payload = {
            "clicks": 45,
            "time_spent": 25,
            "purchase_count": 5,
            "page_views": 30,
            "cart_additions": 7
        }
        resp = client.post('/api/predict', json=payload)
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'segment' in data
        assert 'confidence' in data
        assert 'recommendations' in data
        print(f"  [PASS] Predict endpoint works: {data['segment']} ({data['confidence']}%)")

        # Test train endpoint
        resp = client.post('/api/train')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'success'
        assert 'accuracy' in data
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
        test_api_endpoints()
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
