import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from apps.market_data.models.instrument import Instrument, InstrumentStatus
from apps.market_data.services.movement_service import PriceMovementService
from apps.market_data.services.price_resolver import PriceResolver
from apps.watchlists.models import WatchlistItem

User = get_user_model()


class WatchlistService:
    """
    Domain service for managing user personal watchlists.
    Enforces user isolation, database uniqueness, and annotates items
    with live published market data from the central PriceResolver.
    Never persists prices inside user watchlist records.
    """

    @classmethod
    def add_item(
        cls,
        user: Any,
        instrument_id: uuid.UUID | str,
        notes: str = '',
        target_price: Optional[Decimal] = None,
    ) -> WatchlistItem:
        try:
            instrument = Instrument.objects.get(pk=instrument_id)
        except (Instrument.DoesNotExist, ValueError):
            raise ObjectDoesNotExist(f"Instrument with id {instrument_id} does not exist.")

        if not instrument.is_active or instrument.status != InstrumentStatus.ACTIVE:
            raise ValidationError(
                f"Instrument {instrument.symbol} is inactive or unapproved and cannot be watched."
            )

        if WatchlistItem.objects.filter(user=user, instrument=instrument).exists():
            raise ValidationError("Instrument is already in your watchlist.")

        if target_price is not None and target_price <= Decimal('0'):
            raise ValidationError({'target_price': 'Target price must be strictly positive.'})

        item = WatchlistItem(
            user=user,
            instrument=instrument,
            notes=notes or '',
            target_price=target_price,
        )
        item.save()
        return item

    @classmethod
    def remove_item(cls, user: Any, item_id: uuid.UUID | str) -> bool:
        try:
            item = WatchlistItem.objects.get(pk=item_id, user=user)
        except (WatchlistItem.DoesNotExist, ValueError):
            raise ObjectDoesNotExist(f"Watchlist item with id {item_id} not found for this user.")

        item.delete()
        return True

    @classmethod
    def get_annotated_item_data(cls, item: WatchlistItem) -> Dict[str, Any]:
        inst = item.instrument
        resolved = PriceResolver.resolve_price(inst)
        movement = PriceMovementService.calculate_movement(
            instrument=inst,
            current_price=resolved.price,
            current_dt=resolved.effective_at,
            currency=resolved.currency,
            unit=resolved.unit,
        )

        ref_data = getattr(inst, 'reference_data', None)

        return {
            'id': str(item.id),
            'instrument': {
                'id': str(inst.id),
                'symbol': inst.symbol,
                'name': inst.name,
                'asset_class': inst.asset_class,
                'product_type': inst.product_type,
                'exchange': inst.exchange,
                'currency': inst.currency,
                'isin': inst.isin,
                'scheme_code': inst.scheme_code,
                'sector': getattr(ref_data, 'sector', ''),
                'industry': getattr(ref_data, 'industry', ''),
                'status': inst.status,
            },
            'notes': item.notes,
            'target_price': str(item.target_price) if item.target_price is not None else None,
            'created_at': item.created_at.isoformat(),
            'updated_at': item.updated_at.isoformat(),
            'market_data': {
                'price': str(resolved.price) if resolved.price is not None else None,
                'currency': resolved.currency,
                'unit': resolved.unit,
                'effective_at': resolved.effective_at.isoformat() if resolved.effective_at else None,
                'status': resolved.status,
                'source': resolved.source,
                'source_reference': resolved.source_reference,
                'is_synthetic': resolved.is_synthetic,
                'notes': resolved.notes,
                'movement': {
                    'change_amount': str(movement.change_amount) if movement.change_amount is not None else None,
                    'change_percent': str(movement.change_percent) if movement.change_percent is not None else None,
                    'previous_price': str(movement.previous_price) if movement.previous_price is not None else None,
                    'previous_effective_at': movement.previous_effective_at.isoformat() if movement.previous_effective_at else None,
                    'status': movement.status,
                    'notes': movement.notes,
                },
            },
        }

    @classmethod
    def list_items(cls, user: Any) -> List[Dict[str, Any]]:
        items = (
            WatchlistItem.objects.filter(user=user)
            .select_related('instrument', 'instrument__reference_data', 'instrument__coverage')
            .order_by('-created_at')
        )
        return [cls.get_annotated_item_data(item) for item in items]

    @classmethod
    def get_item(cls, user: Any, item_id: uuid.UUID | str) -> Dict[str, Any]:
        try:
            item = (
                WatchlistItem.objects.filter(user=user, pk=item_id)
                .select_related('instrument', 'instrument__reference_data', 'instrument__coverage')
                .get()
            )
        except (WatchlistItem.DoesNotExist, ValueError):
            raise ObjectDoesNotExist(f"Watchlist item with id {item_id} not found for this user.")

        return cls.get_annotated_item_data(item)
