import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db import transaction

from apps.market_data.models.instrument import Instrument
from apps.market_data.models.market_data_point import MarketDataPoint
from apps.market_data.providers.registry import provider_registry

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Core service for managing, persisting, caching, and serving financial market data.
    """

    FRESHNESS_MINUTES = 15

    @classmethod
    def is_fresh(cls, point: Optional[MarketDataPoint]) -> bool:
        if not point or not point.timestamp:
            return False
        now_utc = datetime.now(timezone.utc)
        return (now_utc - point.timestamp) <= timedelta(minutes=cls.FRESHNESS_MINUTES)

    @classmethod
    def get_latest_quote(
        cls,
        instrument: Instrument,
        force_refresh: bool = False,
    ) -> MarketDataPoint:
        """
        Retrieves the latest quote for the instrument.
        If fresh quote exists in DB and force_refresh is False, returns DB quote.
        Otherwise fetches normalized quote from provider and persists it.
        """
        latest = instrument.latest_quote
        if latest and not force_refresh and cls.is_fresh(latest):
            return latest

        provider = provider_registry.get_provider_for_instrument(instrument)
        quote_data = provider.get_quote(instrument)

        # Save to database
        point = cls.persist_quote(instrument, quote_data)
        return point

    @classmethod
    @transaction.atomic
    def persist_quote(cls, instrument: Instrument, quote_data) -> MarketDataPoint:
        """Saves a normalized quote to MarketDataPoint."""
        # Use update_or_create on unique tuple: (instrument, timestamp, interval, provider)
        point, _ = MarketDataPoint.objects.update_or_create(
            instrument=instrument,
            timestamp=quote_data.timestamp,
            interval='1D',
            provider=quote_data.provider,
            defaults={
                'price': quote_data.price,
                'open_price': quote_data.open_price,
                'high_price': quote_data.high_price,
                'low_price': quote_data.low_price,
                'close_price': quote_data.close_price,
                'volume': quote_data.volume,
                'change_amount': quote_data.change_amount,
                'change_percent': quote_data.change_percent,
                'is_synthetic': quote_data.is_synthetic,
            },
        )
        return point

    @classmethod
    def get_history(
        cls,
        instrument: Instrument,
        start_date: date,
        end_date: date,
        interval: str = '1D',
    ) -> List[MarketDataPoint]:
        """
        Retrieves historical timeseries for an instrument.
        Populates missing ranges via provider if needed.
        """
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

        existing = list(
            MarketDataPoint.objects.filter(
                instrument=instrument,
                interval=interval,
                timestamp__gte=start_dt,
                timestamp__lte=end_dt,
            ).order_by('timestamp')
        )

        # If data is empty or sparse, fetch from provider
        if len(existing) < 5:
            provider = provider_registry.get_provider_for_instrument(instrument)
            points = provider.get_history(instrument, start_date, end_date, interval)

            with transaction.atomic():
                for p in points:
                    MarketDataPoint.objects.update_or_create(
                        instrument=instrument,
                        timestamp=p.timestamp,
                        interval=interval,
                        provider=provider.provider_name,
                        defaults={
                            'price': p.price,
                            'open_price': p.open_price,
                            'high_price': p.high_price,
                            'low_price': p.low_price,
                            'close_price': p.close_price,
                            'volume': p.volume,
                            'change_amount': p.change_amount,
                            'change_percent': p.change_percent,
                            'is_synthetic': getattr(provider, 'provider_name', '') == 'DEMO',
                        },
                    )

            existing = list(
                MarketDataPoint.objects.filter(
                    instrument=instrument,
                    interval=interval,
                    timestamp__gte=start_dt,
                    timestamp__lte=end_dt,
                ).order_by('timestamp')
            )

        return existing

    @classmethod
    def get_market_overview(cls) -> Dict[str, Any]:
        """Provides high-level market summary for dashboard overview."""
        indices = Instrument.objects.filter(asset_class='INDEX', is_active=True)[:5]
        equities = Instrument.objects.filter(asset_class='EQUITY', is_active=True)[:8]
        mutual_funds = Instrument.objects.filter(asset_class='MUTUAL_FUND', is_active=True)[:6]

        def format_inst(inst: Instrument):
            quote = cls.get_latest_quote(inst)
            return {
                'id': str(inst.id),
                'symbol': inst.symbol,
                'name': inst.name,
                'asset_class': inst.asset_class,
                'exchange': inst.exchange,
                'price': str(quote.price),
                'change_amount': str(quote.change_amount) if quote.change_amount is not None else '0.0000',
                'change_percent': str(quote.change_percent) if quote.change_percent is not None else '0.0000',
                'is_synthetic': quote.is_synthetic,
                'timestamp': quote.timestamp.isoformat(),
            }

        return {
            'indices': [format_inst(i) for i in indices],
            'equities': [format_inst(e) for e in equities],
            'mutual_funds': [format_inst(m) for m in mutual_funds],
            'is_demo_mode': getattr(settings, 'MARKET_DATA_PROVIDER_MODE', 'DEMO') == 'DEMO',
            'demo_notice': 'DEMO DATA — Synthetic prices, not live market quotations.',
        }
