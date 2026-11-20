import uuid

from django.db import models

from apps.market_data.models.common import CrossDbQuerySet
from apps.market_data.models.instrument import Instrument


class PriceType(models.TextChoices):
    LTP = 'LTP', 'Last Traded Price'
    NAV = 'NAV', 'Net Asset Value'
    CLOSE = 'CLOSE', 'Daily Closing Price'
    INDICATIVE_VALUATION = 'INDICATIVE_VALUATION', 'Indicative Valuation'
    APPRAISAL = 'APPRAISAL', 'Independent Appraisal'


class QuotationUnit(models.TextChoices):
    SHARES = 'SHARES', 'Per Share'
    UNITS = 'UNITS', 'Per Unit'
    GRAMS_24K = 'GRAMS_24K', 'Per Gram 24K'
    GRAMS_22K = 'GRAMS_22K', 'Per Gram 22K'
    CURRENCY = 'CURRENCY', 'Absolute Currency Amount'


class CollectionCadence(models.TextChoices):
    EVERY_TRADING_DAY = 'EVERY_TRADING_DAY', 'Every Trading Day'
    EVERY_BUSINESS_DAY = 'EVERY_BUSINESS_DAY', 'Every Business Day'
    WEEKLY = 'WEEKLY', 'Weekly'
    MONTHLY = 'MONTHLY', 'Monthly'
    ON_DEMAND = 'ON_DEMAND', 'On Demand'
    USER_REVIEW = 'USER_REVIEW', 'User Review'


class CoverageStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active Coverage'
    PAUSED = 'PAUSED', 'Temporarily Paused'
    RETIRED = 'RETIRED', 'Retired'
    EXCLUDED = 'EXCLUDED', 'Explicitly Excluded'


class InstrumentCoverage(models.Model):
    """
    Policy governing how, when, and from where market prices are collected for an instrument.
    Enforces distinct cadences, quotation bases, and freshness windows.
    """

    objects = CrossDbQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument_id = models.UUIDField(
        unique=True,
        db_index=True,
        default=uuid.uuid4,
        help_text="Canonical Instrument UUID (Primary DB)",
    )
    price_type = models.CharField(
        max_length=32,
        choices=PriceType.choices,
        default=PriceType.LTP,
        db_index=True,
    )
    currency = models.CharField(max_length=10, default='INR')
    unit = models.CharField(
        max_length=32,
        choices=QuotationUnit.choices,
        default=QuotationUnit.UNITS,
    )
    cadence = models.CharField(
        max_length=32,
        choices=CollectionCadence.choices,
        default=CollectionCadence.EVERY_TRADING_DAY,
        db_index=True,
    )
    market_timezone = models.CharField(max_length=64, default='Asia/Kolkata')
    freshness_hours = models.PositiveIntegerField(
        default=24,
        help_text='Threshold after which observation is marked stale.',
    )
    grace_period_hours = models.PositiveIntegerField(
        default=12,
        help_text='Grace period for off-market days or holiday delays.',
    )
    preferred_source = models.CharField(max_length=64, default='MANUAL_VERIFIED')
    status = models.CharField(
        max_length=32,
        choices=CoverageStatus.choices,
        default=CoverageStatus.ACTIVE,
        db_index=True,
    )
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_published_at = models.DateTimeField(null=True, blank=True)
    inclusion_reason = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instrument_coverages'
        indexes = [
            models.Index(fields=['status', 'cadence'], name='cov_status_cad_idx'),
        ]

    def __init__(self, *args, **kwargs):
        inst = kwargs.pop('instrument', None)
        super().__init__(*args, **kwargs)
        if inst is not None:
            self.instrument_id = getattr(inst, 'id', inst)
            self._cached_instrument = inst if hasattr(inst, 'id') else None

    @property
    def instrument(self):
        if hasattr(self, '_cached_instrument') and self._cached_instrument is not None:
            return self._cached_instrument
        if not self.instrument_id:
            return None
        self._cached_instrument = Instrument.objects.using('default').filter(id=self.instrument_id).first()
        return self._cached_instrument

    @instrument.setter
    def instrument(self, value):
        self.instrument_id = getattr(value, 'id', value) if value else None
        self._cached_instrument = value

    def __str__(self) -> str:
        inst = self.instrument
        sym = inst.symbol if inst else str(self.instrument_id)
        return f"Coverage({sym} - {self.cadence}:{self.price_type})"
