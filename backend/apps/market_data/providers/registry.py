import logging
from typing import Dict, List, Optional

from django.conf import settings

from apps.market_data.providers.amfi_provider import AMFIMarketDataProvider
from apps.market_data.providers.base import (
    BaseMarketDataProvider,
    ProviderHealth,
)
from apps.market_data.providers.demo_provider import DemoMarketDataProvider
from apps.market_data.providers.truedata_provider import TrueDataMarketDataProvider

logger = logging.getLogger(__name__)


class MarketDataProviderRegistry:
    """
    Centralized registry for market data providers.
    Directs quote and historical requests to the appropriate provider based on
    asset class, application mode ('DEMO' vs 'PRODUCTION'), and provider availability.
    """

    def __init__(self):
        self._providers: Dict[str, BaseMarketDataProvider] = {}
        self._initialize_defaults()

    def _initialize_defaults(self):
        demo = DemoMarketDataProvider()
        amfi = AMFIMarketDataProvider()
        truedata = TrueDataMarketDataProvider()

        self.register(demo)
        self.register(amfi)
        self.register(truedata)

    def register(self, provider: BaseMarketDataProvider):
        self._providers[provider.provider_name.upper()] = provider

    def get(self, name: str) -> Optional[BaseMarketDataProvider]:
        return self._providers.get(name.upper())

    def get_provider_for_instrument(self, instrument) -> BaseMarketDataProvider:
        mode = getattr(settings, 'MARKET_DATA_PROVIDER_MODE', 'DEMO').upper()

        # In DEMO mode, DEMO provider handles all requests
        if mode == 'DEMO':
            return self._providers['DEMO']

        # In PRODUCTION mode:
        asset_class = getattr(instrument, 'asset_class', 'EQUITY')

        # Mutual funds default to AMFI
        if asset_class == 'MUTUAL_FUND':
            return self._providers.get('AMFI', self._providers['DEMO'])

        # Equities/Indices try TrueData if configured, else fallback to DEMO
        if asset_class in ['EQUITY', 'INDEX']:
            truedata = self._providers.get('TRUEDATA')
            if truedata and getattr(truedata, 'has_credentials', False):
                return truedata
            return self._providers['DEMO']

        # Default fallback
        return self._providers['DEMO']

    def list_providers(self) -> List[Dict[str, any]]:
        results = []
        for name, provider in self._providers.items():
            caps = provider.capabilities
            results.append({
                'name': name,
                'capabilities': {
                    'realtime': caps.realtime,
                    'intraday': caps.intraday,
                    'daily_eod': caps.daily_eod,
                    'historical': caps.historical,
                    'supported_asset_classes': caps.supported_asset_classes,
                },
            })
        return results

    def check_all_health(self) -> List[ProviderHealth]:
        return [provider.health_check() for provider in self._providers.values()]


# Global registry singleton
provider_registry = MarketDataProviderRegistry()


def get_provider(name: str) -> Optional[BaseMarketDataProvider]:
    return provider_registry.get(name)
