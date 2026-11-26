import os
from datetime import date, datetime, timezone
from typing import List

from django.conf import settings

from apps.market_data.providers.base import (
    BaseMarketDataProvider,
    HistoricalPoint,
    ProviderCapabilities,
    ProviderHealth,
    QuoteData,
)


class TrueDataMarketDataProvider(BaseMarketDataProvider):
    """TrueData integration placeholder. No live operation is claimed as implemented."""

    provider_name = 'TRUEDATA'
    is_implemented = False

    def __init__(self):
        self.api_key = getattr(settings, 'TRUEDATA_API_KEY', os.getenv('TRUEDATA_API_KEY', ''))
        self.username = getattr(settings, 'TRUEDATA_USERNAME', os.getenv('TRUEDATA_USERNAME', ''))

    @property
    def has_credentials(self) -> bool:
        return bool(self.api_key and self.username)

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            realtime=False, intraday=False, daily_eod=False, historical=False,
            supported_asset_classes=[],
        )

    def get_quote(self, instrument) -> QuoteData:
        raise NotImplementedError('TrueData live quote integration has not been implemented.')

    def get_history(self, instrument, start_date: date, end_date: date, interval: str = '1D') -> List[HistoricalPoint]:
        raise NotImplementedError('TrueData historical integration has not been implemented.')

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            name=self.provider_name, is_available=False, latency_ms=None,
            last_checked=datetime.now(timezone.utc),
            message='Adapter implementation is pending; credentials alone do not indicate availability.',
            mode='NOT_IMPLEMENTED',
            metadata={'credentials_configured': self.has_credentials},
        )
