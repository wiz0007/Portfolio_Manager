import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
sys.path.insert(0, BACKEND_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection
from apps.market_data.models import Instrument

def main():
    rel = Instrument.objects.filter(symbol='RELIANCE').first()
    if not rel:
        print("RELIANCE not found!")
        return

    query = """
    EXPLAIN (ANALYZE, BUFFERS)
    SELECT id, effective_at, value, open_price, high_price, low_price, volume
    FROM price_observations
    WHERE instrument_id = %s
      AND status = 'PUBLISHED'
      AND effective_at >= '2025-11-19 00:00:00+00'
      AND effective_at <= '2026-11-19 23:59:59+00'
    ORDER BY effective_at ASC;
    """

    cursor = connection.cursor()
    cursor.execute(query, [str(rel.id)])
    rows = cursor.fetchall()

    print("=" * 65)
    print("PostgreSQL Query Execution Plan (RELIANCE 1-Year History):")
    print("=" * 65)
    for r in rows:
        print(r[0])
    print("=" * 65)

if __name__ == '__main__':
    main()
