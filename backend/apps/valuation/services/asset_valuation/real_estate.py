from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from apps.assets.models.investment import Investment
from apps.valuation.services.asset_valuation.base import (
    BaseAssetValuationStrategy,
    ValuationResult,
    ValuationStatus,
)
from apps.valuation.services.calculation.decimal_utils import quantize_currency, to_decimal


class RealEstateValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates real estate property holdings using latest estimated appraisal
    or historical acquisition outlay, strictly adjusted for ownership percentage.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)

        ownership_pct = to_decimal(details.get('ownership_percentage', '100.00'))
        if ownership_pct <= Decimal('0') or ownership_pct > Decimal('100.00'):
            return ValuationResult(
                current_value=None,
                valuation_method='APPRAISAL',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='Ownership percentage must be between 0.01% and 100.00%.',
            )

        raw_val = (
            details.get('estimated_current_value')
            if details.get('estimated_current_value') is not None
            else (
                details.get('estimated_value')
                if details.get('estimated_value') is not None
                else details.get('market_value')
            )
        )

        val_date_raw = details.get('valuation_date') or details.get('last_appraisal_date')
        val_source = str(details.get('valuation_source', 'APPRAISAL'))
        is_estimated = False
        notes = ""

        if raw_val is not None:
            base_value = to_decimal(raw_val)
            if base_value < Decimal('0'):
                return ValuationResult(
                    current_value=None,
                    valuation_method='APPRAISAL',
                    source='NONE',
                    observed_at=obs_dt,
                    status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                    notes='Appraisal property value cannot be negative.',
                )
            method = 'APPRAISAL'
            source = val_source
        elif details.get('purchase_price') is not None:
            base_value = to_decimal(details['purchase_price'])
            if base_value < Decimal('0'):
                return ValuationResult(
                    current_value=None,
                    valuation_method='HISTORICAL_COST',
                    source='NONE',
                    observed_at=obs_dt,
                    status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                    notes='Property purchase price cannot be negative.',
                )
            method = 'HISTORICAL_COST'
            source = 'ACQUISITION_COST'
            is_estimated = True
            notes = "No independent appraisal available; referenced using historical cost basis."
        elif investment.initial_value is not None:
            base_value = to_decimal(investment.initial_value)
            method = 'HISTORICAL_COST'
            source = 'ACQUISITION_COST'
            is_estimated = True
            notes = "Referenced using initial recorded holding value."
        else:
            return ValuationResult(
                current_value=None,
                valuation_method='APPRAISAL',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing property valuation or purchase price.',
            )

        adjusted_value = quantize_currency(base_value * (ownership_pct / Decimal('100.00')))

        # If appraisal date is specified, preserve observed timestamp accordingly
        if val_date_raw:
            try:
                if isinstance(val_date_raw, str):
                    d_parsed = datetime.fromisoformat(val_date_raw)
                elif hasattr(val_date_raw, 'isoformat'):
                    d_parsed = datetime.combine(val_date_raw, datetime.min.time(), tzinfo=timezone.utc)
                else:
                    d_parsed = obs_dt
                obs_dt = d_parsed
            except Exception:
                pass

        val_status = ValuationStatus.ESTIMATED if is_estimated else ValuationStatus.SUCCESS

        return ValuationResult(
            current_value=adjusted_value,
            valuation_method=method,
            source=source,
            source_reference=str(details.get('property_name', details.get('property_nickname', 'PROPERTY'))),
            observed_at=obs_dt,
            currency=investment.currency,
            status=val_status,
            notes=notes,
            metadata={
                'base_property_value': str(base_value),
                'ownership_percentage': str(ownership_pct),
                'property_type': details.get('property_type', 'RESIDENTIAL'),
                'land_classification': details.get('land_classification', ''),
                'property_use': details.get('property_use', ''),
                'city': details.get('city', ''),
                'valuation_date': str(val_date_raw) if val_date_raw else None,
            },
        )
