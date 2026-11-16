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
        on_delete=models.CASCADE,
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

    def __str__(self) -> str:
        return f"{self.display_name} ({self.asset_type}) - {self.currency} {self.current_value}"
