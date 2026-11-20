from apps.market_data.services.price_resolver import (
    PriceResolver,
    ResolutionStatus,
    ResolvedPrice,
)

# MarketDataResolver is the canonical domain resolver specified by the Architecture ERD
MarketDataResolver = PriceResolver

__all__ = [
    'MarketDataResolver',
    'PriceResolver',
    'ResolutionStatus',
    'ResolvedPrice',
]
