import csv
import io
import logging
import uuid
from datetime import datetime, timezone
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
from apps.market_data.models.observation import ObservationStatus, PriceObservation
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

    @classmethod
    def preview_csv(cls, user, csv_content: str, filename: str = 'import.csv') -> Dict[str, Any]:
        """
        Parses and validates a CSV string without creating PriceObservation records.
        Returns detailed summary and row-level validation errors.
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        total_rows = 0
        valid_rows: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        seen_instruments: set = set()

        now_utc = dj_timezone.now()

        for idx, raw_row in enumerate(reader, start=2):  # Header is line 1
            total_rows += 1
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
                    instrument = Instrument.objects.filter(id=inst_uuid).first()
                except ValueError:
                    row_errors.append({'field': 'instrument_id', 'error': 'Invalid UUID format for instrument_id.'})
            elif item_id_raw:
                try:
                    item_uuid = uuid.UUID(item_id_raw)
                    item = MarketDataWorklistItem.objects.filter(id=item_uuid).select_related('instrument').first()
                    if item:
                        instrument = item.instrument
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
                        eff_dt = datetime.combine(eff_date, datetime.min.time(), tzinfo=timezone.utc)

                    if eff_dt > now_utc + dj_timezone.timedelta(minutes=5):
                        row_errors.append({'field': 'effective_at', 'error': 'Effective timestamp cannot be in the future.'})
                except Exception:
                    row_errors.append({'field': 'effective_at', 'error': f"Invalid date format '{eff_raw}'. Use YYYY-MM-DD or ISO 8601."})

            # Coverage policy compatibility
            price_type = clean_cell(raw_row.get('price_type', 'LTP')).upper()
            currency = clean_cell(raw_row.get('currency', 'INR')).upper()
            unit = clean_cell(raw_row.get('unit', 'UNITS')).upper()

            if instrument and hasattr(instrument, 'coverage'):
                cov = instrument.coverage
                if cov.currency != currency:
                    row_errors.append({'field': 'currency', 'error': f"Currency mismatch: expected '{cov.currency}', got '{currency}'."})

            # Duplicate check inside batch
            if instrument and eff_dt:
                dedup_key = (instrument.id, eff_dt.date())
                if dedup_key in seen_instruments:
                    row_errors.append({'field': 'instrument_id', 'error': f"Duplicate observation for instrument {instrument.symbol} on {eff_dt.date()} inside this CSV."})
                else:
                    seen_instruments.add(dedup_key)

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
                    'price_type': price_type,
                    'value': str(dec_val),
                    'currency': currency,
                    'unit': unit,
                    'effective_at': eff_dt.isoformat(),
                    'source': clean_cell(raw_row.get('source_id') or 'CSV_IMPORT'),
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
            PriceObservation.objects.create(
                instrument_id=row['instrument_id'],
                price_type=row['price_type'],
                value=Decimal(row['value']),
                currency=row['currency'],
                unit=row['unit'],
                effective_at=datetime.fromisoformat(row['effective_at']),
                source=row['source'],
                source_reference=row['source_reference'],
                notes=f"[Batch {batch.id}] {row['notes']}".strip(),
                status=ObservationStatus.DRAFT,
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
