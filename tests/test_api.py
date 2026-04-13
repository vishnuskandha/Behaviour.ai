import json

def test_health_endpoint(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['status'] == 'healthy'

def test_info_endpoint(client):
    resp = client.get('/api/info')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'features' in data

def test_stats_endpoint(client):
    resp = client.get('/api/stats')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert 'total_users' in data

def test_predict_endpoint(client):
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

def test_model_info_endpoint(client):
    resp = client.get('/api/model-info')
    assert resp.status_code in (200, 404)
