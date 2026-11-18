from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from apps.assets.models.investment import Investment
from apps.market_data.services.price_resolver import PriceResolver, ResolutionStatus
from apps.valuation.services.asset_valuation.base import (
    BaseAssetValuationStrategy,
    ValuationResult,
    ValuationStatus,
)
from apps.valuation.services.calculation.decimal_utils import (
    quantize_currency,
    quantize_units,
    to_decimal,
)


class RealEstateInvestmentTrustValuationStrategy(BaseAssetValuationStrategy):
    """
    Evaluates Real Estate Investment Trust (REIT) holdings:
    REIT Units * Exchange Quoted Price.
    Strictly distinct from physical property appraisals.
    """

    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        details = investment.details or {}
        obs_dt = as_of or datetime.now(timezone.utc)

        units_raw = investment.quantity or details.get('units') or details.get('quantity')
        if units_raw is None:
            return ValuationResult(
                current_value=None,
                valuation_method='REIT_MARKET_PRICE',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INCOMPLETE_INPUT,
                notes='Missing units for REIT holding; cannot default to 1.0.',
            )

        units = to_decimal(units_raw)
        if units <= Decimal('0'):
            return ValuationResult(
                current_value=None,
                valuation_method='REIT_MARKET_PRICE',
                source='NONE',
                observed_at=obs_dt,
                status=ValuationStatus.INVALID_FINANCIAL_INPUT,
                notes='REIT units must be greater than zero.',
            )

        units = quantize_units(units)

        market_price = None
        source_name = 'USER_INPUT'
        source_ref = details.get('symbol', 'REIT')
        is_synthetic = False
        val_status = ValuationStatus.SUCCESS

        # 1. Check instrument link via canonical PriceResolver
        if investment.instrument:
            try:
                resolved = PriceResolver.resolve_price(investment.instrument, as_of=obs_dt)
                if resolved.price is not None and resolved.status in (
                    ResolutionStatus.AVAILABLE,
                    ResolutionStatus.STALE,
                    ResolutionStatus.SYNTHETIC,
                ):
                    market_price = resolved.price
                    source_name = resolved.source or 'MANUAL_VERIFIED'
                    source_ref = resolved.source_reference or investment.instrument.symbol
                    is_synthetic = resolved.is_synthetic
                    if resolved.effective_at:
                        obs_dt = resolved.effective_at
                    if resolved.status == ResolutionStatus.STALE:
                        val_status = ValuationStatus.STALE_DATA
            except Exception:
                pass

        # 2. Check for user explicit estimate
        if market_price is None:
            raw_p = details.get('current_price') or details.get('market_price') or details.get('user_estimate')
            if raw_p is not None:
                market_price = to_decimal(raw_p)
                source_name = 'USER_ESTIMATE'
                val_status = ValuationStatus.ESTIMATED
            else:
                return ValuationResult(
                    current_value=None,
                    valuation_method='REIT_MARKET_PRICE',
                    source='NONE',
                    observed_at=obs_dt,
                    status=ValuationStatus.MARKET_DATA_UNAVAILABLE,
                    notes='Market price unavailable for REIT.',
                )

        market_price = to_decimal(market_price)
        current_val = quantize_currency(units * market_price)

        return ValuationResult(
            current_value=current_val,
            valuation_method='REIT_MARKET_PRICE',
            source=source_name,
            source_reference=source_ref,
            observed_at=obs_dt,
            currency=investment.currency,
            status=val_status,
            is_synthetic=is_synthetic,
            metadata={
                'units': str(units),
                'market_price': str(market_price),
                'symbol': source_ref,
            },
        )
