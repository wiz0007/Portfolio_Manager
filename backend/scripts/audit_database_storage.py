import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
sys.path.insert(0, BACKEND_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection

def main():
    cursor = connection.cursor()
    
    # 1. Total database size
    cursor.execute("SELECT pg_database_size(current_database()), pg_size_pretty(pg_database_size(current_database()));")
    db_size_bytes, db_size_pretty = cursor.fetchone()
    print("=" * 70)
    print(f"Neon PostgreSQL Database Size: {db_size_pretty} ({db_size_bytes:,} bytes)")
    print("=" * 70)

    # 2. Per-table and index breakdown
    query = """
    SELECT
        c.relname AS table_name,
        s.n_live_tup AS row_estimate,
        pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size,
        pg_size_pretty(pg_relation_size(c.oid)) AS table_size,
        pg_size_pretty(pg_indexes_size(c.oid)) AS index_size,
        pg_total_relation_size(c.oid) AS total_bytes
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_stat_user_tables s ON s.relid = c.oid
    WHERE n.nspname = 'public'
    ORDER BY pg_total_relation_size(c.oid) DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"{'Table Name':<32} {'Rows':<8} {'Total':<10} {'Table':<10} {'Indexes':<10}")
    print("-" * 70)
    for r in rows:
        tname, r_est, total, tbl, idx, _ = r
        print(f"{tname:<32} {r_est:<8} {total:<10} {tbl:<10} {idx:<10}")

    # 3. MarketDataPoint synthetic vs non-synthetic breakdown
    print("\n" + "=" * 70)
    print("Market Data Point Composition Audit")
    print("=" * 70)
    cursor.execute("""
    SELECT provider, is_synthetic, COUNT(*), MIN(timestamp::date), MAX(timestamp::date)
    FROM market_data_points
    GROUP BY provider, is_synthetic
    ORDER BY count DESC;
    """)
    for r in cursor.fetchall():
        prov, synth, count, min_d, max_d = r
        print(f"Provider: {prov:<16} | Synthetic: {str(synth):<5} | Count: {count:<6} | Range: {min_d} to {max_d}")

    # 4. PriceObservations breakdown
    print("\n" + "=" * 70)
    print("Price Observations Audit")
    print("=" * 70)
    cursor.execute("""
    SELECT source, status, is_synthetic, COUNT(*), MIN(effective_at::date), MAX(effective_at::date)
    FROM price_observations
    GROUP BY source, status, is_synthetic
    ORDER BY count DESC;
    """)
    for r in cursor.fetchall():
        src, status, synth, count, min_d, max_d = r
        print(f"Source: {src:<16} | Status: {status:<12} | Synthetic: {str(synth):<5} | Count: {count:<6} | Range: {min_d} to {max_d}")

if __name__ == '__main__':
    main()
