import json
import requests
import time

BASE_URL = "http://localhost:5000/api"

print("Fetching stats...")
try:
    r = requests.get(f"{BASE_URL}/stats")
    print(r.json())
except Exception as e:
    print(f"Error fetching stats: {e}")

print("Training model...")
try:
    r = requests.post(f"{BASE_URL}/train")
    print(r.json())
except Exception as e:
    print(f"Error training model: {e}")

print("Predicting segment for test user...")
payload = {
    "clicks": 100,
    "time_spent": 120,
    "purchase_count": 10,
    "page_views": 50,
    "cart_additions": 15
}
try:
    r = requests.post(f"{BASE_URL}/predict", json=payload)
    print(r.json())
except Exception as e:
    print(f"Error predicting segment: {e}")
