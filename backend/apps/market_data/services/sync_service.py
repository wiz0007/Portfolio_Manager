import logging
from typing import Any, Dict, List

from django.utils import timezone

from apps.market_data.models.instrument import Instrument
from apps.market_data.models.instrument_reference import MarketInstrumentReference
from apps.market_data.models.sync_event import InstrumentSyncEvent, SyncEventStatus

logger = logging.getLogger(__name__)


class InstrumentIdentitySyncService:
    """
    Controlled synchronization service between Canonical Instrument Identity
    (Primary Portfolio Database) and MarketInstrumentReference (Market Data Storage Database).

    Uses a durable outbox pattern (InstrumentSyncEvent) with monotonic identity versioning
    and strict target database routing (no silent fallback to 'default').
    """

    TARGET_DB = 'market_data'
    SOURCE_DB = 'default'

    @classmethod
    def _target_db(cls) -> str:
        """Returns the market data database alias strictly."""
        return cls.TARGET_DB

    @classmethod
    def record_sync_event(cls, instrument: Instrument) -> InstrumentSyncEvent:
        """
        Creates an outbox event in the Primary Database ('default') inside the
        same transaction as the canonical instrument mutation.
        """
        payload = {
            'symbol': instrument.symbol,
            'name': instrument.name,
            'asset_class': instrument.asset_class,
            'product_type': instrument.product_type or '',
            'exchange': instrument.exchange or '',
            'currency': instrument.currency or 'INR',
            'isin': instrument.isin,
            'scheme_code': instrument.scheme_code,
            'security_code': instrument.security_code,
            'is_active': instrument.is_active,
            'identity_version': instrument.identity_version or 1,
        }
        event = InstrumentSyncEvent.objects.using(cls.SOURCE_DB).create(
            instrument_id=instrument.id,
            identity_version=instrument.identity_version or 1,
            payload=payload,
            status=SyncEventStatus.PENDING,
        )
        # Attempt immediate dispatch if market_data database is available
        try:
            cls.apply_sync_event(event)
        except Exception as e:
            logger.warning("Immediate outbox sync dispatch failed for %s, will retry in background: %s", instrument.symbol, e)
        return event

    @classmethod
    def apply_sync_event(cls, event: InstrumentSyncEvent) -> bool:
        """
        Idempotently applies an outbox sync event to Market Data Storage.
        Guarantees that an older event never overwrites a newer projection version.
        """
        target_db = cls._target_db()
        payload = event.payload
        inst_id = event.instrument_id
        target_version = event.identity_version

        existing = MarketInstrumentReference.objects.using(target_db).filter(id=inst_id).first()
        if existing and existing.sync_version > target_version:
            # Newer version already synchronized; mark this event as processed
            event.status = SyncEventStatus.PROCESSED
            event.processed_at = timezone.now()
            event.save(using=cls.SOURCE_DB)
            return True

        MarketInstrumentReference.objects.using(target_db).update_or_create(
            id=inst_id,
            defaults={
                'symbol': payload['symbol'],
                'name': payload['name'],
                'asset_class': payload['asset_class'],
                'product_type': payload['product_type'],
                'exchange': payload['exchange'],
                'currency': payload['currency'],
                'isin': payload['isin'],
                'scheme_code': payload['scheme_code'],
                'security_code': payload['security_code'],
                'is_active': payload['is_active'],
                'sync_version': target_version,
            },
        )
        event.status = SyncEventStatus.PROCESSED
        event.processed_at = timezone.now()
        event.save(using=cls.SOURCE_DB)
        return True

    @classmethod
    def process_pending_sync_events(cls, limit: int = 100) -> Dict[str, int]:
        """Processes pending or failed sync outbox events."""
        pending_events = (
            InstrumentSyncEvent.objects.using(cls.SOURCE_DB)
            .filter(status__in=[SyncEventStatus.PENDING, SyncEventStatus.FAILED])
            .order_by('created_at')[:limit]
        )
        processed = 0
        failed = 0

        for event in pending_events:
            try:
                event.attempts += 1
                cls.apply_sync_event(event)
                processed += 1
            except Exception as e:
                event.status = SyncEventStatus.FAILED
                event.last_error = str(e)
                event.save(using=cls.SOURCE_DB)
                failed += 1

        return {'processed': processed, 'failed': failed}

    @classmethod
    def sync_instrument(cls, instrument: Instrument) -> MarketInstrumentReference:
        """Direct idempotent sync helper used in management commands and test suites."""
        target_db = cls._target_db()
        current_version = getattr(instrument, 'identity_version', 1) or 1

        ref, _ = MarketInstrumentReference.objects.using(target_db).update_or_create(
            id=instrument.id,
            defaults={
                'symbol': instrument.symbol,
                'name': instrument.name,
                'asset_class': instrument.asset_class,
                'product_type': instrument.product_type or '',
                'exchange': instrument.exchange or '',
                'currency': instrument.currency or 'INR',
                'isin': instrument.isin,
                'scheme_code': instrument.scheme_code,
                'security_code': instrument.security_code,
                'is_active': instrument.is_active,
                'sync_version': current_version,
            },
        )
        return ref

    @classmethod
    def reconcile_all(cls, batch_size: int = 500) -> Dict[str, Any]:
        """
        Full field-level reconciliation pass:
        Compares actual canonical attributes against projection attributes.
        Does NOT increment versions when data is already identical.
        """
        target_db = cls._target_db()
        canonical_qs = Instrument.objects.using(cls.SOURCE_DB).all()
        total_canonical = canonical_qs.count()

        existing_refs = {
            ref.id: ref
            for ref in MarketInstrumentReference.objects.using(target_db).all()
        }

        to_create: List[MarketInstrumentReference] = []
        to_update: List[MarketInstrumentReference] = []

        for inst in canonical_qs.iterator(chunk_size=batch_size):
            ref = existing_refs.get(inst.id)
            if not ref:
                to_create.append(
                    MarketInstrumentReference(
                        id=inst.id,
                        symbol=inst.symbol,
                        name=inst.name,
                        asset_class=inst.asset_class,
                        product_type=inst.product_type or '',
                        exchange=inst.exchange or '',
                        currency=inst.currency or 'INR',
                        isin=inst.isin,
                        scheme_code=inst.scheme_code,
                        security_code=inst.security_code,
                        is_active=inst.is_active,
                        sync_version=inst.identity_version or 1,
                    )
                )
            else:
                # Compare actual field values before updating
                has_diff = (
                    ref.symbol != inst.symbol
                    or ref.name != inst.name
                    or ref.asset_class != inst.asset_class
                    or ref.product_type != (inst.product_type or '')
                    or ref.exchange != (inst.exchange or '')
                    or ref.currency != (inst.currency or 'INR')
                    or ref.isin != inst.isin
                    or ref.scheme_code != inst.scheme_code
                    or ref.security_code != inst.security_code
                    or ref.is_active != inst.is_active
                )
                if has_diff:
                    ref.symbol = inst.symbol
                    ref.name = inst.name
                    ref.asset_class = inst.asset_class
                    ref.product_type = inst.product_type or ''
                    ref.exchange = inst.exchange or ''
                    ref.currency = inst.currency or 'INR'
                    ref.isin = inst.isin
                    ref.scheme_code = inst.scheme_code
                    ref.security_code = inst.security_code
                    ref.is_active = inst.is_active
                    ref.sync_version = max(ref.sync_version, inst.identity_version or 1)
                    to_update.append(ref)

        if to_create:
            MarketInstrumentReference.objects.using(target_db).bulk_create(
                to_create,
                batch_size=batch_size,
                ignore_conflicts=True,
            )
        if to_update:
            MarketInstrumentReference.objects.using(target_db).bulk_update(
                to_update,
                fields=[
                    'symbol',
                    'name',
                    'asset_class',
                    'product_type',
                    'exchange',
                    'currency',
                    'isin',
                    'scheme_code',
                    'security_code',
                    'is_active',
                    'sync_version',
                ],
                batch_size=batch_size,
            )

        synced_total = MarketInstrumentReference.objects.using(target_db).count()
        return {
            'target_db': target_db,
            'total_canonical': total_canonical,
            'synced_total': synced_total,
            'created': len(to_create),
            'updated': len(to_update),
            'status': 'SYNCHRONIZED' if synced_total >= total_canonical else 'DISCREPANCY_DETECTED',
        }
