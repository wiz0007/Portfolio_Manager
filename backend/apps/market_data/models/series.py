import uuid

from django.db import models

from apps.market_data.models.coverage import PriceType, QuotationUnit
from apps.market_data.models.instrument_reference import MarketInstrumentReference


class MarketDataSeries(models.Model):
    """
    Independently identifiable time series metadata in the Market Data Storage Database.
    Prevents silent mixing of observations from different exchanges, currencies,
    price types, or adjustment methodologies.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument_id = models.UUIDField(db_index=True, help_text="Canonical Instrument UUID")
    instrument_ref = models.ForeignKey(
        MarketInstrumentReference,
        on_delete=models.CASCADE,
        related_name='series',
        null=True,
        blank=True,
    )
    exchange = models.CharField(max_length=32, blank=True, default='', db_index=True)
    source = models.CharField(max_length=64, default='MANUAL', db_index=True)
    price_type = models.CharField(
        max_length=32,
        choices=PriceType.choices,
        default=PriceType.CLOSE,
        db_index=True,
    )
    currency = models.CharField(max_length=10, default='INR')
    unit = models.CharField(
        max_length=32,
        choices=QuotationUnit.choices,
        default=QuotationUnit.SHARES,
    )
    pricing_methodology = models.CharField(max_length=64, blank=True, default='')
    adjustment_methodology = models.CharField(max_length=64, blank=True, default='RAW')
    market_timezone = models.CharField(max_length=64, default='Asia/Kolkata')
    data_version = models.PositiveIntegerField(
        default=1,
        help_text='Monotonically increasing version incremented on every publication, correction, or approved backfill.',
    )
    last_published_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    description = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'market_data_series'
        ordering = ['instrument_id', 'exchange', 'price_type']
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'instrument_id',
                    'exchange',
                    'source',
                    'price_type',
                    'currency',
                    'unit',
                    'pricing_methodology',
                    'adjustment_methodology',
                ],
                name='uniq_market_series_dim',
            )
        ]
        indexes = [
            models.Index(fields=['instrument_id', 'price_type'], name='mds_inst_type_idx'),
            models.Index(fields=['source', 'exchange'], name='mds_src_exch_idx'),
        ]

    def __str__(self) -> str:
        return f"Series({self.instrument_id} - {self.exchange}:{self.price_type} [{self.currency}])"
