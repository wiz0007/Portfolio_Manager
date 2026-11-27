import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.exceptions import ValidationError

from apps.market_data.models.instrument import Instrument
from apps.market_data.providers.registry import provider_registry
from apps.market_data.services.history_service import MarketHistoryService
from apps.market_data.services.movement_service import PriceMovementService
from apps.market_data.services.price_resolver import PriceResolver

logger = logging.getLogger(__name__)


@dataclass
class ResolvedQuote:
    id: Optional[str]
    instrument_id: str
    instrument: Instrument
    price: Optional[Decimal]
    open_price: Optional[Decimal]
    high_price: Optional[Decimal]
    low_price: Optional[Decimal]
    close_price: Optional[Decimal]
    volume: Optional[int]
    change_amount: Optional[Decimal]
    change_percent: Optional[Decimal]
    provider: str
    is_synthetic: bool
    interval: str
    timestamp: Optional[datetime]
    currency: str
    status: str
    notes: str = ''


class MarketDataService:
    """Compatibility facade over the authoritative PriceObservation resolver."""

    @classmethod
    def is_fresh(cls, point) -> bool:
        if not point or not point.timestamp:
            return False
        return point.timestamp <= datetime.now(timezone.utc)

    @classmethod
    def get_latest_quote(cls, instrument: Instrument, force_refresh: bool = False) -> ResolvedQuote:
        # Provider responses are not silently promoted to published observations.
        resolved = PriceResolver.resolve_price(instrument)
        if resolved.price is not None:
            movement = PriceMovementService.calculate_movement(
                instrument=instrument, current_price=resolved.price,
                current_dt=resolved.effective_at, price_type=resolved.price_type,
                currency=resolved.currency, unit=resolved.unit, series_id=resolved.series_id,
            )
            return ResolvedQuote(
                id=resolved.observation_id, instrument_id=str(instrument.id), instrument=instrument,
                price=resolved.price, open_price=None, high_price=None, low_price=None,
                close_price=resolved.price, volume=None,
                change_amount=movement.change_amount, change_percent=movement.change_percent,
                provider=resolved.source, is_synthetic=resolved.is_synthetic,
                interval='1D', timestamp=resolved.effective_at, currency=resolved.currency,
                status=resolved.status, notes=resolved.notes,
            )

        from apps.market_data.models.market_data_point import MarketDataPoint
        legacy = MarketDataPoint.objects.using('market_data').filter(instrument_id=instrument.id).order_by('-timestamp').first()
        if legacy and legacy.price is not None:
            return ResolvedQuote(
                id=str(legacy.id),
                instrument_id=str(instrument.id),
                instrument=instrument,
                price=legacy.price,
                open_price=legacy.open_price,
                high_price=legacy.high_price,
                low_price=legacy.low_price,
                close_price=legacy.close_price or legacy.price,
                volume=legacy.volume,
                change_amount=legacy.change_amount,
                change_percent=legacy.change_percent,
                provider=legacy.provider,
                is_synthetic=legacy.is_synthetic,
                interval=legacy.interval or '1D',
                timestamp=legacy.timestamp,
                currency=instrument.currency,
                status='AVAILABLE',
                notes='Legacy market data point.',
            )

        if getattr(settings, 'MARKET_DATA_PROVIDER_MODE', 'DEMO') == 'DEMO':
            provider = provider_registry.get_provider_for_instrument(instrument)
            if provider and getattr(provider, 'provider_name', '') == 'DEMO':
                quote_data = provider.get_quote(instrument)
                return ResolvedQuote(
                    id=None,
                    instrument_id=str(instrument.id),
                    instrument=instrument,
                    price=quote_data.price,
                    open_price=quote_data.open_price,
                    high_price=quote_data.high_price,
                    low_price=quote_data.low_price,
                    close_price=quote_data.close_price,
                    volume=quote_data.volume,
                    change_amount=quote_data.change_amount,
                    change_percent=quote_data.change_percent,
                    provider='DEMO',
                    is_synthetic=True,
                    interval='1D',
                    timestamp=quote_data.timestamp,
                    currency=instrument.currency,
                    status='AVAILABLE',
                    notes='Synthetic demo quote.',
                )

        movement = PriceMovementService.calculate_movement(
            instrument=instrument, current_price=None,
            current_dt=None, price_type=None,
            currency=instrument.currency, unit='UNITS', series_id=None,
        )
        return ResolvedQuote(
            id=None, instrument_id=str(instrument.id), instrument=instrument,
            price=None, open_price=None, high_price=None, low_price=None,
            close_price=None, volume=None,
            change_amount=movement.change_amount, change_percent=movement.change_percent,
            provider='NONE', is_synthetic=False,
            interval='1D', timestamp=None, currency=instrument.currency,
            status=resolved.status, notes=resolved.notes,
        )

    @classmethod
    def persist_quote(cls, instrument: Instrument, quote_data):
        raise ValidationError(
            'Direct MarketDataPoint quote persistence is deprecated. '
            'Create a PriceObservation through the review and publication workflow.'
        )

    @classmethod
    def get_history(cls, instrument: Instrument, start_date: date, end_date: date, interval: str = '1D') -> List[Any]:
        result = MarketHistoryService.get_history(
            instrument=instrument, start_date=start_date, end_date=end_date, interval=interval
        )
        return result.points

    @classmethod
    def get_market_overview(cls) -> Dict[str, Any]:
        indices = list(Instrument.objects.filter(asset_class='INDEX', is_active=True)[:5])
        equities = list(Instrument.objects.filter(asset_class='EQUITY', is_active=True)[:8])
        mutual_funds = list(Instrument.objects.filter(asset_class='MUTUAL_FUND', is_active=True)[:8])
        cryptos = list(Instrument.objects.filter(asset_class='CRYPTO', is_active=True)[:10])
        all_instruments = indices + equities + mutual_funds + cryptos
        resolved_map = PriceResolver.resolve_prices_bulk(all_instruments)
        movement_map = PriceMovementService.calculate_movements_bulk(resolved_map)

        import json

        def format_inst(inst):
            resolved = resolved_map.get(inst.id)
            movement = movement_map.get(inst.id)
            available = bool(resolved and resolved.price is not None)

            extra_meta = {}
            if resolved and resolved.notes:
                try:
                    if isinstance(resolved.notes, str) and resolved.notes.strip().startswith('{'):
                        extra_meta = json.loads(resolved.notes)
                except Exception:
                    pass

            return {
                'id': str(inst.id), 'symbol': inst.symbol, 'name': inst.name,
                'asset_class': inst.asset_class, 'exchange': inst.exchange,
                'price': str(resolved.price) if available else 'N/A',
                'change_amount': str(movement.change_amount) if movement and movement.change_amount is not None else '0.0000',
                'change_percent': str(movement.change_percent) if movement and movement.change_percent is not None else '0.0000',
                'is_synthetic': bool(resolved and resolved.is_synthetic),
                'timestamp': resolved.effective_at.isoformat() if resolved and resolved.effective_at else None,
                'status': resolved.status if resolved else 'UNAVAILABLE',
                'series_id': resolved.series_id if resolved else None,
                'observation_id': resolved.observation_id if resolved else None,
                'data_version': resolved.data_version if resolved else None,
                'currency': resolved.currency if resolved else inst.currency,
                'unit': resolved.unit if resolved else None,
                'market_cap': extra_meta.get('market_cap'),
                'volume_24h': extra_meta.get('volume_24h'),
                'fund_house': extra_meta.get('fund_house'),
                'scheme_code': getattr(inst, 'scheme_code', None),
                'isin': getattr(inst, 'isin', None),
                'plan_type': extra_meta.get('plan_type'),
                'option_type': extra_meta.get('option_type'),
            }

        def safe_format(inst):
            try:
                return format_inst(inst)
            except Exception as exc:
                logger.warning('Market overview resolution failed for %s: %s', inst.symbol, exc)
                return {
                    'id': str(inst.id), 'symbol': inst.symbol, 'name': inst.name,
                    'asset_class': inst.asset_class, 'exchange': inst.exchange,
                    'price': 'N/A', 'change_amount': '0.0000', 'change_percent': '0.0000',
                    'is_synthetic': False, 'timestamp': None, 'status': 'UNAVAILABLE',
                }

        from django.conf import settings
        return {
            'indices': [safe_format(i) for i in indices],
            'equities': [safe_format(i) for i in equities],
            'mutual_funds': [safe_format(i) for i in mutual_funds],
            'cryptocurrencies': [safe_format(i) for i in cryptos],
            'is_demo_mode': getattr(settings, 'MARKET_DATA_PROVIDER_MODE', 'DEMO').upper() == 'DEMO',
            'demo_notice': 'DEMO DATA — Synthetic prices, not live market quotations.'
                if getattr(settings, 'MARKET_DATA_PROVIDER_MODE', 'DEMO').upper() == 'DEMO' else '',
        }
