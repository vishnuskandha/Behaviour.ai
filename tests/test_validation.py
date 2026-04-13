def test_predict_validation(client):
    payload = {
        "clicks": -1,  # Invalid
        "time_spent": 25,
        "purchase_count": 5,
        "page_views": 30,
        "cart_additions": 7
    }
    resp = client.post('/api/predict', json=payload)
    assert resp.status_code == 400
