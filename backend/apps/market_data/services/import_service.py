import csv
import io
import logging
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone as dj_timezone

from apps.market_data.models.import_batch import (
    ImportBatchStatus,
    PriceImportBatch,
    PriceImportRowError,
)
from apps.market_data.models.instrument import Instrument, InstrumentStatus
from apps.market_data.models.observation import ObservationStatus, PriceObservation, TrustClass
from apps.market_data.models.series import MarketDataSeries
from apps.market_data.models.worklist import MarketDataWorklistItem

logger = logging.getLogger(__name__)


def clean_cell(val: Any) -> str:
    if val is None:
        return ''
    s = str(val).strip()
    # Strip dangerous spreadsheet formula prefixes (=, @, \t, \r)
    # Never strip '-' or '+' as they are essential for numbers and normal text
    if s.startswith(('=', '@', '\t', '\r')):
        s = s.lstrip('=@\t\r').strip()
    return s


class PriceImportService:
    """
    Service for parsing, validating, previewing, and committing bulk CSV price observation uploads.
    """

    SUPPORTED_VERSIONS = {'1.0'}
    MAX_CONTENT_BYTES = 5 * 1024 * 1024
    MAX_ROWS = 5000

    @classmethod
    def preview_csv(cls, user, csv_content: str, filename: str = 'import.csv') -> Dict[str, Any]:
        """
        Parses and validates a CSV string without creating PriceObservation records.
        Returns detailed summary and row-level validation errors.
        """
        if len(csv_content.encode('utf-8')) > cls.MAX_CONTENT_BYTES:
            raise ValidationError('CSV exceeds the 5 MB upload limit.')
        reader = csv.DictReader(io.StringIO(csv_content))
        total_rows = 0
        valid_rows: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        seen_series_dates: set = set()
        instrument_cache = {}
        worklist_item_cache = {}
        coverage_cache = {}
        series_cache = {}

        now_utc = dj_timezone.now()

        for idx, raw_row in enumerate(reader, start=2):  # Header is line 1
            total_rows += 1
            if total_rows > cls.MAX_ROWS:
                raise ValidationError(f'CSV exceeds the {cls.MAX_ROWS} row limit.')
            row_errors = []

            schema_ver = clean_cell(raw_row.get('schema_version', '1.0'))
            if schema_ver not in cls.SUPPORTED_VERSIONS:
                row_errors.append({'field': 'schema_version', 'error': f"Unsupported schema version '{schema_ver}'. Expected '1.0'."})

            inst_id_raw = clean_cell(raw_row.get('instrument_id'))
            item_id_raw = clean_cell(raw_row.get('worklist_item_id'))
            instrument = None

            # Resolve instrument by ID or worklist item ID
            if inst_id_raw:
                try:
                    inst_uuid = uuid.UUID(inst_id_raw)
                    if inst_uuid not in instrument_cache:
                        instrument_cache[inst_uuid] = Instrument.objects.filter(id=inst_uuid).first()
                    instrument = instrument_cache[inst_uuid]
                except ValueError:
                    row_errors.append({'field': 'instrument_id', 'error': 'Invalid UUID format for instrument_id.'})
            elif item_id_raw:
                try:
                    item_uuid = uuid.UUID(item_id_raw)
                    if item_uuid not in worklist_item_cache:
                        worklist_item_cache[item_uuid] = MarketDataWorklistItem.objects.using('market_data').filter(id=item_uuid).first()
                    item = worklist_item_cache[item_uuid]
                    if item:
                        if item.instrument_id not in instrument_cache:
                            instrument_cache[item.instrument_id] = Instrument.objects.filter(id=item.instrument_id).first()
                        instrument = instrument_cache[item.instrument_id]
                except ValueError:
                    row_errors.append({'field': 'worklist_item_id', 'error': 'Invalid UUID format for worklist_item_id.'})

            if not instrument and not row_errors:
                row_errors.append({'field': 'instrument_id', 'error': 'Instrument not found in canonical catalogue.'})
            elif instrument and instrument.status != InstrumentStatus.ACTIVE:
                row_errors.append({'field': 'instrument_id', 'error': f"Instrument '{instrument.symbol}' is not active (status: {instrument.status})."})

            # Value validation
            val_raw = clean_cell(raw_row.get('value'))
            dec_val = None
            if not val_raw:
                row_errors.append({'field': 'value', 'error': 'Price value is required.'})
            else:
                try:
                    dec_val = Decimal(val_raw)
                    if dec_val <= Decimal('0'):
                        row_errors.append({'field': 'value', 'error': 'Price value must be strictly positive.'})
                    elif not dec_val.is_finite():
                        row_errors.append({'field': 'value', 'error': 'Price value must be a finite decimal.'})
                except InvalidOperation:
                    row_errors.append({'field': 'value', 'error': f"Invalid decimal numeric string '{val_raw}'."})

            # Effective date validation
            eff_raw = clean_cell(raw_row.get('effective_at'))
            eff_dt = None
            if not eff_raw:
                row_errors.append({'field': 'effective_at', 'error': 'Effective timestamp is required.'})
            else:
                try:
                    # Support ISO formats YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
                    if 'T' in eff_raw:
                        eff_dt = datetime.fromisoformat(eff_raw.replace('Z', '+00:00'))
                    else:
                        eff_date = datetime.strptime(eff_raw, '%Y-%m-%d').date()
                        eff_dt = datetime.combine(eff_date, datetime.min.time(), tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc)

                    if dj_timezone.is_naive(eff_dt):
                        eff_dt = eff_dt.replace(tzinfo=ZoneInfo('Asia/Kolkata'))
                    eff_dt = eff_dt.astimezone(timezone.utc)
                    if eff_dt > now_utc + timedelta(minutes=5):
                        row_errors.append({'field': 'effective_at', 'error': 'Effective timestamp cannot be in the future.'})
                except Exception:
                    row_errors.append({'field': 'effective_at', 'error': f"Invalid date format '{eff_raw}'. Use YYYY-MM-DD or ISO 8601."})

            # Exact series identity is mandatory for CSV imports.
            price_type = clean_cell(raw_row.get('price_type', 'LTP')).upper()
            currency = clean_cell(raw_row.get('currency', 'INR')).upper()
            unit = clean_cell(raw_row.get('unit', 'UNITS')).upper()

            source_name = clean_cell(raw_row.get('source_id') or 'CSV_IMPORT')
            series_raw = clean_cell(raw_row.get('series_id'))
            series = None
            if instrument:
                series_cache_key = (instrument.id, price_type, currency, unit, source_name, series_raw)
                if series_cache_key not in series_cache:
                    series_qs = MarketDataSeries.objects.using('market_data').filter(
                        instrument_id=instrument.id, price_type=price_type,
                        currency=currency, unit=unit, is_active=True,
                    )
                    if series_raw:
                        try:
                            series_cache[series_cache_key] = series_qs.filter(pk=uuid.UUID(series_raw)).first()
                        except ValueError:
                            series_cache[series_cache_key] = None
                    else:
                        matches = list(series_qs.filter(source=source_name).order_by('id')[:2])
                        if len(matches) == 1:
                            series_cache[series_cache_key] = matches[0]
                        elif len(matches) > 1:
                            series_cache[series_cache_key] = 'AMBIGUOUS'
                        else:
                            all_matches = list(series_qs.order_by('id')[:2])
                            if len(all_matches) == 1:
                                series_cache[series_cache_key] = all_matches[0]
                            elif len(all_matches) > 1:
                                series_cache[series_cache_key] = 'AMBIGUOUS'
                            elif not series_raw:
                                auto_s, _ = MarketDataSeries.objects.using('market_data').get_or_create(
                                    instrument_id=instrument.id,
                                    exchange=instrument.exchange or '',
                                    source=source_name,
                                    price_type=price_type,
                                    currency=currency,
                                    unit=unit,
                                    defaults={'is_active': True, 'description': f'Auto-created series for {instrument.symbol}'}
                                )
                                series_cache[series_cache_key] = auto_s
                            else:
                                series_cache[series_cache_key] = None
                series = series_cache[series_cache_key]
                if series == 'AMBIGUOUS':
                    row_errors.append({'field': 'series_id', 'error': 'Multiple series match. Supply an exact series_id.'})
                elif series is None and series_raw:
                    row_errors.append({'field': 'series_id', 'error': 'No active series matches the supplied series_id and identity dimensions.'})
                if series and series.source != source_name:
                    row_errors.append({'field': 'source_id', 'error': f"Source '{source_name}' does not match selected series source '{series.source}'."})
                if series is None and not any(e['field'] == 'series_id' for e in row_errors):
                    row_errors.append({'field': 'series_id', 'error': 'No exact active series matches this instrument, price type, currency and unit.'})

                if instrument.id not in coverage_cache:
                    coverage_cache[instrument.id] = instrument.coverage
                cov = coverage_cache[instrument.id]
                if cov and cov.currency and cov.currency != currency:
                    row_errors.append({'field': 'currency', 'error': f"Currency mismatch: expected '{cov.currency}', got '{currency}'."})
                if cov and cov.price_type != price_type:
                    row_errors.append({'field': 'price_type', 'error': f"Price type mismatch: expected '{cov.price_type}', got '{price_type}'."})

            if instrument and eff_dt and series:
                dedup_key = (instrument.id, series.id, eff_dt.astimezone(ZoneInfo('Asia/Kolkata')).date())
                if dedup_key in seen_series_dates:
                    row_errors.append({'field': 'series_id', 'error': f"Duplicate observation for series {series.id} on this market date inside this CSV."})
                else:
                    seen_series_dates.add(dedup_key)
                market_day = eff_dt.astimezone(ZoneInfo('Asia/Kolkata')).date()
                day_start = datetime.combine(market_day, datetime.min.time(), tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc)
                day_end = datetime.combine(market_day + timedelta(days=1), datetime.min.time(), tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc)
                if PriceObservation.objects.using('market_data').filter(
                    instrument_id=instrument.id, series_id=series.id,
                    effective_at__gte=day_start, effective_at__lt=day_end,
                    price_type=price_type, source=source_name, status=ObservationStatus.PUBLISHED,
                ).exists():
                    row_errors.append({'field': 'effective_at', 'error': 'An observation for this exact series and market date is already published.'})

            if row_errors:
                for err in row_errors:
                    errors.append({
                        'row_number': idx,
                        'field': err['field'],
                        'error': err['error'],
                        'raw_data': raw_row,
                    })
            else:
                valid_rows.append({
                    'row_number': idx,
                    'instrument_id': str(instrument.id),
                    'symbol': instrument.symbol,
                    'instrument_name': instrument.name,
                    'series_id': str(series.id),
                    'price_type': price_type,
                    'value': str(dec_val),
                    'currency': currency,
                    'unit': unit,
                    'effective_at': eff_dt.isoformat(),
                    'source': source_name,
                    'source_reference': clean_cell(raw_row.get('source_reference')),
                    'notes': clean_cell(raw_row.get('notes')),
                })

        batch = PriceImportBatch.objects.create(
            user=user,
            filename=filename,
            schema_version='1.0',
            total_rows=total_rows,
            valid_rows=len(valid_rows),
            error_rows=len(errors),
            status=ImportBatchStatus.PREVIEWED if len(valid_rows) > 0 else ImportBatchStatus.FAILED,
            metadata={'valid_rows': valid_rows, 'errors': errors},
        )

        return {
            'batch_id': str(batch.id),
            'filename': filename,
            'total_rows': total_rows,
            'valid_count': len(valid_rows),
            'error_count': len(errors),
            'valid_rows': valid_rows,
            'errors': errors,
        }

    @classmethod
    @transaction.atomic(using='market_data')
    def commit_batch(cls, user, batch_id: Any) -> PriceImportBatch:
        """
        Commits a server-side validated preview batch without trusting client-supplied parsed rows.
        """
        try:
            batch = PriceImportBatch.objects.select_for_update().get(id=batch_id, user=user)
        except (PriceImportBatch.DoesNotExist, ValueError):
            raise ValidationError("Import batch not found or access denied.")

        if batch.status == ImportBatchStatus.COMMITTED:
            raise ValidationError("Import batch has already been committed.")

        valid_rows = batch.metadata.get('valid_rows', [])
        errors = batch.metadata.get('errors', [])

        if not valid_rows:
            batch.status = ImportBatchStatus.FAILED
            batch.save(update_fields=['status', 'updated_at'])
            raise ValidationError("Batch has no valid rows to commit.")

        # Log row errors for operator report download
        for err in errors:
            PriceImportRowError.objects.create(
                batch=batch,
                row_number=err['row_number'],
                raw_data=err.get('raw_data', {}),
                error_field=err.get('field', ''),
                error_message=err.get('error', ''),
            )

        # Create draft PriceObservation for every valid row
        for row in valid_rows:
            if not MarketDataSeries.objects.using('market_data').filter(
                pk=row['series_id'], instrument_id=row['instrument_id'],
                price_type=row['price_type'], currency=row['currency'], unit=row['unit'],
                source=row['source'], is_active=True,
            ).exists():
                raise ValidationError(f"Series {row['series_id']} changed or is no longer active; create a new preview.")
            PriceObservation.objects.create(
                instrument_id=row['instrument_id'],
                series_id=row['series_id'],
                price_type=row['price_type'],
                value=Decimal(row['value']),
                currency=row['currency'],
                unit=row['unit'],
                effective_at=datetime.fromisoformat(row['effective_at']),
                source=row['source'],
                source_reference=row['source_reference'],
                notes=f"[Batch {batch.id}] {row['notes']}".strip(),
                status=ObservationStatus.DRAFT,
                trust_class=TrustClass.UNVERIFIED,
                recorded_by=user,
            )

        batch.status = ImportBatchStatus.COMMITTED
        batch.save(update_fields=['status', 'updated_at'])
        return batch

    @classmethod
    @transaction.atomic(using='market_data')
    def commit_import(cls, user, preview_result: Dict[str, Any]) -> PriceImportBatch:
        """
        Persists validated rows as draft PriceObservations and logs batch audit history.
        Strictly requires server-persisted batch_id.
        """
        batch_id = preview_result.get('batch_id')
        if not batch_id:
            raise ValidationError("Server-persisted batch_id is required. Direct client row commitment is disabled for security.")
        return cls.commit_batch(user, batch_id)
