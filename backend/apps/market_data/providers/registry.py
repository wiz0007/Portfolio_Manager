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


class ProviderUnavailableError(RuntimeError):
    """Raised when no real provider with the required capability is configured."""


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
        if mode == 'DEMO':
            return self._providers['DEMO']
        if mode != 'PRODUCTION':
            raise ProviderUnavailableError(f'Unsupported MARKET_DATA_PROVIDER_MODE: {mode}')

        asset_class = getattr(instrument, 'asset_class', 'EQUITY')
        if asset_class == 'MUTUAL_FUND':
            provider = self._providers.get('AMFI')
        elif asset_class in ('EQUITY', 'INDEX', 'COMMODITY'):
            provider = self._providers.get('TRUEDATA')
        else:
            provider = None

        if provider is None:
            raise ProviderUnavailableError(
                f'No production market-data provider is configured for asset class {asset_class}.'
            )
        capabilities = provider.capabilities
        if asset_class not in capabilities.supported_asset_classes:
            raise ProviderUnavailableError(
                f'{provider.provider_name} does not support {asset_class}.'
            )
        if not any((capabilities.realtime, capabilities.intraday, capabilities.daily_eod, capabilities.historical)):
            raise ProviderUnavailableError(f'{provider.provider_name} has no implemented capabilities.')
        if provider.provider_name == 'TRUEDATA' and not getattr(provider, 'is_implemented', False):
            raise ProviderUnavailableError('TrueData adapter is not implemented; no demo fallback is allowed in production.')
        return provider

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
