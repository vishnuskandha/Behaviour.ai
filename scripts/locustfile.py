from locust import HttpUser, task, between
import random

class BehaviourAPIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def check_health(self):
        self.client.get("/api/health")

    @task(2)
    def check_stats(self):
        self.client.get("/api/stats")

    @task(5)
    def predict_segment(self):
        payload = {
            "clicks": random.randint(10, 500),
            "time_spent": random.randint(5, 300),
            "purchase_count": random.randint(0, 50),
            "page_views": random.randint(10, 200),
            "cart_additions": random.randint(0, 30)
        }
        self.client.post("/api/predict", json=payload)
