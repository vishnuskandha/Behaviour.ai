"""
Database layer for BehaviourAI using SQLAlchemy.

Provides:
- ORM model: CustomerBehaviour
- DatabaseManager: high-level data access methods
- Connection pooling, schema management
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import create_engine, text, Index
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy import Column, String, Integer, Float
from config import DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE

Base = declarative_base()


class CustomerBehaviour(Base):
    """
    SQLAlchemy ORM model for customer behaviour data.
    Maps to table: customer_behaviour
    """
    __tablename__ = 'customer_behaviour'

    user_id = Column(String(20), primary_key=True)
    clicks = Column(Integer, nullable=False)
    time_spent = Column(Float, nullable=False)
    purchase_count = Column(Integer, nullable=False)
    page_views = Column(Integer, nullable=False)
    cart_additions = Column(Integer, nullable=False)
    customer_segment = Column(Integer, nullable=False)
    month = Column(String(3), nullable=False)

    # Indexes for query performance (created separately)
    __table_args__ = (
        Index('idx_customer_segment', 'customer_segment'),
        Index('idx_month', 'month'),
        Index('idx_segment_month', 'customer_segment', 'month'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert row to dictionary."""
        return {
            'user_id': self.user_id,
            'clicks': self.clicks,
            'time_spent': self.time_spent,
            'purchase_count': self.purchase_count,
            'page_views': self.page_views,
            'cart_additions': self.cart_additions,
            'customer_segment': self.customer_segment,
            'month': self.month
        }


class DatabaseManager:
    """
    Manages database connections and operations for BehaviourAI.

    Uses SQLAlchemy for ORM and connection pooling.
    Supports SQLite (file-based), PostgreSQL, MySQL via connection string.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize DatabaseManager.

        Args:
            database_url: SQLAlchemy connection URL. If None, uses config.DATABASE_URL.
        """
        self.database_url = database_url or DATABASE_URL
        self.engine = None
        self.SessionLocal = None
        self._connected = False

        self._connect()

    def _connect(self) -> None:
        """Establish database connection and create tables if needed."""
        try:
            # Configure connection pool
            self.engine = create_engine(
                self.database_url,
                pool_size=int(os.getenv("DB_POOL_SIZE", DB_POOL_SIZE)),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", DB_MAX_OVERFLOW)),
                pool_recycle=int(os.getenv("DB_POOL_RECYCLE", DB_POOL_RECYCLE)),
                echo=bool(os.getenv("SQL_ECHO", False))  # Set SQL_ECHO=1 for SQL logging
            )

            # Create session factory
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )

            # Create tables if they don't exist
            Base.metadata.create_all(bind=self.engine)

            self._connected = True
            print(f"[DB] Connected to database: {self.database_url}")

        except Exception as e:
            print(f"[DB ERROR] Failed to connect to database: {e}")
            raise

    def get_session(self):
        """Get a new database session. Use as context manager."""
        if not self._connected:
            raise RuntimeError("Database not connected")
        return self.SessionLocal()

    def load_all_data(self) -> pd.DataFrame:
        """
        Load entire customer_behaviour table into a pandas DataFrame.

        Used for ML training and clustering operations that need full dataset.

        Returns:
            DataFrame with all customer records
        """
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_table('customer_behaviour', conn)
            return df
        except Exception as e:
            print(f"[DB ERROR] Failed to load data: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """
        Compute aggregate statistics directly in database for efficiency.

        Returns:
            Dictionary with total_users, avg_clicks, avg_time_spent, avg_purchases, segments
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT
                        COUNT(*) as total_users,
                        AVG(clicks) as avg_clicks,
                        AVG(time_spent) as avg_time_spent,
                        AVG(purchase_count) as avg_purchases,
                        COUNT(*) FILTER (WHERE customer_segment = 0) as segment_0_count,
                        COUNT(*) FILTER (WHERE customer_segment = 1) as segment_1_count,
                        COUNT(*) FILTER (WHERE customer_segment = 2) as segment_2_count
                    FROM customer_behaviour
                """))
                row = result.fetchone()

                return {
                    "total_users": int(row[0]) if row[0] is not None else 0,
                    "avg_clicks": round(float(row[1]), 1) if row[1] is not None else 0.0,
                    "avg_time_spent": round(float(row[2]), 1) if row[2] is not None else 0.0,
                    "avg_purchases": round(float(row[3]), 1) if row[3] is not None else 0.0,
                    "segments": {
                        0: int(row[4]) if row[4] is not None else 0,
                        1: int(row[5]) if row[5] is not None else 0,
                        2: int(row[6]) if row[6] is not None else 0
                    }
                }
        except Exception as e:
            print(f"[DB ERROR] Failed to get statistics: {e}")
            raise

    def get_monthly_trends(self) -> List[Dict[str, Any]]:
        """
        Get monthly aggregations using database GROUP BY.

        Returns:
            List of dictionaries: month, avg_purchases, avg_clicks, avg_time
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT
                        month,
                        AVG(purchase_count) as avg_purchases,
                        AVG(clicks) as avg_clicks,
                        AVG(time_spent) as avg_time
                    FROM customer_behaviour
                    GROUP BY month
                    ORDER BY
                        CASE month
                            WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 WHEN 'Mar' THEN 3
                            WHEN 'Apr' THEN 4 WHEN 'May' THEN 5 WHEN 'Jun' THEN 6
                            WHEN 'Jul' THEN 7 WHEN 'Aug' THEN 8 WHEN 'Sep' THEN 9
                            WHEN 'Oct' THEN 10 WHEN 'Nov' THEN 11 WHEN 'Dec' THEN 12
                        END
                """))
                rows = result.fetchall()

                trends = []
                for row in rows:
                    trends.append({
                        "month": row[0],
                        "avg_purchases": round(float(row[1]), 2) if row[1] is not None else 0.0,
                        "avg_clicks": round(float(row[2]), 2) if row[2] is not None else 0.0,
                        "avg_time": round(float(row[3]), 2) if row[3] is not None else 0.0
                    })

                return trends
        except Exception as e:
            print(f"[DB ERROR] Failed to get trends: {e}")
            raise

    def insert_sample_data(self, df: pd.DataFrame) -> None:
        """
        Bulk insert DataFrame into customer_behaviour table.

        Args:
            df: DataFrame with columns matching CustomerBehaviour model
        """
        try:
            # Validate columns
            required_cols = {'user_id', 'clicks', 'time_spent', 'purchase_count',
                           'page_views', 'cart_additions', 'customer_segment', 'month'}
            if not required_cols.issubset(set(df.columns)):
                missing = required_cols - set(df.columns)
                raise ValueError(f"Missing required columns: {missing}")

            # Clean data types
            df_clean = df.copy()
            for col in ['clicks', 'purchase_count', 'page_views', 'cart_additions']:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(int)
            df_clean['time_spent'] = pd.to_numeric(df_clean['time_spent'], errors='coerce').fillna(0).astype(float)
            df_clean['customer_segment'] = pd.to_numeric(df_clean['customer_segment'], errors='coerce').astype(int)
            df_clean['month'] = df_clean['month'].astype(str).str.title()

            # Bulk insert using to_sql with chunking (SQLite has 999 variable limit)
            with self.engine.begin() as conn:
                # Clear existing data
                conn.execute(text("DELETE FROM customer_behaviour"))

                # Insert in chunks to avoid SQLite parameter limit
                chunk_size = 200  # Safe for SQLite (200 rows * 8 cols = 1600 params < 999)
                total_rows = len(df_clean)
                for i in range(0, total_rows, chunk_size):
                    chunk = df_clean.iloc[i:i+chunk_size]
                    chunk.to_sql('customer_behaviour', conn, if_exists='append', index=False, method='multi')
                    print(f"[DB] Inserted {min(i+chunk_size, total_rows)}/{total_rows} records", end='\r')

                print(f"\n[DB] Inserted {total_rows} records into customer_behaviour")

            print(f"[DB] Inserted {len(df_clean)} records into customer_behaviour")
        except Exception as e:
            print(f"[DB ERROR] Failed to insert sample data: {e}")
            raise

    def row_count(self) -> int:
        """Get total number of rows in customer_behaviour table."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM customer_behaviour"))
                return int(result.scalar())
        except Exception as e:
            print(f"[DB ERROR] Failed to count rows: {e}")
            raise

    def clear_table(self) -> None:
        """Delete all rows from customer_behaviour table. Use with caution!"""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("DELETE FROM customer_behaviour"))
            print("[DB] Table cleared")
        except Exception as e:
            print(f"[DB ERROR] Failed to clear table: {e}")
            raise
