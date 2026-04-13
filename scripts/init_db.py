#!/usr/bin/env python
"""
Database initialization script for BehaviourAI.

This script:
1. Runs Alembic migrations to create/update database schema
2. Seeds the database with data from CSV (real or synthetic)
3. Creates admin user (if extended with auth)
4. Optionally clears existing data (use with caution)

Usage:
    python scripts/init_db.py [--clear] [--seed]

Options:
    --clear     Clear existing data before seeding (WARNING: irreversible)
    --seed      Load data from CSV into database (default: True)
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATABASE_URL, USE_REAL_DATA, DATA_FILE, REAL_DATA_FILE
from data.database import DatabaseManager
import pandas as pd

def run_migrations():
    """Run Alembic migrations to bring database to latest schema."""
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("alembic.ini")
        # Ensure database URL is set correctly
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

        print("[DB] Running Alembic migrations...")
        command.upgrade(alembic_cfg, "head")
        print("[DB] [OK] Migrations applied successfully")
        return True
    except ImportError:
        print("[DB] Alembic not installed. Skipping migrations.")
        print("[DB] Install with: pip install alembic")
        return False
    except Exception as e:
        print(f"[DB ERROR] Migration failed: {e}")
        return False

def seed_database(db: DatabaseManager, data_path: Path, clear_first: bool = False):
    """Load data from CSV into database."""
    try:
        if not data_path.exists():
            print(f"[DB] Data file not found: {data_path}")
            print("[DB] Generating synthetic data...")
            from data.generate_data import generate_sample_data
            generate_sample_data(DATA_FILE)
            data_path = DATA_FILE

        print(f"[DB] Loading data from {data_path}...")
        df = pd.read_csv(data_path)
        print(f"[DB] Loaded {len(df)} records from CSV")

        if clear_first:
            print("[DB] Clearing existing data...")
            db.clear_table()

        print("[DB] Inserting data into database...")
        db.insert_sample_data(df)

        count = db.row_count()
        print(f"[DB] [OK] Database contains {count} records")
        return True

    except Exception as e:
        print(f"[DB ERROR] Failed to seed database: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Initialize and seed BehaviourAI database")
    parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')
    parser.add_argument('--no-seed', action='store_true', help='Skip data seeding (migrations only)')
    args = parser.parse_args()

    print("=" * 60)
    print("BehaviourAI - Database Initialization")
    print("=" * 60)

    # Step 1: Run migrations
    migration_success = run_migrations()

    # Step 2: Seed data (if requested)
    if not args.no_seed:
        # Determine which data file to use
        data_path = REAL_DATA_FILE if USE_REAL_DATA else DATA_FILE
        print(f"\n[DB] Data source: {'REAL' if USE_REAL_DATA else 'SYNTHETIC'}")
        print(f"[DB] Data file: {data_path}")

        db = DatabaseManager()
        seed_success = seed_database(db, data_path, clear_first=args.clear)

        if seed_success:
            print("\n[DB] Database initialization complete!")
            print(f"[DB] Total records: {db.row_count()}")
        else:
            print("\n[DB] Database initialization failed during seeding")
            return 1
    else:
        print("\n[DB] Skipping data seeding (--no-seed flag)")

    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
