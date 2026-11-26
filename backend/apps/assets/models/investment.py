import uuid

from django.conf import settings
from django.db import models

from apps.portfolios.models import Portfolio


class AssetCategory(models.TextChoices):
    CASH = 'cash', 'Cash & Banking'
    FIXED_INCOME = 'fixed_income', 'Fixed Income & Deposits'
    EQUITY = 'equity', 'Listed Equities'
    MUTUAL_FUNDS = 'mutual_funds', 'Mutual Funds & ETFs'
    GOLD = 'gold', 'Gold & Precious Metals'
    REAL_ESTATE = 'real_estate', 'Real Estate & Property'
    CRYPTO = 'crypto', 'Cryptocurrencies'


class ValuationMethod(models.TextChoices):
    MANUAL = 'MANUAL', 'Manual Cost Basis'
    BANK_BALANCE = 'BANK_BALANCE', 'Bank Balance'
    MARKET_FEED = 'MARKET_FEED', 'Live Market Feed'
    MARKET_PRICE = 'MARKET_PRICE', 'Live Market Price'
    CONTRACTUAL = 'CONTRACTUAL', 'Contractual Calculation'
    CONTRACTUAL_CALCULATION = 'CONTRACTUAL_CALCULATION', 'Contractual Calculation'
    NAV = 'NAV', 'Mutual Fund Daily NAV'
    NAV_FEED = 'NAV_FEED', 'Mutual Fund Daily NAV'
    APPRAISAL = 'APPRAISAL', 'Independent Appraisal'
    GOVERNMENT_REFERENCE = 'GOVERNMENT_REFERENCE', 'Government Reference / Circle Rate'
    USER_ESTIMATE = 'USER_ESTIMATE', 'User Estimate'


class Investment(models.Model):
    """
    Core investment record representing a discrete holding inside a portfolio.
    Compositional container linked 1:1 to a specific asset detail record.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.PROTECT,
        related_name='investments',
        db_index=True,
    )
    instrument = models.ForeignKey(
        'market_data.Instrument',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investments',
        db_index=True,
        help_text='Associated standardized market instrument, if market-linked.',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='investments',
        db_index=True,
    )
    category = models.CharField(
        max_length=50,
        choices=AssetCategory.choices,
        db_index=True,
    )
    asset_type = models.CharField(max_length=60, db_index=True)
    display_name = models.CharField(max_length=200)
    currency = models.CharField(max_length=10, default='INR')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')

    valuation_method = models.CharField(
        max_length=50,
        choices=ValuationMethod.choices,
        default=ValuationMethod.MANUAL,
    )
    initial_value = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
        help_text='Total capital invested or opening deposit amount.',
    )
    current_value = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=0,
        help_text='Current valuation or latest marked value.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['portfolio', 'category'], name='inv_portfolio_cat_idx'),
            models.Index(fields=['user', 'asset_type'], name='inv_user_type_idx'),
            models.Index(fields=['user', '-created_at'], name='inv_user_created_idx'),
        ]

    def clean(self):
        super().clean()
        if self.portfolio_id and self.user_id:
            if hasattr(self, 'portfolio') and self.portfolio and self.portfolio.user_id != self.user_id:
                from django.core.exceptions import ValidationError
                raise ValidationError({'portfolio': 'Investment portfolio must belong to the investment owner.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.display_name} ({self.asset_type}) - {self.currency} {self.current_value}"

    @property
    def invested_amount(self):
        """Standard financial cost-basis alias for initial_value."""
        return self.initial_value

    @invested_amount.setter
    def invested_amount(self, value):
        self.initial_value = value

    @property
    def details(self):
        """Optimized targeted lookup of attached asset-specific detail model (ERD Section 17.4)."""
        if hasattr(self, '_custom_details') and self._custom_details is not None:
            return self._custom_details

        # Targeted relation lookup mapped by asset_type rather than querying all 8 relations
        asset_map = {
            'EQUITY': 'equity_detail',
            'MUTUAL_FUND': 'mutual_fund_detail',
            'BOND': 'bond_detail',
            'DEPOSIT': 'deposit_detail',
            'REAL_ESTATE': 'real_estate_detail',
            'GOLD': 'gold_detail',
            'COMMODITY': 'gold_detail',
            'CRYPTO': 'crypto_detail',
            'CASH': 'cash_detail',
        }
        target_rel = asset_map.get(str(self.asset_type).upper())
        relations_to_check = [target_rel] if target_rel else [
            'cash_detail', 'deposit_detail', 'bond_detail', 'equity_detail',
            'mutual_fund_detail', 'gold_detail', 'real_estate_detail', 'crypto_detail',
        ]

        for rel in relations_to_check:
            if not rel:
                continue
            try:
                detail_obj = getattr(self, rel, None)
                if detail_obj:
                    return {
                        field.name: getattr(detail_obj, field.name)
                        for field in detail_obj._meta.fields
                        if field.name not in ('id', 'investment')
                    }
            except Exception:
                pass
        return {}

    @details.setter
    def details(self, value):
        self._custom_details = value

    @property
    def quantity(self):
        """Convenience property for quantity/units from attached detail record."""
        det = self.details
        if not det:
            return None
        if det.get('property_type') == 'REIT' and det.get('area') is not None:
            return det.get('area')
        return det.get('quantity') or det.get('units') or det.get('weight_grams')

    @property
    def purchase_price(self):
        """Convenience property for purchase price from attached detail record."""
        det = self.details
        if not det:
            return None
        return (
            det.get('purchase_price')
            or det.get('average_buy_price')
            or det.get('purchase_price_per_share')
            or det.get('purchase_nav')
            or det.get('average_purchase_nav')
        )
