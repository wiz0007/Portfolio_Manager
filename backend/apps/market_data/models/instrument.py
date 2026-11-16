import uuid
from typing import Optional

from django.db import models


class AssetClass(models.TextChoices):
    EQUITY = 'EQUITY', 'Listed Equity / Stock'
    MUTUAL_FUND = 'MUTUAL_FUND', 'Mutual Fund'
    COMMODITY = 'COMMODITY', 'Commodity / Precious Metal'
    FIXED_INCOME = 'FIXED_INCOME', 'Fixed Income / Debt'
    REAL_ESTATE = 'REAL_ESTATE', 'Real Estate'
    CRYPTO = 'CRYPTO', 'Cryptocurrency'
    INDEX = 'INDEX', 'Market Index'
    CASH_EQUIVALENT = 'CASH_EQUIVALENT', 'Cash Equivalent'


class Instrument(models.Model):
    """
    Standardized, provider-independent financial instrument definition.
    Represents equities, mutual funds, indices, commodities, etc.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    asset_class = models.CharField(
        max_length=32,
        choices=AssetClass.choices,
        default=AssetClass.EQUITY,
        db_index=True,
    )
    exchange = models.CharField(max_length=32, blank=True, default='', db_index=True)
    currency = models.CharField(max_length=10, default='INR')
    isin = models.CharField(max_length=32, blank=True, null=True, unique=True)
    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instruments'
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol', 'exchange'], name='inst_sym_exch_idx'),
            models.Index(fields=['asset_class', 'is_active'], name='inst_class_active_idx'),
            models.Index(fields=['name'], name='inst_name_idx'),
        ]

    def __str__(self) -> str:
        exchange_str = f" ({self.exchange})" if self.exchange else ""
        return f"{self.symbol}{exchange_str} - {self.name}"

    @property
    def latest_quote(self) -> Optional['MarketDataPoint']:
        """Returns the most recent market data point for this instrument."""
        return self.data_points.order_by('-timestamp').first()
