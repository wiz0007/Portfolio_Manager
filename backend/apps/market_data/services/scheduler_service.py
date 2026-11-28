"""
Market Data Scheduler Service.

Orchestrates automated synchronization, reconciliation, and health monitoring
for market data providers (CoinGecko, MFAPI/AMFI) with lock lease handling,
overlap prevention, failure categorization, and bounded job execution.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache

from apps.market_data.providers.coingecko.client import CoinGeckoClient
from apps.market_data.providers.mfapi.client import MFAPIClient
from apps.market_data.services.crypto_service import CryptoMarketDataService
from apps.market_data.services.mutual_fund_service import MutualFundMarketDataService
from apps.market_data.services.system_publisher import SystemPublisher

logger = logging.getLogger(__name__)


class MarketDataSchedulerService:
    """
    Central scheduler for market data ingestion and synchronization.
    Tracks job execution states, failure categories, and prevents overlapping jobs.
    """

    LOCK_TIMEOUT_SECONDS = 600  # 10 minutes lock expiry

    # Job registry with cadence rules and provider dependencies
    JOBS = {
        'crypto_prices': {
            'provider': 'COINGECKO',
            'asset_class': 'CRYPTO',
            'scope': 'PRICE_SYNC',
            'default_interval_minutes': getattr(settings, 'COINGECKO_PRICE_SYNC_INTERVAL_MINUTES', 15),
            'business_day_only': False,
        },
        'crypto_catalogue': {
            'provider': 'COINGECKO',
            'asset_class': 'CRYPTO',
            'scope': 'CATALOGUE_SYNC',
            'default_interval_minutes': 1440,  # 24 hours
            'business_day_only': False,
        },
        'mf_nav': {
            'provider': 'MFAPI',
            'asset_class': 'MUTUAL_FUND',
            'scope': 'NAV_SYNC',
            'default_interval_minutes': getattr(settings, 'MF_NAV_SYNC_INTERVAL_HOURS', 24) * 60,
            'business_day_only': True,
        },
        'mf_catalogue': {
            'provider': 'MFAPI',
            'asset_class': 'MUTUAL_FUND',
            'scope': 'CATALOGUE_SYNC',
            'default_interval_minutes': 1440 * 7,  # weekly
            'business_day_only': False,
        },
        'health_check': {
            'provider': 'ALL',
            'asset_class': 'ALL',
            'scope': 'HEALTH_CHECK',
            'default_interval_minutes': 60,  # 1 hour
            'business_day_only': False,
        },
    }

    # Internal in-memory state fallback when cache is cleared
    _job_states: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_job_state(cls, job_name: str) -> Dict[str, Any]:
        """Retrieve state for a job from cache or internal dict."""
        cache_key = f"market_data_job_state_{job_name}"
        cached = cache.get(cache_key)
        if cached and isinstance(cached, dict):
            return cached
        if job_name in cls._job_states:
            return cls._job_states[job_name]
        return {
            'job_id': job_name,
            'provider': cls.JOBS.get(job_name, {}).get('provider', 'UNKNOWN'),
            'asset_class': cls.JOBS.get(job_name, {}).get('asset_class', 'UNKNOWN'),
            'scope': cls.JOBS.get(job_name, {}).get('scope', 'UNKNOWN'),
            'started_at': None,
            'completed_at': None,
            'last_successful_at': None,
            'attempt_count': 0,
            'processed_count': 0,
            'created_count': 0,
            'skipped_count': 0,
            'corrected_count': 0,
            'failed_count': 0,
            'failure_category': None,
            'last_error': None,
            'lock_status': 'IDLE',
        }

    @classmethod
    def update_job_state(cls, job_name: str, updates: Dict[str, Any]) -> None:
        """Update job state in both cache and internal dictionary."""
        state = cls.get_job_state(job_name)
        state.update(updates)
        cls._job_states[job_name] = state
        cache_key = f"market_data_job_state_{job_name}"
        cache.set(cache_key, state, timeout=86400 * 7)  # 7 days retention

    @classmethod
    def is_provider_enabled(cls, provider: str) -> bool:
        """Check whether provider is globally enabled in settings."""
        if provider == 'COINGECKO':
            return getattr(settings, 'COINGECKO_ENABLED', True)
        if provider == 'MFAPI':
            return getattr(settings, 'MFAPI_ENABLED', True)
        if provider == 'ALL':
            return True
        return False

    @classmethod
    def is_job_due(cls, job_name: str) -> bool:
        """Check if job is due for execution based on last run timestamp and interval."""
        job_def = cls.JOBS.get(job_name)
        if not job_def:
            return False

        provider = job_def['provider']
        if not cls.is_provider_enabled(provider):
            return False

        state = cls.get_job_state(job_name)
        last_success = state.get('last_successful_at')
        if not last_success:
            return True

        if isinstance(last_success, str):
            try:
                last_success = datetime.fromisoformat(last_success)
            except ValueError:
                return True

        interval_minutes = job_def['default_interval_minutes']
        now = datetime.now(timezone.utc)
        if now - last_success >= timedelta(minutes=interval_minutes):
            if job_def.get('business_day_only'):
                # In Python weekday: Monday=0 ... Sunday=6
                if now.weekday() >= 5:
                    return False
            return True

        return False

    @classmethod
    def run_job(cls, job_name: str, dry_run: bool = False, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a scheduled market data job with lock acquisition and error handling.
        """
        if job_name not in cls.JOBS:
            raise ValueError(f"Unknown market data job: {job_name}")

        job_def = cls.JOBS[job_name]
        provider = job_def['provider']

        if not cls.is_provider_enabled(provider):
            logger.info("Scheduler: provider %s is disabled. Skipping job %s.", provider, job_name)
            return {'status': 'SKIPPED', 'reason': f'Provider {provider} disabled'}

        # Lock acquisition to prevent overlapping executions
        lock_key = f"market_data_job_lock_{job_name}"
        acquired = cache.add(lock_key, "locked", timeout=cls.LOCK_TIMEOUT_SECONDS)
        if not acquired and not dry_run:
            logger.warning("Scheduler: Job %s is currently locked by another worker. Skipping.", job_name)
            return {'status': 'LOCKED', 'reason': 'Another worker is executing this job'}

        now = datetime.now(timezone.utc)
        cls.update_job_state(job_name, {
            'started_at': now.isoformat(),
            'attempt_count': cls.get_job_state(job_name).get('attempt_count', 0) + 1,
            'lock_status': 'RUNNING',
            'failure_category': None,
            'last_error': None,
        })

        publisher = SystemPublisher
        try:
            result = cls._dispatch_job(job_name, dry_run=dry_run, limit=limit, publisher=publisher)

            completed_now = datetime.now(timezone.utc)
            cls.update_job_state(job_name, {
                'completed_at': completed_now.isoformat(),
                'last_successful_at': completed_now.isoformat(),
                'processed_count': result.get('processed', result.get('total_synced', result.get('synced', 0))),
                'created_count': result.get('created', 0),
                'skipped_count': result.get('skipped', 0),
                'corrected_count': result.get('corrected', 0),
                'failed_count': len(result.get('errors', [])) if result.get('errors') else 0,
                'lock_status': 'IDLE',
                'failure_category': None,
            })
            result['status'] = 'SUCCESS'
            return result

        except Exception as exc:
            completed_now = datetime.now(timezone.utc)
            err_msg = str(exc)
            failure_cat = 'NETWORK_ERROR' if 'timeout' in err_msg.lower() or 'connection' in err_msg.lower() else 'EXECUTION_ERROR'
            logger.exception("Scheduler: Job %s failed: %s", job_name, err_msg)
            cls.update_job_state(job_name, {
                'completed_at': completed_now.isoformat(),
                'lock_status': 'IDLE',
                'failure_category': failure_cat,
                'last_error': err_msg,
                'failed_count': cls.get_job_state(job_name).get('failed_count', 0) + 1,
            })
            return {'status': 'FAILED', 'error': err_msg, 'failure_category': failure_cat}

        finally:
            cache.delete(lock_key)

    @classmethod
    def _dispatch_job(
        cls, job_name: str, dry_run: bool = False, limit: Optional[int] = None, publisher: Any = None
    ) -> Dict[str, Any]:
        """Dispatch job execution to corresponding service."""
        if job_name == 'crypto_prices':
            if dry_run:
                quotes = CoinGeckoClient().get_markets()
                return {'synced': len(quotes), 'dry_run': True}
            return CryptoMarketDataService.sync_prices(publisher=publisher)

        if job_name == 'crypto_catalogue':
            if dry_run:
                coins = CoinGeckoClient().get_coins_list()
                if limit:
                    coins = coins[:limit]
                return {'total_synced': len(coins), 'created': 0, 'updated': 0, 'dry_run': True}
            return CryptoMarketDataService.sync_catalogue(from_provider=True)

        if job_name == 'mf_nav':
            if dry_run:
                return {'synced': 0, 'dry_run': True}
            return MutualFundMarketDataService.sync_nav(publisher=publisher)

        if job_name == 'mf_catalogue':
            if dry_run:
                schemes = MFAPIClient().get_all_schemes()
                if limit:
                    schemes = schemes[:limit]
                return {'total_synced': len(schemes), 'created': 0, 'updated': 0, 'dry_run': True}
            return MutualFundMarketDataService.sync_catalogue()

        if job_name == 'health_check':
            health: Dict[str, Any] = {}
            # Check CoinGecko
            try:
                cg_ping = CoinGeckoClient().ping()
                health['coingecko'] = 'HEALTHY' if cg_ping else 'UNHEALTHY'
            except Exception as e:
                health['coingecko'] = f'ERROR: {e}'

            # Check MFAPI
            try:
                mf_check = MFAPIClient().ping()
                health['mfapi'] = 'HEALTHY' if mf_check else 'UNHEALTHY'
            except Exception as e:
                health['mfapi'] = f'ERROR: {e}'

            return {'health': health, 'processed': len(health)}

        raise ValueError(f"No handler defined for job {job_name}")

    @classmethod
    def run_all_due_jobs(cls, dry_run: bool = False) -> Dict[str, Any]:
        """Execute all jobs that are currently due."""
        results = {}
        for job_name in cls.JOBS:
            if cls.is_job_due(job_name):
                logger.info("Scheduler: Running due job %s", job_name)
                results[job_name] = cls.run_job(job_name, dry_run=dry_run)
            else:
                results[job_name] = {'status': 'SKIPPED', 'reason': 'Not due'}
        return results
