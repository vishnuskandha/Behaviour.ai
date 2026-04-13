import pandas as pd
import numpy as np

def generate_sample_data(path="data/behaviour_data.csv", n=500):
    np.random.seed(42)

    segments = np.random.choice([0, 1, 2], size=n, p=[0.4, 0.4, 0.2])

    data = {
        "user_id": [f"U{str(i).zfill(4)}" for i in range(1, n + 1)],
        "clicks": np.where(segments == 0, np.random.randint(1, 20, n),
                  np.where(segments == 1, np.random.randint(20, 60, n),
                           np.random.randint(60, 120, n))),
        "time_spent": np.where(segments == 0, np.random.uniform(1, 10, n),
                      np.where(segments == 1, np.random.uniform(10, 30, n),
                               np.random.uniform(30, 60, n))).round(1),
        "purchase_count": np.where(segments == 0, np.random.randint(0, 2, n),
                          np.where(segments == 1, np.random.randint(2, 8, n),
                                   np.random.randint(8, 20, n))),
        "page_views": np.where(segments == 0, np.random.randint(1, 15, n),
                     np.where(segments == 1, np.random.randint(15, 50, n),
                              np.random.randint(50, 100, n))),
        "cart_additions": np.where(segments == 0, np.random.randint(0, 3, n),
                          np.where(segments == 1, np.random.randint(3, 10, n),
                                   np.random.randint(10, 25, n))),
        "customer_segment": segments,
        "month": np.random.choice(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], n)
    }

    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    print(f"[DataGen] Generated {n} records -> {path}")
    return df

if __name__ == "__main__":
    generate_sample_data()
