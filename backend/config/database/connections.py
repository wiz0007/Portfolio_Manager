import time
from typing import Any, Dict

from django.conf import settings
from django.db import connections


def is_market_data_db_configured() -> bool:
    """Returns True if the 'market_data' database alias is configured in settings.DATABASES."""
    return 'market_data' in getattr(settings, 'DATABASES', {})


def check_primary_database_health() -> Dict[str, Any]:
    """Checks the health and responsiveness of the primary (default) portfolio database."""
    start = time.perf_counter()
    try:
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            'alias': 'default',
            'role': 'Primary Portfolio Database',
            'status': 'HEALTHY',
            'engine': conn.settings_dict.get('ENGINE', 'unknown'),
            'latency_ms': latency_ms,
            'is_configured': True,
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            'alias': 'default',
            'role': 'Primary Portfolio Database',
            'status': 'UNHEALTHY',
            'error': str(e),
            'latency_ms': latency_ms,
            'is_configured': True,
        }


def check_market_data_database_health() -> Dict[str, Any]:
    """Checks the health and responsiveness of the market data storage database."""
    if not is_market_data_db_configured():
        return {
            'alias': 'market_data',
            'role': 'Market Data & Historical Time-Series Storage',
            'status': 'PENDING_CONFIGURATION',
            'is_configured': False,
            'message': 'NEON_STORAGE_DATABASE_URL environment variable is not configured.',
        }

    start = time.perf_counter()
    try:
        conn = connections['market_data']
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            'alias': 'market_data',
            'role': 'Market Data & Historical Time-Series Storage',
            'status': 'HEALTHY',
            'engine': conn.settings_dict.get('ENGINE', 'unknown'),
            'latency_ms': latency_ms,
            'is_configured': True,
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            'alias': 'market_data',
            'role': 'Market Data & Historical Time-Series Storage',
            'status': 'UNHEALTHY',
            'error': str(e),
            'latency_ms': latency_ms,
            'is_configured': True,
        }


def get_database_status(detailed: bool = False) -> Dict[str, Any]:
    """
    Comprehensive health summary across both databases.
    If detailed=False, sanitizes error messages and engine details to prevent leaking internal infrastructure.
    """
    primary = check_primary_database_health()
    market = check_market_data_database_health()

    if primary['status'] == 'HEALTHY' and market['status'] == 'HEALTHY':
        overall_status = 'HEALTHY'
    elif primary['status'] == 'HEALTHY' and market['status'] == 'PENDING_CONFIGURATION':
        # Missing secondary configuration is degraded in development, not healthy
        overall_status = 'DEGRADED'
    else:
        overall_status = 'UNHEALTHY'

    if not detailed:
        # Sanitize internal connection details and raw exceptions
        sanitized_primary = {
            'alias': primary['alias'],
            'role': primary['role'],
            'status': primary['status'],
            'is_configured': primary['is_configured'],
            'latency_ms': primary.get('latency_ms'),
        }
        sanitized_market = {
            'alias': market['alias'],
            'role': market['role'],
            'status': market['status'],
            'is_configured': market['is_configured'],
            'latency_ms': market.get('latency_ms'),
        }
        return {
            'overall_status': overall_status,
            'databases': {
                'primary': sanitized_primary,
                'market_data': sanitized_market,
            },
        }

    return {
        'overall_status': overall_status,
        'databases': {
            'primary': primary,
            'market_data': market,
        },
    }
