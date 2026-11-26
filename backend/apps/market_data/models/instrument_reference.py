
from django.db import models

from apps.market_data.models.instrument import AssetClass


class MarketInstrumentReference(models.Model):
    """
    Lightweight, synchronized identity projection of a canonical Instrument
    stored in the Market Data Storage Database.

    The primary portfolio database remains authoritative for instrument definitions;
    this projection contains only the attributes necessary for market data series,
    daily observations, quotes, and coverage resolution.
    """

    id = models.UUIDField(primary_key=True, editable=False, help_text="Canonical Instrument UUID")
    symbol = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    asset_class = models.CharField(
        max_length=32,
        choices=AssetClass.choices,
        default=AssetClass.EQUITY,
        db_index=True,
    )
    product_type = models.CharField(max_length=64, blank=True, default='', db_index=True)
    exchange = models.CharField(max_length=32, blank=True, default='', db_index=True)
    currency = models.CharField(max_length=10, default='INR')
    isin = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    scheme_code = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    security_code = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    sync_version = models.PositiveIntegerField(default=1)
    last_synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'market_instrument_references'
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol', 'exchange'], name='mir_sym_exch_idx'),
            models.Index(fields=['asset_class', 'is_active'], name='mir_class_active_idx'),
            models.Index(fields=['isin'], name='mir_isin_idx'),
            models.Index(fields=['scheme_code'], name='mir_scheme_idx'),
        ]

    def __str__(self) -> str:
        exchange_str = f" ({self.exchange})" if self.exchange else ""
        return f"[MarketRef] {self.symbol}{exchange_str} - {self.name}"
