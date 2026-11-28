from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from apps.analytics.services.financial_math import quantize_currency, to_decimal
from apps.analytics.services.fx_service import FXConversionService
from apps.assets.models.investment import AssetCategory, Investment
from apps.portfolios.models import Portfolio


@dataclass
class AllocationItem:
    key: str
    name: str
    market_value: Decimal
    percentage: Decimal
    holding_count: int


@dataclass
class AllocationResult:
    portfolio_id: Optional[str]
    currency: str
    total_market_value: Decimal
    by_asset_category: List[AllocationItem] = field(default_factory=list)
    by_instrument: List[AllocationItem] = field(default_factory=list)


class AllocationAnalyticsService:
    """Calculates authoritative asset allocation breakdowns."""

    @classmethod
    def get_allocation(
        cls,
        user,
        portfolio: Optional[Portfolio] = None,
        currency: Optional[str] = None,
    ) -> AllocationResult:
        qs = Investment.objects.filter(user=user, is_active=True).select_related(
            'instrument', 'portfolio'
        )
        if portfolio:
            qs = qs.filter(portfolio=portfolio)

        reporting_curr = currency or (portfolio.base_currency if portfolio else 'INR')

        investments = list(qs)
        total_val = Decimal('0.00')

        cat_map: Dict[str, Dict[str, Any]] = {}
        inst_map: Dict[str, Dict[str, Any]] = {}
        today = date.today()

        for inv in investments:
            c_val = to_decimal(inv.current_value)
            if c_val <= Decimal('0'):
                continue

            inv_curr = getattr(inv, 'currency', reporting_curr)
            if inv_curr != reporting_curr:
                c_val, _, _ = FXConversionService.convert_amount(c_val, inv_curr, reporting_curr, today)

            total_val += c_val

            # By category
            cat_key = inv.category
            cat_name = dict(AssetCategory.choices).get(cat_key, cat_key.title())
            if cat_key not in cat_map:
                cat_map[cat_key] = {'name': cat_name, 'value': Decimal('0.00'), 'count': 0}
            cat_map[cat_key]['value'] += c_val
            cat_map[cat_key]['count'] += 1

            # By instrument / holding
            inst_key = str(inv.id)
            inst_name = inv.display_name
            if inst_key not in inst_map:
                inst_map[inst_key] = {'name': inst_name, 'value': Decimal('0.00'), 'count': 1}
            inst_map[inst_key]['value'] += c_val

        cat_items: List[AllocationItem] = []
        for k, v in cat_map.items():
            pct = ((v['value'] / total_val) * Decimal('100')).quantize(Decimal('0.01')) if total_val > 0 else Decimal('0.00')
            cat_items.append(AllocationItem(
                key=k,
                name=v['name'],
                market_value=quantize_currency(v['value']),
                percentage=pct,
                holding_count=v['count'],
            ))

        inst_items: List[AllocationItem] = []
        for k, v in inst_map.items():
            pct = ((v['value'] / total_val) * Decimal('100')).quantize(Decimal('0.01')) if total_val > 0 else Decimal('0.00')
            inst_items.append(AllocationItem(
                key=k,
                name=v['name'],
                market_value=quantize_currency(v['value']),
                percentage=pct,
                holding_count=v['count'],
            ))

        # Sort descending by value
        cat_items.sort(key=lambda x: x.market_value, reverse=True)
        inst_items.sort(key=lambda x: x.market_value, reverse=True)

        return AllocationResult(
            portfolio_id=str(portfolio.id) if portfolio else None,
            currency=reporting_curr,
            total_market_value=quantize_currency(total_val),
            by_asset_category=cat_items,
            by_instrument=inst_items,
        )
