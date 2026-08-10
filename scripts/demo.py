"""Demo script for the BehaviourAI REST API.

Assumes the app is already running locally (see QUICKSTART.md), then exercises
the /stats, /train, and /predict endpoints with the X-API-Key header.

Usage:
    python scripts/demo.py
"""

import json
import os
import urllib.error
import urllib.request
from typing import Optional

BASE_URL = os.getenv("BEHAVIOURAI_URL", "http://localhost:5000/api")
API_KEY = os.getenv("API_KEY", "demo-secret-key")


def request(method: str, path: str, payload: Optional[dict] = None) -> dict:
    """Perform a JSON request against the BehaviourAI API."""
    url = f"{BASE_URL}/{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method, headers={"X-API-Key": API_KEY}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    print(f"Fetching stats from {BASE_URL}/stats ...")
    print(request("GET", "stats"))

    print("Training model...")
    print(request("POST", "train"))

    payload = {
        "clicks": 100,
        "time_spent": 120,
        "purchase_count": 10,
        "page_views": 50,
        "cart_additions": 15,
    }
    print("Predicting segment for test user...")
    print(request("POST", "predict", payload))


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")
