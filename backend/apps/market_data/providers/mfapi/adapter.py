"""MFAPI market data provider adapter."""
import logging
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from django.conf import settings

from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
from apps.market_data.providers.base import (
    BaseMarketDataProvider,
    HistoricalPoint,
    ProviderCapabilities,
    ProviderHealth,
    QuoteData,
)
from apps.market_data.providers.mfapi.client import MFAPIClient
from apps.market_data.providers.mfapi.constants import CURATED_SCHEMES, DEFAULT_CURRENCY
from apps.market_data.providers.mfapi.serializers import (
    serialize_nav_data,
)

logger = logging.getLogger(__name__)


class MFAPIMarketDataProvider(BaseMarketDataProvider):
    """
    Indian Mutual Fund Net Asset Value (NAV) provider adapter using MFAPI.in.
    Provides daily authoritative EOD NAV quotes and complete historical series.
    """

    provider_name = 'MFAPI'

    def __init__(self, client: Optional[MFAPIClient] = None):
        self.client = client or MFAPIClient()

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            realtime=False,
            intraday=False,
            daily_eod=True,
            historical=True,
            supported_asset_classes=['MUTUAL_FUND'],
        )

    def _resolve_scheme_code(self, instrument) -> str:
        """Resolves AMFI scheme code for mutual fund instrument."""
        if getattr(instrument, 'scheme_code', None):
            return str(instrument.scheme_code).strip()

        # Check secondary database provider mapping
        mapping = ProviderInstrumentMapping.objects.using('market_data').filter(
            instrument_id=instrument.id,
            provider_name__in=['MFAPI', 'AMFI'],
        ).order_by('-is_primary').first()
        if mapping and mapping.provider_symbol:
            return mapping.provider_symbol.strip()

        sym = (getattr(instrument, 'symbol', '') or '').strip()
        if sym.isdigit():
            return sym

        isin = getattr(instrument, 'isin', None)
        if isin:
            for c in CURATED_SCHEMES:
                if c.get('isin') == isin:
                    return c['scheme_code']

        return sym

    def get_quote(self, instrument) -> QuoteData:
        scheme_code = self._resolve_scheme_code(instrument)
        if not scheme_code:
            raise ValueError(f"Cannot resolve scheme_code for instrument {instrument.symbol}")

        raw = self.client.get_scheme(scheme_code)
        nav_entries = serialize_nav_data(raw.get('data') or [])
        if not nav_entries:
            raise ValueError(f"No NAV data returned for scheme code {scheme_code}")

        # The serialized entries are sorted ascending by date, so the last is the latest NAV
        latest = nav_entries[-1]
        prev = nav_entries[-2] if len(nav_entries) >= 2 else None

        change_amt = (latest['nav'] - prev['nav']) if prev else None
        change_pct = ((latest['nav'] - prev['nav']) / prev['nav'] * Decimal('100')) if prev and prev['nav'] > 0 else None

        currency = getattr(settings, 'MF_NAV_DEFAULT_CURRENCY', DEFAULT_CURRENCY)
        return QuoteData(
            symbol=instrument.symbol,
            price=latest['nav'],
            close_price=latest['nav'],
            change_amount=change_amt,
            change_percent=change_pct,
            timestamp=latest['timestamp'],
            provider=self.provider_name,
            is_synthetic=False,
            currency=currency,
        )

    def get_history(
        self,
        instrument,
        start_date: date,
        end_date: date,
        interval: str = '1D',
    ) -> List[HistoricalPoint]:
        scheme_code = self._resolve_scheme_code(instrument)
        if not scheme_code:
            return []

        raw = self.client.get_scheme(scheme_code)
        nav_entries = serialize_nav_data(raw.get('data') or [])

        start_dt = datetime(start_date.year, start_date.month, start_date.day, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)

        historical_points = []
        prev_price = None

        for item in nav_entries:
            dt = item['timestamp']
            price = item['nav']
            if dt < start_dt or dt > end_dt:
                prev_price = price
                continue

            change_amt = (price - prev_price) if prev_price is not None else None
            change_pct = ((price - prev_price) / prev_price * Decimal('100')) if prev_price and prev_price > 0 else None
            prev_price = price

            historical_points.append(
                HistoricalPoint(
                    timestamp=dt,
                    price=price,
                    close_price=price,
                    change_amount=change_amt,
                    change_percent=change_pct,
                )
            )

        return historical_points

    def health_check(self) -> ProviderHealth:
        enabled = getattr(settings, 'MFAPI_ENABLED', True)
        if not enabled:
            return ProviderHealth(
                name=self.provider_name,
                is_available=False,
                last_checked=datetime.now(timezone.utc),
                message='MFAPI provider is disabled by configuration.',
                mode='PRODUCTION',
                metadata={'enabled': False},
            )

        t0 = time.perf_counter()
        try:
            ok = self.client.ping()
            latency = round((time.perf_counter() - t0) * 1000, 2)
            if ok:
                return ProviderHealth(
                    name=self.provider_name,
                    is_available=True,
                    latency_ms=latency,
                    last_checked=datetime.now(timezone.utc),
                    message='MFAPI.in online and responding.',
                    mode='PRODUCTION',
                    metadata={'base_url': self.client.base_url},
                )
            return ProviderHealth(
                name=self.provider_name,
                is_available=False,
                latency_ms=latency,
                last_checked=datetime.now(timezone.utc),
                message='MFAPI ping returned invalid response.',
                mode='PRODUCTION',
            )
        except Exception as e:
            latency = round((time.perf_counter() - t0) * 1000, 2)
            return ProviderHealth(
                name=self.provider_name,
                is_available=False,
                latency_ms=latency,
                last_checked=datetime.now(timezone.utc),
                message=f'MFAPI health check failed: {e!s}',
                mode='PRODUCTION',
            )
