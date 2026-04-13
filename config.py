"""
Application configuration and constants.
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "behaviour_data.csv"  # Synthetic data (fallback)
REAL_DATA_FILE = DATA_DIR / "real_behaviour_data.csv"  # Real-world data
MODEL_DIR = DATA_DIR / "models"
MODEL_FILE = MODEL_DIR / "random_forest_model.pkl"
SCALER_FILE = MODEL_DIR / "standard_scaler.pkl"

# Ensure directories exist
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ML Configuration
FEATURES = ["clicks", "time_spent", "purchase_count", "page_views", "cart_additions"]
TARGET = "customer_segment"
N_ESTIMATORS = 100
TEST_SIZE = 0.2
RANDOM_STATE = 42

# KMeans Configuration
KMEANS_N_CLUSTERS = 3
KMEANS_N_INIT = 10

# Segment mapping
SEGMENT_MAP = {
    0: "Low Value",
    1: "Medium Value",
    2: "High Value"
}

# Recommendations per segment
RECOMMENDATIONS = {
    0: [
        "Send discount coupons",
        "Show budget-friendly products",
        "Re-engagement email campaign"
    ],
    1: [
        "Upsell premium features",
        "Loyalty rewards program",
        "Personalized product recommendations"
    ],
    2: [
        "VIP membership offer",
        "Exclusive early access",
        "Premium customer support"
    ]
}

# Clustering features (subset for performance)
CLUSTER_FEATURES = ["clicks", "time_spent", "purchase_count"]

# API response limits
MAX_CLUSTER_SAMPLE = 500  # Max points returned from clustering

# API Authentication (Optional Stretch Goal)
API_KEY = os.getenv("API_KEY", "demo-secret-key")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Data source configuration
USE_REAL_DATA = os.getenv("USE_REAL_DATA", "false").lower() in ("true", "1", "yes")

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # 'sqlite', 'postgresql', 'mysql'
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "behaviour_ai")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Build DATABASE_URL
if DB_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'behaviour_ai.db'}"
elif DB_TYPE == "postgresql":
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
elif DB_TYPE == "mysql":
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    raise ValueError(f"Unsupported DB_TYPE: {DB_TYPE}")

# Connection pool settings (relevant for PostgreSQL/MySQL)
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 10))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 20))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", 3600))
