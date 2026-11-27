"""CoinGecko market data provider adapter."""
import logging
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.conf import settings

from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
from apps.market_data.providers.base import (
    BaseMarketDataProvider,
    HistoricalPoint,
    ProviderCapabilities,
    ProviderHealth,
    QuoteData,
)
from apps.market_data.providers.coingecko.client import CoinGeckoClient
from apps.market_data.providers.coingecko.constants import (
    SUPPORTED_COIN_IDS,
    SYMBOL_TO_COIN_ID,
)
from apps.market_data.providers.coingecko.exceptions import CoinGeckoError
from apps.market_data.providers.coingecko.serializers import (
    serialize_chart_data,
    serialize_market_item,
)

logger = logging.getLogger(__name__)


class CoinGeckoMarketDataProvider(BaseMarketDataProvider):
    """
    Production-ready CoinGecko adapter implementing BaseMarketDataProvider.
    Provides verified cryptocurrency spot quotes and historical price points.
    """

    provider_name = 'COINGECKO'

    def __init__(self, client: Optional[CoinGeckoClient] = None):
        self.client = client or CoinGeckoClient()

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            realtime=False,
            intraday=False,
            daily_eod=True,
            historical=True,
            supported_asset_classes=['CRYPTO'],
        )

    def _resolve_coin_id(self, instrument) -> str:
        """Find the canonical CoinGecko coin_id for an instrument."""
        # 1. Check primary database mapping
        mapping = ProviderInstrumentMapping.objects.using('market_data').filter(
            instrument_id=instrument.id,
            provider_name=self.provider_name,
        ).first()
        if mapping and mapping.provider_symbol:
            return mapping.provider_symbol.strip().lower()

        # 2. Check supported coins map by symbol
        sym = (instrument.symbol or '').strip().upper()
        if sym in SYMBOL_TO_COIN_ID:
            return SYMBOL_TO_COIN_ID[sym]

        # 3. Fallback to lowercase symbol or instrument scheme_code if present
        if instrument.symbol and instrument.symbol.lower() in SUPPORTED_COIN_IDS:
            return instrument.symbol.lower()

        return (instrument.symbol or '').strip().lower()

    def get_quote(self, instrument) -> QuoteData:
        coin_id = self._resolve_coin_id(instrument)
        vs_currency = getattr(settings, 'COINGECKO_QUOTE_CURRENCY', 'INR').lower()

        try:
            markets = self.client.get_markets(ids=[coin_id], vs_currency=vs_currency)
            if not markets:
                raise CoinGeckoError(f"No market data returned for coin ID: {coin_id}")
            item = serialize_market_item(markets[0])
            vol_int = int(item['total_volume']) if item['total_volume'] is not None else None

            return QuoteData(
                symbol=instrument.symbol,
                price=item['price'],
                high_price=item['high_24h'],
                low_price=item['low_24h'],
                close_price=item['price'],
                volume=vol_int,
                change_amount=item['price_change_24h'],
                change_percent=item['price_change_percentage_24h'],
                timestamp=item['timestamp'],
                provider=self.provider_name,
                is_synthetic=False,
                currency=vs_currency.upper(),
            )
        except Exception as e:
            logger.error("Failed to fetch quote for %s from CoinGecko: %s", instrument.symbol, str(e))
            raise

    def get_quotes(self, instruments: List[Any]) -> Dict[str, QuoteData]:
        if not instruments:
            return {}
        coin_map = {self._resolve_coin_id(inst): inst for inst in instruments}
        vs_currency = getattr(settings, 'COINGECKO_QUOTE_CURRENCY', 'INR').lower()

        try:
            markets = self.client.get_markets(ids=list(coin_map.keys()), vs_currency=vs_currency)
            results = {}
            for raw in markets:
                try:
                    item = serialize_market_item(raw)
                    cid = item['id'].lower()
                    inst = coin_map.get(cid)
                    if inst:
                        vol_int = int(item['total_volume']) if item['total_volume'] is not None else None
                        results[inst.symbol] = QuoteData(
                            symbol=inst.symbol,
                            price=item['price'],
                            high_price=item['high_24h'],
                            low_price=item['low_24h'],
                            close_price=item['price'],
                            volume=vol_int,
                            change_amount=item['price_change_24h'],
                            change_percent=item['price_change_percentage_24h'],
                            timestamp=item['timestamp'],
                            provider=self.provider_name,
                            is_synthetic=False,
                            currency=vs_currency.upper(),
                        )
                except Exception:
                    continue
            return results
        except Exception as e:
            logger.error("Failed bulk quote fetch from CoinGecko: %s", str(e))
            return super().get_quotes(instruments)

    def get_history(
        self,
        instrument,
        start_date: date,
        end_date: date,
        interval: str = '1D',
    ) -> List[HistoricalPoint]:
        coin_id = self._resolve_coin_id(instrument)
        vs_currency = getattr(settings, 'COINGECKO_QUOTE_CURRENCY', 'INR').lower()
        days_span = max(1, (end_date - start_date).days + 1)

        raw_chart = self.client.get_market_chart(
            coin_id=coin_id,
            days=days_span,
            vs_currency=vs_currency,
            interval='daily',
        )
        points_data = serialize_chart_data(raw_chart)

        historical_points = []
        start_dt = datetime(start_date.year, start_date.month, start_date.day, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)

        prev_price = None
        for p in points_data:
            dt = p['timestamp']
            if dt < start_dt or dt > end_dt:
                continue
            curr_price = p['price']
            vol_int = int(p['volume']) if p['volume'] is not None else None
            change_amt = (curr_price - prev_price) if prev_price is not None else None
            change_pct = ((curr_price - prev_price) / prev_price * Decimal('100')) if prev_price and prev_price > 0 else None
            prev_price = curr_price

            historical_points.append(
                HistoricalPoint(
                    timestamp=dt,
                    price=curr_price,
                    open_price=curr_price,
                    high_price=curr_price,
                    low_price=curr_price,
                    close_price=curr_price,
                    volume=vol_int,
                    change_amount=change_amt,
                    change_percent=change_pct,
                )
            )

        return historical_points

    def health_check(self) -> ProviderHealth:
        enabled = getattr(settings, 'COINGECKO_ENABLED', True)
        if not enabled:
            return ProviderHealth(
                name=self.provider_name,
                is_available=False,
                last_checked=datetime.now(timezone.utc),
                message='CoinGecko provider is disabled by configuration.',
                mode='PRODUCTION',
                metadata={'enabled': False},
            )

        api_key = getattr(settings, 'COINGECKO_API_KEY', '')
        if not api_key:
            return ProviderHealth(
                name=self.provider_name,
                is_available=False,
                last_checked=datetime.now(timezone.utc),
                message='CoinGecko API key is not configured in backend settings.',
                mode='PRODUCTION',
                metadata={'configured': False, 'credentials_present': False},
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
                    message='CoinGecko Demo API online and authenticated.',
                    mode='PRODUCTION',
                    metadata={'base_url': self.client.base_url, 'authenticated': True},
                )
            return ProviderHealth(
                name=self.provider_name,
                is_available=False,
                latency_ms=latency,
                last_checked=datetime.now(timezone.utc),
                message='CoinGecko ping returned unexpected payload.',
                mode='PRODUCTION',
            )
        except Exception as e:
            latency = round((time.perf_counter() - t0) * 1000, 2)
            return ProviderHealth(
                name=self.provider_name,
                is_available=False,
                latency_ms=latency,
                last_checked=datetime.now(timezone.utc),
                message=f'CoinGecko health check failed: {e!s}',
                mode='PRODUCTION',
            )
