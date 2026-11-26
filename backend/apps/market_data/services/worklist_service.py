import csv
import io
import logging
from datetime import date, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

from django.db import transaction
from django.utils import timezone as dj_timezone

from apps.market_data.models.instrument import Instrument
from apps.market_data.models.coverage import (
    CollectionCadence,
    CoverageStatus,
    InstrumentCoverage,
)
from apps.market_data.models.observation import ObservationStatus, PriceObservation, TrustClass
from apps.market_data.models.series import MarketDataSeries
from apps.market_data.models.worklist import (
    DueReason,
    MarketDataWorklist,
    MarketDataWorklistItem,
    WorklistItemStatus,
    WorklistStatus,
)

logger = logging.getLogger(__name__)


def sanitize_csv_cell(value: str) -> str:
    """Neutralizes spreadsheet formula injection (=, +, -, @, \\t, \\r)."""
    if not value:
        return ''
    s = str(value)
    if s.startswith(('=', '+', '-', '@', '\t', '\r')):
        return f"'{s}"
    return s


# No year-specific official exchange calendar is bundled. This fallback excludes
# weekends only and explicitly records that official holidays are not verified.



class MarketDataWorklistService:
    """
    Deterministic daily worklist generation, management, and export service.
    Atomic on secondary database ('market_data'), holiday-aware, and strictly idempotent.
    """

    @classmethod
    def is_trading_day(cls, target_date: date) -> bool:
        """Weekday-only fallback; official exchange holidays are not verified here."""
        # Saturday is 5, Sunday is 6
        if target_date.weekday() >= 5:
            return False
        return True

    @classmethod
    @transaction.atomic(using='market_data')
    def generate_worklist(cls, target_date: Optional[date] = None) -> MarketDataWorklist:
        """
        Generates or updates the daily collection worklist for the target calendar date.
        Strictly idempotent: Preserves completed and skipped operational work on reruns.
        """
        target_date = target_date or dj_timezone.now().astimezone(ZoneInfo('Asia/Kolkata')).date()
        is_market_open = cls.is_trading_day(target_date)

        worklist, _created = MarketDataWorklist.objects.using('market_data').get_or_create(
            worklist_date=target_date,
            defaults={
                'status': WorklistStatus.GENERATED,
                'metadata': {'is_trading_day': is_market_open, 'calendar_source': 'WEEKDAY_FALLBACK', 'official_holiday_check': False},
            },
        )

        active_coverages = list(InstrumentCoverage.objects.using('market_data').filter(
            status=CoverageStatus.ACTIVE,
        ))
        instrument_map = {
            instrument.id: instrument
            for instrument in Instrument.objects.filter(id__in=[cov.instrument_id for cov in active_coverages])
        }

        items_created = 0

        for cov in active_coverages:
            inst = instrument_map.get(cov.instrument_id)
            if inst is None:
                logger.warning('Skipping coverage with missing canonical instrument %s', cov.instrument_id)
                continue
            due_reason = None

            # 1. Resolve one exact series; never combine providers or quotation bases.
            series_qs = MarketDataSeries.objects.using('market_data').filter(
                instrument_id=cov.instrument_id, is_active=True,
                price_type=cov.price_type, currency=cov.currency, unit=cov.unit,
            )
            preferred = list(series_qs.filter(source=cov.preferred_source)[:2])
            candidates = preferred if preferred else list(series_qs.order_by('id')[:2])
            if len(candidates) == 0:
                series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
                    instrument_id=cov.instrument_id,
                    exchange=inst.exchange or '',
                    source=cov.preferred_source or 'MANUAL',
                    price_type=cov.price_type,
                    currency=cov.currency,
                    unit=cov.unit,
                    defaults={'is_active': True, 'description': f'Default series for {inst.symbol}'}
                )
                candidates = [series]
            if len(candidates) != 1:
                logger.warning('Skipping worklist item for %s: expected one exact series, found %s', cov.instrument_id, len(candidates))
                continue
            series = candidates[0]
            latest_published = PriceObservation.objects.using('market_data').filter(
                instrument_id=cov.instrument_id, series_id=series.id,
                status=ObservationStatus.PUBLISHED, is_synthetic=False,
                trust_class__in=[TrustClass.VERIFIED_OFFICIAL, TrustClass.VERIFIED_PERMITTED_SECONDARY, TrustClass.MANUAL_VERIFIED, TrustClass.CORRECTED],
            ).exclude(corrections__status=ObservationStatus.PUBLISHED).order_by('-effective_at').first()

            if not latest_published:
                due_reason = DueReason.FIRST_PRICE
            elif cov.cadence == CollectionCadence.EVERY_TRADING_DAY:
                if is_market_open:
                    due_reason = DueReason.DUE_TODAY
                else:
                    due_reason = DueReason.SKIPPED_HOLIDAY
            elif cov.cadence == CollectionCadence.EVERY_BUSINESS_DAY:
                if target_date.weekday() < 5:
                    due_reason = DueReason.DUE_TODAY
            elif cov.cadence == CollectionCadence.WEEKLY:
                # Due on Friday or end of week
                if target_date.weekday() == 4:
                    due_reason = DueReason.DUE_TODAY
            elif cov.cadence == CollectionCadence.MONTHLY:
                # Due on last day of month
                tomorrow = target_date + timedelta(days=1)
                if tomorrow.month != target_date.month:
                    due_reason = DueReason.DUE_TODAY
            elif cov.cadence == CollectionCadence.ON_DEMAND:
                # Only if stale
                pass

            # Stale check
            if latest_published and cov.freshness_hours:
                cutoff = dj_timezone.now() - timedelta(hours=cov.freshness_hours)
                if latest_published.effective_at < cutoff and is_market_open:
                    due_reason = DueReason.STALE

            if not due_reason:
                continue

            existing_item = MarketDataWorklistItem.objects.using('market_data').filter(
                worklist=worklist,
                instrument_id=inst.id if inst else cov.instrument_id,
            ).first()

            if existing_item and existing_item.status in (
                WorklistItemStatus.COMPLETED, WorklistItemStatus.SKIPPED,
            ):
                # Preserve terminal operational work on deterministic regeneration.
                continue

            last_price = latest_published.value if latest_published else None
            last_dt = latest_published.effective_at if latest_published else None

            _item, item_created = MarketDataWorklistItem.objects.using('market_data').update_or_create(
                worklist=worklist,
                instrument_id=cov.instrument_id,
                defaults={
                    'coverage': cov,
                    'canonical_name': inst.name if inst else cov.symbol,
                    'symbol': inst.symbol if inst else cov.symbol,
                    'exchange': (inst.exchange or '') if inst else '',
                    'isin': inst.isin if inst else None,
                    'asset_class': inst.asset_class if inst else 'EQUITY',
                    'product_type': inst.product_type if inst else '',
                    'expected_price_type': cov.price_type,
                    'currency': cov.currency,
                    'unit': cov.unit,
                    'effective_date': target_date,
                    'due_reason': due_reason,
                    'status': (
                        WorklistItemStatus.SKIPPED
                        if due_reason == DueReason.SKIPPED_HOLIDAY
                        else WorklistItemStatus.PENDING
                    ),
                    'last_published_price': last_price,
                    'last_published_date': last_dt,
                    'source_guidance': cov.preferred_source,
                    'notes': cov.notes,
                },
            )
            if item_created:
                items_created += 1

        worklist.total_items = worklist.items.using('market_data').count()
        worklist.completed_items = worklist.items.using('market_data').filter(status=WorklistItemStatus.COMPLETED).count()
        worklist.save(using='market_data')

        return worklist

    @classmethod
    def export_to_markdown(cls, worklist: MarketDataWorklist) -> str:
        """
        Renders the worklist as a structured GitHub-Flavored Markdown table.
        """
        lines = [
            f"# Market Data Collection Worklist — {worklist.worklist_date.isoformat()}",
            f"**Status:** {worklist.status} | **Total Items:** {worklist.total_items} | **Completed:** {worklist.completed_items}",
            f"**Generated At:** {worklist.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "| Item ID | Symbol | Instrument Name | Class | Exchange | Price Type | Unit | Due Reason | Status | Guidance |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]

        for item in worklist.items.all().order_by('asset_class', 'symbol'):
            item_id_short = str(item.id)[:8]
            lines.append(
                f"| `{item_id_short}` | **{item.symbol}** | {item.canonical_name} | {item.asset_class} | {item.exchange or '-'} | {item.expected_price_type} | {item.unit} | {item.due_reason} | {item.status} | {item.source_guidance} |"
            )

        lines.append("")
        lines.append("---")
        lines.append("*Generated by Portfolio Manager Central Market Data Operations*")
        return "\n".join(lines)

    @classmethod
    def export_to_csv(cls, worklist: MarketDataWorklist) -> str:
        """
        Renders the worklist in versioned CSV schema with formula-injection defenses.
        Schema:
        schema_version,worklist_item_id,instrument_id,price_type,value,currency,unit,effective_at,source_id,source_reference,notes
        """
        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')
        headers = [
            'schema_version',
            'worklist_item_id',
            'instrument_id',
            'series_id',
            'symbol',
            'price_type',
            'value',
            'reference_price',
            'target_market_date',
            'currency',
            'unit',
            'effective_at',
            'source_id',
            'source_reference',
            'notes',
        ]
        writer.writerow(headers)

        items = list(worklist.items.all().order_by('asset_class', 'symbol'))
        series_by_instrument = {}
        for series in MarketDataSeries.objects.using('market_data').filter(
            instrument_id__in=[item.instrument_id for item in items], is_active=True
        ).order_by('id'):
            series_by_instrument.setdefault(series.instrument_id, []).append(series)

        for item in items:
            matching_series = [series for series in series_by_instrument.get(item.instrument_id, [])
                               if series.price_type == item.expected_price_type
                               and series.currency == item.currency and series.unit == item.unit][:2]
            exact_series = matching_series[0] if len(matching_series) == 1 else None
            row = [
                '1.0',
                str(item.id),
                str(item.instrument_id),
                str(exact_series.id) if exact_series else '',
                sanitize_csv_cell(item.symbol),
                item.expected_price_type,
                '',  # Operator must enter a newly collected value.
                str(item.last_published_price) if item.last_published_price is not None else '',
                worklist.worklist_date.isoformat(),
                item.currency,
                item.unit,
                '',  # Actual source timestamp must be supplied; never fabricate one.
                sanitize_csv_cell(exact_series.source if exact_series else ''),
                '',
                sanitize_csv_cell(item.notes),
            ]
            writer.writerow(row)

        return output.getvalue()
