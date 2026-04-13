#!/usr/bin/env python
"""
Preprocess real-world customer behavior data for BehaviourAI.

This script downloads and transforms a real dataset (e.g., UCI Online Retail)
into the BehaviourAI schema: clicks, time_spent, purchase_count, page_views,
cart_additions, customer_segment, month, user_id.

Dataset Options:
1. UCI Online Retail (Default) - E-commerce transactional data
   https://archive.ics.uci.edu/ml/datasets/online+retail
   Downloads automatically if not present

2. Custom dataset - Provide path to your own CSV with appropriate columns

Output: data/real_behaviour_data.csv
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import urllib.request
import zipfile
import io

# Project paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = DATA_DIR / "real_behaviour_data.csv"

# Expected schema for BehaviourAI
SCHEMA = {
    'user_id': 'string',
    'clicks': 'integer',
    'time_spent': 'float',
    'purchase_count': 'integer',
    'page_views': 'integer',
    'cart_additions': 'integer',
    'customer_segment': 'integer',  # 0=Low, 1=Medium, 2=High
    'month': 'string'  # Jan, Feb, etc.
}


def download_uci_online_retail() -> Path:
    """
    Download UCI Online Retail dataset if not already present.
    Returns: Path to the downloaded CSV file.
    """
    raw_data_path = DATA_DIR / "online_retail.csv"

    if not raw_data_path.exists():
        print("Downloading UCI Online Retail dataset...")
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"

        try:
            # Download Excel file
            response = urllib.request.urlopen(url)
            excel_data = response.read()

            # Read Excel into DataFrame
            df_excel = pd.read_excel(io.BytesIO(excel_data))

            # Save as CSV for future use
            df_excel.to_csv(raw_data_path, index=False)
            print(f"[OK] Downloaded and saved to {raw_data_path}")
        except Exception as e:
            print(f"[ERROR] Failed to download dataset: {e}")
            print("Please download manually from:")
            print("https://archive.ics.uci.edu/ml/datasets/online+retail")
            print(f"Place the CSV at: {raw_data_path}")
            raise
    else:
        print(f"[OK] Found existing raw dataset at {raw_data_path}")

    return raw_data_path


def transform_uci_online_retail(input_path: Path, output_path: Path, n_users: int = 5000) -> pd.DataFrame:
    """
    Transform UCI Online Retail Excel data into BehaviourAI schema.

    The UCI dataset contains transactional data. We need to aggregate by customer
    to create user-level features.

    Processing steps:
    1. Clean data (remove cancelled invoices, invalid entries)
    2. Aggregate by CustomerID to compute features:
       - clicks → count of InvoiceNo (transactions as proxy for clicks)
       - time_spent → average days between purchases (proxy for engagement)
       - purchase_count → sum of Quantity (total items bought)
       - page_views → count of unique StockCode (products viewed)
       - cart_additions → sum of positive Quantity (items added to cart)
    3. Generate customer_segment using KMeans clustering on aggregated features
    4. Add month information (most recent purchase month)
    5. Filter to top N customers by activity

    Args:
        input_path: Path to raw UCI Online Retail CSV
        output_path: Path to save transformed data
        n_users: Number of customers to include (sorted by activity)

    Returns:
        Transformed DataFrame
    """
    print(f"Loading raw data from {input_path}...")
    df = pd.read_excel(input_path) if input_path.suffix == '.xlsx' else pd.read_csv(input_path)

    print(f"Raw data shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")

    # Data cleaning
    print("\nCleaning data...")

    # Remove rows with missing CustomerID
    initial_rows = len(df)
    df = df.dropna(subset=['CustomerID'])
    print(f"  Removed {initial_rows - len(df)} rows with missing CustomerID")

    # Convert CustomerID to string
    df['CustomerID'] = df['CustomerID'].astype(int).astype(str)

    # Remove cancelled invoices (InvoiceNo starts with 'C')
    if 'InvoiceNo' in df.columns:
        df = df[~df['InvoiceNo'].astype(str).str.startswith('C', na=False)]
        print(f"  Removed cancelled invoices")

    # Ensure Quantity is numeric and positive for "cart additions"
    if 'Quantity' in df.columns:
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
        df = df.dropna(subset=['Quantity'])

    # Ensure UnitPrice is numeric and positive
    if 'UnitPrice' in df.columns:
        df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
        df = df[df['UnitPrice'] > 0]

    print(f"Cleaned data shape: {df.shape}")

    # Feature engineering: aggregate by customer
    print("\nAggregating features by customer...")
    customer_features = []

    for customer_id, group in df.groupby('CustomerID'):
        # Clicks: number of transactions (InvoiceNo count)
        clicks = group['InvoiceNo'].nunique()

        # Time spent: days between first and last purchase (engagement duration)
        if 'InvoiceDate' in group.columns:
            dates = pd.to_datetime(group['InvoiceDate'])
            time_spent = (dates.max() - dates.min()).days
            if time_spent == 0:
                time_spent = 1  # Minimum 1 day
        else:
            time_spent = 30  # Default 30 days if no date

        # Purchase count: total quantity of items purchased
        purchase_count = int(group['Quantity'].sum())

        # Page views: number of unique products viewed/ordered (StockCode count)
        page_views = group['StockCode'].nunique()

        # Cart additions: sum of positive quantities (items added before purchase)
        cart_additions = int(group[group['Quantity'] > 0]['Quantity'].sum())
        if cart_additions == 0:
            cart_additions = purchase_count  # Fallback

        # Most recent purchase month
        if 'InvoiceDate' in group.columns:
            last_purchase = pd.to_datetime(group['InvoiceDate']).max()
            month = last_purchase.strftime('%b')  # Jan, Feb, etc.
        else:
            month = 'Jan'

        customer_features.append({
            'user_id': customer_id,
            'clicks': clicks,
            'time_spent': max(1, time_spent),  # Ensure at least 1
            'purchase_count': max(0, purchase_count),
            'page_views': page_views,
            'cart_additions': max(0, cart_additions),
            'month': month
        })

    features_df = pd.DataFrame(customer_features)
    print(f"Created features for {len(features_df)} customers")

    # Handle outliers and scaling
    print("\nHandling outliers...")
    # Cap extreme values at reasonable upper bounds
    bounds = {
        'clicks': 500,
        'time_spent': 365,  # 1 year max
        'purchase_count': 1000,
        'page_views': 500,
        'cart_additions': 1000
    }

    for col, upper_bound in bounds.items():
        if col in features_df.columns:
            before = len(features_df[features_df[col] > upper_bound])
            features_df[col] = features_df[col].clip(upper=upper_bound)
            if before > 0:
                print(f"  Capped {col}: {before} values > {upper_bound}")

    # Ensure all values are non-negative
    for col in ['clicks', 'time_spent', 'purchase_count', 'page_views', 'cart_additions']:
        features_df[col] = features_df[col].clip(lower=0)

    # Sort by activity (most engaged customers first) and take top N
    features_df['total_activity'] = (
        features_df['clicks'] + features_df['purchase_count'] + features_df['page_views']
    )
    features_df = features_df.sort_values('total_activity', ascending=False).head(n_users)
    features_df = features_df.drop(columns=['total_activity'])

    print(f"Selected top {len(features_df)} customers by activity")

    # Generate customer segments using KMeans clustering
    print("\nGenerating customer segments via KMeans clustering...")
    feature_cols_for_clustering = ['clicks', 'time_spent', 'purchase_count', 'page_views', 'cart_additions']

    # Prepare features for clustering
    X = features_df[feature_cols_for_clustering].values
    X_scaled = StandardScaler().fit_transform(X)

    # KMeans clustering (3 segments: Low, Medium, High value)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)

    # Assign segments. We want to label clusters meaningfully:
    # Cluster with highest avg purchase_count = High Value (2)
    # Cluster with medium = Medium Value (1)
    # Cluster with lowest = Low Value (0)
    features_df['cluster_raw'] = clusters

    # Calculate average purchase_count per cluster
    cluster_means = features_df.groupby('cluster_raw')['purchase_count'].mean().sort_values(ascending=False)
    cluster_mapping = {
        cluster_means.index[0]: 2,  # Highest purchases → High Value
        cluster_means.index[1]: 1,  # Medium → Medium Value
        cluster_means.index[2]: 0   # Lowest → Low Value
    }

    features_df['customer_segment'] = features_df['cluster_raw'].map(cluster_mapping)
    features_df = features_df.drop(columns=['cluster_raw'])

    # Verify segment distribution
    segment_counts = features_df['customer_segment'].value_counts().sort_index()
    print("\nSegment distribution:")
    for seg in [0, 1, 2]:
        count = segment_counts.get(seg, 0)
        pct = count / len(features_df) * 100
        label = {0: 'Low Value', 1: 'Medium Value', 2: 'High Value'}[seg]
        print(f"  {label} (segment {seg}): {count} customers ({pct:.1f}%)")

    # Reorder columns to match schema
    features_df = features_df[['user_id', 'clicks', 'time_spent', 'purchase_count', 'page_views', 'cart_additions', 'customer_segment', 'month']]

    # Save to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_path, index=False)
    print(f"\n[OK] Transformed dataset saved to {output_path}")
    print(f"  Total records: {len(features_df)}")
    print(f"  Schema: {', '.join(features_df.columns)}")

    return features_df


def load_and_validate_dataset(input_path: Path) -> pd.DataFrame:
    """
    Load and validate a custom dataset.

    The dataset should have at least these columns (case-insensitive matching):
    - user_id or customer_id or customer_id
    - clicks or session_clicks or click_count
    - time_spent or session_duration or time_minutes
    - purchase_count or purchases or order_count
    - page_views or pages_viewed
    - cart_additions or add_to_cart or cart_items
    - Optional: customer_segment or segment or cluster
    - Optional: month

    This function will:
    1. Load the CSV
    2. Map column names to BehaviourAI schema
    3. Generate segments if missing
    4. Validate data types and ranges
    5. Return clean DataFrame
    """
    print(f"Loading custom dataset from {input_path}...")
    df = pd.read_csv(input_path)

    print(f"Original columns: {df.columns.tolist()}")

    # Column mapping (flexible matching)
    column_mapping = {}
    possible_names = {
        'user_id': ['user_id', 'customer_id', 'customerid', 'cust_id', 'client_id'],
        'clicks': ['clicks', 'click_count', 'session_clicks', 'clicks_count'],
        'time_spent': ['time_spent', 'time_spent_minutes', 'session_duration', 'duration', 'time_minutes'],
        'purchase_count': ['purchase_count', 'purchases', 'order_count', 'total_purchases', 'purchase_total'],
        'page_views': ['page_views', 'pages_viewed', 'pageview_count', 'views'],
        'cart_additions': ['cart_additions', 'add_to_cart', 'cart_items', 'cart_count', 'items_added'],
        'customer_segment': ['customer_segment', 'segment', 'cluster', 'category', 'user_type'],
        'month': ['month', 'month_name', 'purchase_month']
    }

    for target, candidates in possible_names.items():
        for col in df.columns:
            if col.lower().replace(' ', '_') in [c.lower() for c in candidates]:
                column_mapping[target] = col
                break

    print(f"Mapped columns: {column_mapping}")

    # Check required columns
    required = ['user_id', 'clicks', 'time_spent', 'purchase_count', 'page_views', 'cart_additions']
    missing = [r for r in required if r not in column_mapping]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Please ensure your dataset contains these fields.")

    # Create new DataFrame with standardized column names
    transformed = pd.DataFrame()
    for target in SCHEMA.keys():
        if target in column_mapping:
            transformed[target] = df[column_mapping[target]]
        elif target == 'customer_segment' and target not in column_mapping:
            # Will generate segments later
            continue
        elif target == 'month' and target not in column_mapping:
            # Default to current month or 'Jan'
            transformed[target] = 'Jan'
        else:
            raise ValueError(f"Could not map column for: {target}")

    # Clean data types
    print("\nCleaning and validating data...")
    for col in ['clicks', 'purchase_count', 'page_views', 'cart_additions']:
        transformed[col] = pd.to_numeric(transformed[col], errors='coerce').fillna(0).astype(int)
        transformed[col] = transformed[col].clip(lower=0)

    transformed['time_spent'] = pd.to_numeric(transformed['time_spent'], errors='coerce').fillna(1).astype(float)
    transformed['time_spent'] = transformed['time_spent'].clip(lower=0, upper=1440)  # Max 24 hours

    if 'customer_segment' not in transformed.columns:
        print("\nGenerating customer segments using KMeans...")
        X = transformed[['clicks', 'time_spent', 'purchase_count', 'page_views', 'cart_additions']].values
        X_scaled = StandardScaler().fit_transform(X)
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)

        # Map clusters to Low/Medium/High based on purchase_count
        transformed['cluster_raw'] = clusters
        cluster_means = transformed.groupby('cluster_raw')['purchase_count'].mean().sort_values(ascending=False)
        cluster_mapping = {
            cluster_means.index[0]: 2,
            cluster_means.index[1]: 1,
            cluster_means.index[2]: 0
        }
        transformed['customer_segment'] = transformed['cluster_raw'].map(cluster_mapping)
        transformed = transformed.drop(columns=['cluster_raw'])
        print("[OK] Segments generated")
    else:
        # Ensure segments are 0, 1, 2
        transformed['customer_segment'] = pd.to_numeric(transformed['customer_segment'], errors='coerce')
        # Map to 0, 1, 2 if needed (you may need to adjust based on your data)
        unique_segments = sorted(transformed['customer_segment'].dropna().unique())
        if len(unique_segments) == 3:
            # Remap to 0, 1, 2 in order
            old_to_new = {unique_segments[i]: i for i in range(3)}
            transformed['customer_segment'] = transformed['customer_segment'].map(old_to_new)
            print(f"[OK] Remapped segments: {old_to_new}")

    # Validate month format
    valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    if 'month' in transformed.columns:
        transformed['month'] = transformed['month'].astype(str).str.title()
        # Fix invalid months
        invalid_mask = ~transformed['month'].isin(valid_months)
        if invalid_mask.any():
            print(f"  Warning: {invalid_mask.sum()} invalid month values, replacing with 'Jan'")
            transformed.loc[invalid_mask, 'month'] = 'Jan'
    else:
        transformed['month'] = 'Jan'

    # Reorder columns
    transformed = transformed[['user_id', 'clicks', 'time_spent', 'purchase_count', 'page_views', 'cart_additions', 'customer_segment', 'month']]

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    transformed.to_csv(output_path, index=False)
    print(f"\n[OK] Transformed dataset saved to {output_path}")
    print(f"  Records: {len(transformed)}")
    print(f"  Schema: {', '.join(transformed.columns)}")

    return transformed


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess real-world customer behavior data for BehaviourAI"
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Path to custom input CSV/Excel file (if not using UCI dataset)'
    )
    parser.add_argument(
        '--n-users',
        type=int,
        default=5000,
        help='Number of customers to include (default: 5000)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("BehaviourAI - Real Data Preprocessing")
    print("=" * 60)

    # Ensure output directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Process data
    if args.input:
        # Custom dataset
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}")
            return 1
        df = load_and_validate_dataset(input_path)
        df.to_csv(OUTPUT_FILE, index=False)
    else:
        # UCI Online Retail dataset
        try:
            raw_path = download_uci_online_retail()
            df = transform_uci_online_retail(raw_path, OUTPUT_FILE, n_users=args.n_users)
        except Exception as e:
            print(f"\n[ERROR] Error during preprocessing: {e}")
            import traceback
            traceback.print_exc()
            return 1

    print("\n" + "=" * 60)
    print("Preprocessing complete!")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Records: {len(df)}")
    print("\nNext steps:")
    print("  1. Run: python scripts/init_db.py  (to migrate data to database)")
    print("  2. Run: python test_app.py         (to verify integration)")
    print("  3. Run: python app.py              (to start the app)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
