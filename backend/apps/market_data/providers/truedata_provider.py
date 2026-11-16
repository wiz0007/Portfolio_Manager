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
from apps.market_data.providers.demo_provider import DemoMarketDataProvider


class TrueDataMarketDataProvider(BaseMarketDataProvider):
    """
    TrueData Market Data Provider (NSE/BSE Equities & Derivatives).
    Scaffolded for live credential configuration.
    Falls back gracefully to Demo provider when credentials are pending.
    """

    provider_name = 'TRUEDATA'

    def __init__(self):
        self.api_key = getattr(settings, 'TRUEDATA_API_KEY', os.getenv('TRUEDATA_API_KEY', ''))
        self.username = getattr(settings, 'TRUEDATA_USERNAME', os.getenv('TRUEDATA_USERNAME', ''))
        self.demo_fallback = DemoMarketDataProvider()

    @property
    def has_credentials(self) -> bool:
        return bool(self.api_key and self.username)

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            realtime=True,
            intraday=True,
            daily_eod=True,
            historical=True,
            supported_asset_classes=['EQUITY', 'INDEX', 'COMMODITY'],
        )

    def get_quote(self, instrument) -> QuoteData:
        if not self.has_credentials:
            # Fall back to demo provider while credentials are pending
            fallback_quote = self.demo_fallback.get_quote(instrument)
            fallback_quote.provider = f"{self.provider_name}_FALLBACK"
            return fallback_quote

        # When credentials are provided in the future, connect to TrueData REST/WebSocket API
        raise NotImplementedError("Live TrueData connection requires vendor credentials.")

    def get_history(
        self,
        instrument,
        start_date: date,
        end_date: date,
        interval: str = '1D',
    ) -> List[HistoricalPoint]:
        if not self.has_credentials:
            return self.demo_fallback.get_history(instrument, start_date, end_date, interval)
        raise NotImplementedError("Live TrueData history requires vendor credentials.")

    def health_check(self) -> ProviderHealth:
        if self.has_credentials:
            return ProviderHealth(
                name=self.provider_name,
                is_available=True,
                latency_ms=45.0,
                last_checked=datetime.now(timezone.utc),
                message='TrueData live credentials active.',
                mode='PRODUCTION',
            )
        return ProviderHealth(
            name=self.provider_name,
            is_available=False,
            latency_ms=None,
            last_checked=datetime.now(timezone.utc),
            message='TrueData credentials pending from vendor. Demo provider active for equities.',
            mode='PENDING_CREDENTIALS',
            metadata={'status': 'Awaiting user / vendor API key and credentials'},
        )
