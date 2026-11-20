import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import DecimalField, ExpressionWrapper, F

from apps.assets.models.investment import AssetCategory, Investment
from apps.assets.models.transactions import InvestmentTransaction
from apps.market_data.services.price_resolver import PriceResolver
from apps.portfolios.models import Portfolio
from apps.users.models import User
from apps.valuation.services.calculation.decimal_utils import quantize_currency, to_decimal
from apps.watchlists.services.watchlist_service import WatchlistService


class DashboardService:
    """
    Authoritative aggregation service for the user portfolio dashboard.
    Coordinates read-oriented views over portfolios, investments, transactions,
    market data provenance, and valuation records.
    Never alters investment transactions, records, or persistent cost bases.
    """

    @staticmethod
    def resolve_portfolio_scope(user: User, portfolio_id: Optional[uuid.UUID | str] = None) -> Optional[Portfolio]:
        """
        Validates and resolves portfolio scope.
        Returns Portfolio instance if valid and owned by user, None if combined view.
        Raises ObjectDoesNotExist if portfolio_id does not belong to user or does not exist.
        """
        if not portfolio_id:
            return None

        try:
            return Portfolio.objects.get(id=portfolio_id, user=user)
        except (Portfolio.DoesNotExist, ValueError):
            raise ObjectDoesNotExist(f"Portfolio with id {portfolio_id} not found for this user.")

    @classmethod
    def get_user_dashboard_overview(
        cls,
        user: User,
        portfolio_id: Optional[uuid.UUID | str] = None,
    ) -> Dict[str, Any]:
        """
        Gathers comprehensive dashboard overview for the authenticated user.
        Preserves backward compatibility with existing tests expecting user, portfolio_count,
        and recent_portfolios.
        """
        selected_portfolio = cls.resolve_portfolio_scope(user, portfolio_id)
        user_portfolios = Portfolio.objects.filter(user=user).order_by('-updated_at')
        total_portfolios_count = user_portfolios.count()

        recent = [
            {
                "id": p.id,
                "name": p.name,
                "base_currency": p.base_currency,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            for p in user_portfolios[:5]
        ]

        # Scope investments
        inv_qs = Investment.objects.filter(user=user, is_active=True).select_related(
            'portfolio', 'instrument', 'instrument__reference_data'
        ).prefetch_related('valuations')

        if selected_portfolio:
            inv_qs = inv_qs.filter(portfolio=selected_portfolio)

        investments = list(inv_qs)
        active_investment_count = len(investments)

        # Currency-separated summaries (Option B: No unverified FX conversions)
        totals_by_currency: Dict[str, Dict[str, Any]] = {}
        for inv in investments:
            curr = inv.currency or 'INR'
            if curr not in totals_by_currency:
                totals_by_currency[curr] = {
                    'currency': curr,
                    'total_current_value': Decimal('0.00'),
                    'total_invested_capital': Decimal('0.00'),
                    'valued_investment_count': 0,
                    'unvalued_investment_count': 0,
                    'total_investment_count': 0,
                }

            group = totals_by_currency[curr]
            group['total_investment_count'] += 1

            c_val = to_decimal(inv.current_value)
            i_val = to_decimal(inv.initial_value)

            group['total_current_value'] += c_val
            group['total_invested_capital'] += i_val

            # Valued check: has a positive current value or valid valuation record
            has_snapshot = bool(inv.valuations.all())
            if c_val > Decimal('0') or has_snapshot:
                group['valued_investment_count'] += 1
            else:
                group['unvalued_investment_count'] += 1

        # Format metrics per currency
        formatted_totals: Dict[str, Dict[str, Any]] = {}
        for curr, data in totals_by_currency.items():
            tot_curr = quantize_currency(data['total_current_value'])
            tot_inv = quantize_currency(data['total_invested_capital'])
            abs_gl = quantize_currency(tot_curr - tot_inv)

            gl_pct: Optional[str] = None
            if tot_inv > Decimal('0'):
                pct = ((tot_curr - tot_inv) / tot_inv) * Decimal('100')
                gl_pct = str(quantize_currency(pct))

            formatted_totals[curr] = {
                'currency': curr,
                'total_current_value': str(tot_curr),
                'total_invested_capital': str(tot_inv),
                'absolute_gain_loss': str(abs_gl),
                'gain_loss_percentage': gl_pct,
                'valued_investment_count': data['valued_investment_count'],
                'unvalued_investment_count': data['unvalued_investment_count'],
                'total_investment_count': data['total_investment_count'],
            }

        # Data completeness tracking across all active holdings
        total_valued = sum(d['valued_investment_count'] for d in totals_by_currency.values())
        total_unvalued = sum(d['unvalued_investment_count'] for d in totals_by_currency.values())

        stale_count = 0
        missing_count = 0
        instruments = [inv.instrument for inv in investments if inv.instrument]
        price_map = PriceResolver.resolve_prices_bulk(instruments)

        for inv in investments:
            if inv.instrument:
                res = price_map.get(inv.instrument.id)
                if res:
                    if res.status == 'STALE':
                        stale_count += 1
                    elif res.status in ('MISSING', 'UNSUPPORTED'):
                        missing_count += 1

        completeness_pct = 100.0
        if active_investment_count > 0:
            completeness_pct = round((total_valued / active_investment_count) * 100.0, 2)

        data_completeness = {
            'total_active_holdings': active_investment_count,
            'valued_holdings': total_valued,
            'unvalued_holdings': total_unvalued,
            'stale_holdings': stale_count,
            'missing_price_holdings': missing_count,
            'completeness_percentage': completeness_pct,
        }

        # Determine primary summary
        primary_summary: Optional[Dict[str, Any]] = None
        if selected_portfolio and selected_portfolio.base_currency in formatted_totals:
            primary_summary = formatted_totals[selected_portfolio.base_currency]
        elif len(formatted_totals) == 1:
            primary_summary = next(iter(formatted_totals.values()))
        elif 'INR' in formatted_totals:
            primary_summary = formatted_totals['INR']
        elif formatted_totals:
            primary_summary = next(iter(formatted_totals.values()))
        else:
            primary_summary = {
                'currency': selected_portfolio.base_currency if selected_portfolio else 'INR',
                'total_current_value': '0.00',
                'total_invested_capital': '0.00',
                'absolute_gain_loss': '0.00',
                'gain_loss_percentage': None,
                'valued_investment_count': 0,
                'unvalued_investment_count': 0,
                'total_investment_count': 0,
            }

        return {
            "user": {
                "id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
            },
            "portfolio_count": total_portfolios_count,
            "recent_portfolios": recent,
            "selected_portfolio": {
                "id": str(selected_portfolio.id),
                "name": selected_portfolio.name,
                "base_currency": selected_portfolio.base_currency,
            } if selected_portfolio else None,
            "is_combined": selected_portfolio is None,
            "active_investment_count": active_investment_count,
            "summary": primary_summary,
            "totals_by_currency": formatted_totals,
            "data_completeness": data_completeness,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_asset_allocation(
        cls,
        user: User,
        portfolio_id: Optional[uuid.UUID | str] = None,
        currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates asset allocation percentages using authoritative current valuations.
        Guarantees that unvalued assets do not dilute the valued denominator silently,
        and reports completeness metrics explicitly.
        """
        selected_portfolio = cls.resolve_portfolio_scope(user, portfolio_id)
        inv_qs = Investment.objects.filter(user=user, is_active=True).select_related('portfolio')

        if selected_portfolio:
            inv_qs = inv_qs.filter(portfolio=selected_portfolio)

        if currency:
            inv_qs = inv_qs.filter(currency=currency.upper())

        investments = list(inv_qs)

        # Group by currency first to avoid invalid cross-currency additions
        currencies = sorted(list({inv.currency or 'INR' for inv in investments}))
        if not currencies:
            target_curr = currency.upper() if currency else (selected_portfolio.base_currency if selected_portfolio else 'INR')
            return {
                'currency': target_curr,
                'denominator_value': '0.00',
                'valued_count': 0,
                'unvalued_count': 0,
                'has_unvalued_assets': False,
                'asset_class_allocation': [],
                'portfolio_allocation': [],
                'top_holdings_allocation': [],
                'allocations_by_currency': {},
            }

        allocations_by_currency: Dict[str, Any] = {}

        for curr in currencies:
            curr_invs = [inv for inv in investments if (inv.currency or 'INR') == curr]
            valued_invs = [inv for inv in curr_invs if to_decimal(inv.current_value) > Decimal('0')]
            unvalued_count = len(curr_invs) - len(valued_invs)

            denominator = sum((to_decimal(inv.current_value) for inv in valued_invs), Decimal('0'))
            denominator_quant = quantize_currency(denominator)

            # 1. By Asset Class
            cat_groups: Dict[str, Dict[str, Any]] = {}
            for inv in valued_invs:
                cat = inv.category
                val = to_decimal(inv.current_value)
                if cat not in cat_groups:
                    label = dict(AssetCategory.choices).get(cat, cat.replace('_', ' ').title())
                    cat_groups[cat] = {
                        'category': cat,
                        'display_name': label,
                        'total_value': Decimal('0'),
                        'count': 0,
                    }
                cat_groups[cat]['total_value'] += val
                cat_groups[cat]['count'] += 1

            cat_alloc = []
            for cat, data in sorted(cat_groups.items(), key=lambda x: x[1]['total_value'], reverse=True):
                pct = ((data['total_value'] / denominator) * Decimal('100')) if denominator > Decimal('0') else Decimal('0')
                cat_alloc.append({
                    'category': cat,
                    'display_name': data['display_name'],
                    'total_value': str(quantize_currency(data['total_value'])),
                    'percentage': str(quantize_currency(pct)),
                    'count': data['count'],
                })

            # 2. By Portfolio
            port_groups: Dict[str, Dict[str, Any]] = {}
            for inv in valued_invs:
                p_id = str(inv.portfolio.id)
                val = to_decimal(inv.current_value)
                if p_id not in port_groups:
                    port_groups[p_id] = {
                        'portfolio_id': p_id,
                        'portfolio_name': inv.portfolio.name,
                        'total_value': Decimal('0'),
                        'count': 0,
                    }
                port_groups[p_id]['total_value'] += val
                port_groups[p_id]['count'] += 1

            port_alloc = []
            for p_id, data in sorted(port_groups.items(), key=lambda x: x[1]['total_value'], reverse=True):
                pct = ((data['total_value'] / denominator) * Decimal('100')) if denominator > Decimal('0') else Decimal('0')
                port_alloc.append({
                    'portfolio_id': p_id,
                    'portfolio_name': data['portfolio_name'],
                    'total_value': str(quantize_currency(data['total_value'])),
                    'percentage': str(quantize_currency(pct)),
                    'count': data['count'],
                })

            # 3. Top Holdings (up to 5)
            sorted_by_val = sorted(valued_invs, key=lambda x: to_decimal(x.current_value), reverse=True)
            top_holdings = []
            for inv in sorted_by_val[:5]:
                val = to_decimal(inv.current_value)
                pct = ((val / denominator) * Decimal('100')) if denominator > Decimal('0') else Decimal('0')
                top_holdings.append({
                    'id': str(inv.id),
                    'display_name': inv.display_name,
                    'category': inv.category,
                    'total_value': str(quantize_currency(val)),
                    'percentage': str(quantize_currency(pct)),
                })

            allocations_by_currency[curr] = {
                'currency': curr,
                'denominator_value': str(denominator_quant),
                'valued_count': len(valued_invs),
                'unvalued_count': unvalued_count,
                'has_unvalued_assets': unvalued_count > 0,
                'asset_class_allocation': cat_alloc,
                'portfolio_allocation': port_alloc,
                'top_holdings_allocation': top_holdings,
            }

        # Select primary currency
        primary_curr = (
            currency.upper()
            if currency and currency.upper() in allocations_by_currency
            else (selected_portfolio.base_currency if selected_portfolio and selected_portfolio.base_currency in allocations_by_currency else currencies[0])
        )
        primary_data = allocations_by_currency[primary_curr]

        return {
            **primary_data,
            'allocations_by_currency': allocations_by_currency,
        }

    @classmethod
    def get_holdings_overview(
        cls,
        user: User,
        portfolio_id: Optional[uuid.UUID | str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = True,
        sort_by: str = 'current_value',
        order: str = 'desc',
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Retrieves concise investment holdings overview with sorting and pagination.
        Includes calculated gain/loss, valuation timestamp, and market-price freshness.
        """
        selected_portfolio = cls.resolve_portfolio_scope(user, portfolio_id)
        inv_qs = Investment.objects.filter(user=user).select_related(
            'portfolio', 'instrument', 'instrument__reference_data'
        ).prefetch_related('valuations')

        if selected_portfolio:
            inv_qs = inv_qs.filter(portfolio=selected_portfolio)

        if is_active is not None:
            inv_qs = inv_qs.filter(is_active=is_active)

        if category:
            inv_qs = inv_qs.filter(category=category.lower())

        total_count = inv_qs.count()

        # Database-side SQL annotation and deterministic secondary sort for all sort fields
        inv_qs = inv_qs.annotate(
            db_gain_loss=ExpressionWrapper(
                F('current_value') - F('initial_value'),
                output_field=DecimalField(max_digits=18, decimal_places=4),
            )
        )

        col_map = {
            'current_value': 'current_value',
            'invested_capital': 'initial_value',
            'display_name': 'display_name',
            'gain_loss': 'db_gain_loss',
        }
        db_col = col_map.get(sort_by, 'current_value')
        prefix = '-' if order.lower() == 'desc' else ''
        paged_investments = list(inv_qs.order_by(f"{prefix}{db_col}", '-id')[offset: offset + limit])

        # Bulk resolve market prices for instruments
        instruments = [inv.instrument for inv in paged_investments if inv.instrument]
        price_map = PriceResolver.resolve_prices_bulk(instruments)

        # Annotate holdings
        annotated: List[Dict[str, Any]] = []
        for inv in paged_investments:
            c_val = to_decimal(inv.current_value)
            i_val = to_decimal(inv.initial_value)
            abs_gl = c_val - i_val

            gl_pct: Optional[str] = None
            if i_val > Decimal('0'):
                pct = (abs_gl / i_val) * Decimal('100')
                gl_pct = str(quantize_currency(pct))

            # Latest valuation snapshot
            snapshots = list(inv.valuations.all())
            latest_val = sorted(snapshots, key=lambda v: (v.valuation_date, v.created_at), reverse=True)[0] if snapshots else None
            val_date = latest_val.valuation_date.isoformat() if latest_val else None
            val_source = latest_val.source if latest_val else None
            val_status = 'VALUED' if latest_val else 'MISSING'

            # Price freshness & provenance
            freshness = 'MANUAL'
            is_stale = False
            if inv.instrument:
                res = price_map.get(inv.instrument.id)
                if res:
                    freshness = res.status
                    is_stale = res.status == 'STALE'
                else:
                    freshness = 'MISSING'

            # Clean quantity string where available
            qty = inv.quantity
            qty_str = str(qty) if qty is not None else None

            annotated.append({
                'id': str(inv.id),
                'display_name': inv.display_name,
                'category': inv.category,
                'asset_type': inv.asset_type,
                'portfolio_id': str(inv.portfolio.id),
                'portfolio_name': inv.portfolio.name,
                'is_active': inv.is_active,
                'currency': inv.currency or 'INR',
                'quantity': qty_str,
                'invested_capital': str(quantize_currency(i_val)),
                'current_value': str(quantize_currency(c_val)),
                'absolute_gain_loss': str(quantize_currency(abs_gl)),
                'gain_loss_percentage': gl_pct,
                'valuation_date': val_date,
                'valuation_source': val_source,
                'valuation_status': val_status,
                'price_freshness': freshness,
                'is_stale': is_stale,
            })

        paged_results = annotated

        return {
            'count': total_count,
            'limit': limit,
            'offset': offset,
            'results': paged_results,
        }

    @classmethod
    def get_recent_activity(
        cls,
        user: User,
        portfolio_id: Optional[uuid.UUID | str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves recent investment transactions deterministically sorted by date and creation.
        Uses canonical transaction amounts, gross amounts, fees, and taxes.
        """
        selected_portfolio = cls.resolve_portfolio_scope(user, portfolio_id)
        tx_qs = InvestmentTransaction.objects.filter(user=user).select_related(
            'investment', 'portfolio'
        ).order_by('-transaction_date', '-created_at')

        if selected_portfolio:
            tx_qs = tx_qs.filter(portfolio=selected_portfolio)

        bounded_limit = min(max(1, limit), 50)
        transactions = list(tx_qs[:bounded_limit])

        activity: List[Dict[str, Any]] = []
        for tx in transactions:
            activity.append({
                'id': str(tx.id),
                'investment_id': str(tx.investment.id),
                'investment_name': tx.investment.display_name,
                'portfolio_id': str(tx.portfolio.id),
                'portfolio_name': tx.portfolio.name,
                'transaction_type': tx.transaction_type,
                'transaction_date': tx.transaction_date.isoformat(),
                'units': str(tx.units) if tx.units is not None else '0',
                'price_per_unit': str(tx.price_per_unit) if tx.price_per_unit is not None else '0',
                'amount': str(quantize_currency(tx.amount)),
                'gross_amount': str(quantize_currency(tx.gross_amount)) if tx.gross_amount is not None else None,
                'fees': str(quantize_currency(tx.fees)),
                'taxes': str(quantize_currency(tx.taxes)),
                'net_cash_flow': str(quantize_currency(tx.net_cash_flow)) if tx.net_cash_flow is not None else None,
                'currency': tx.currency or 'INR',
                'notes': tx.notes,
                'created_at': tx.created_at.isoformat(),
            })

        return activity

    @classmethod
    def get_data_quality(
        cls,
        user: User,
        portfolio_id: Optional[uuid.UUID | str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates data quality and valuation reliability across active holdings.
        Categorizes holdings into Valued, Stale, Missing, Awaiting Verification, and Unsupported
        with clear user-facing diagnostic explanations.
        """
        selected_portfolio = cls.resolve_portfolio_scope(user, portfolio_id)
        inv_qs = Investment.objects.filter(user=user, is_active=True).select_related(
            'portfolio', 'instrument'
        ).prefetch_related('valuations')

        if selected_portfolio:
            inv_qs = inv_qs.filter(portfolio=selected_portfolio)

        investments = list(inv_qs)

        valued_list = []
        stale_list = []
        missing_list = []
        unverified_list = []
        unsupported_list = []

        # Bulk resolve market prices for all instrument holdings
        instruments = [inv.instrument for inv in investments if inv.instrument]
        price_map = PriceResolver.resolve_prices_bulk(instruments)

        for inv in investments:
            holding_info = {
                'id': str(inv.id),
                'display_name': inv.display_name,
                'category': inv.category,
                'asset_type': inv.asset_type,
                'currency': inv.currency,
                'current_value': str(quantize_currency(inv.current_value)),
            }

            if inv.instrument:
                inst = inv.instrument
                # Check instrument verification status
                if inst.status in ('PENDING_REVIEW', 'DRAFT', 'REJECTED'):
                    unverified_list.append({
                        **holding_info,
                        'reason': f"Instrument {inst.symbol} is awaiting canonical verification ({inst.status}).",
                    })
                    continue

                res = price_map.get(inst.id)
                if not res or res.status == 'MISSING':
                    missing_list.append({
                        **holding_info,
                        'reason': f"No published market price found for {inst.symbol}.",
                    })
                elif res.status == 'AVAILABLE':
                    valued_list.append(holding_info)
                elif res.status == 'STALE':
                    stale_list.append({
                        **holding_info,
                        'reason': f"Market price for {inst.symbol} is stale (effective {res.effective_at.date() if res.effective_at else 'unknown'}).",
                    })
                elif res.status == 'SYNTHETIC':
                    valued_list.append(holding_info)
                elif res.status == 'AWAITING_VERIFICATION':
                    unverified_list.append({
                        **holding_info,
                        'reason': "Instrument price is awaiting verification.",
                    })
                else:
                    unsupported_list.append({
                        **holding_info,
                        'reason': f"Price status is {res.status}.",
                    })
            else:
                # Non-instrument holdings (Bank deposit, cash, real estate, etc.)
                has_snapshot = bool(inv.valuations.all())
                if to_decimal(inv.current_value) > Decimal('0') or has_snapshot:
                    valued_list.append(holding_info)
                elif to_decimal(inv.initial_value) > Decimal('0'):
                    missing_list.append({
                        **holding_info,
                        'reason': "Holding has acquisition cost but no valuation has been recorded.",
                    })
                else:
                    unsupported_list.append({
                        **holding_info,
                        'reason': "Holding has zero valuation and zero cost basis.",
                    })

        total_active = len(investments)
        if total_active == 0:
            overall_status = 'HEALTHY'
        elif len(missing_list) > 0 or len(unverified_list) > 0:
            overall_status = 'INCOMPLETE'
        elif len(stale_list) > 0 or len(unsupported_list) > 0:
            overall_status = 'WARNING'
        else:
            overall_status = 'HEALTHY'

        return {
            'overall_status': overall_status,
            'total_active_holdings': total_active,
            'categories': {
                'valued': {
                    'count': len(valued_list),
                    'label': 'Successfully Valued',
                    'description': 'Price updated for the latest available trading session or active contract schedule.',
                    'items': valued_list[:10],
                },
                'stale': {
                    'count': len(stale_list),
                    'label': 'Stale Valuations',
                    'description': 'Last available published market price or recorded valuation is older than expected.',
                    'items': stale_list,
                },
                'missing_price': {
                    'count': len(missing_list),
                    'label': 'Missing Market Prices',
                    'description': 'No supported market-price observation or valuation record is available.',
                    'items': missing_list,
                },
                'awaiting_verification': {
                    'count': len(unverified_list),
                    'label': 'Awaiting Verification',
                    'description': 'Underlying instrument or price submission is awaiting operator verification.',
                    'items': unverified_list,
                },
                'unsupported': {
                    'count': len(unsupported_list),
                    'label': 'Unsupported or Incomplete',
                    'description': 'Holding requires manual cost basis or appraisal valuation.',
                    'items': unsupported_list,
                },
            },
        }

    @classmethod
    def get_watchlist_preview(cls, user: User, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves top user watchlist items for dashboard preview.
        Directly reuses WatchlistService without duplicating price resolution.
        """
        bounded_limit = min(max(1, limit), 10)
        items = WatchlistService.list_items(user)
        return items[:bounded_limit]
