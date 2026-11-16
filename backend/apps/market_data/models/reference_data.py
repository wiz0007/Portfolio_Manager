import uuid
from decimal import Decimal

from django.db import models

from apps.market_data.models.instrument import Instrument


class MarketCapCategory(models.TextChoices):
    LARGE_CAP = 'LARGE_CAP', 'Large Cap'
    MID_CAP = 'MID_CAP', 'Mid Cap'
    SMALL_CAP = 'SMALL_CAP', 'Small Cap'
    MICRO_CAP = 'MICRO_CAP', 'Micro Cap'
    NOT_APPLICABLE = 'NOT_APPLICABLE', 'Not Applicable'


class InstrumentReferenceData(models.Model):
    """
    Descriptive, sectoral, and trading reference metadata for an instrument.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument = models.OneToOneField(
        Instrument,
        on_delete=models.CASCADE,
        related_name='reference_data',
    )
    sector = models.CharField(max_length=128, blank=True, default='', db_index=True)
    industry = models.CharField(max_length=128, blank=True, default='')
    market_cap_category = models.CharField(
        max_length=32,
        choices=MarketCapCategory.choices,
        default=MarketCapCategory.NOT_APPLICABLE,
    )
    lot_size = models.PositiveIntegerField(default=1)
    tick_size = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal('0.05'))
    website = models.URLField(blank=True, default='')
    details = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instrument_reference_data'

    def __str__(self) -> str:
        return f"RefData({self.instrument.symbol} - {self.sector})"
