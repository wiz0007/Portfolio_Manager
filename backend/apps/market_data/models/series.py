import uuid

from django.db import models
from django.core.exceptions import ValidationError

from apps.market_data.models.coverage import PriceType, QuotationUnit
from apps.market_data.models.instrument_reference import MarketInstrumentReference


class MarketDataSeriesQuerySet(models.QuerySet):
    IDENTITY_FIELDS = {
        'instrument_id', 'exchange', 'source', 'price_type', 'currency', 'unit',
        'pricing_methodology', 'adjustment_methodology', 'market_timezone',
    }

    def update(self, **kwargs):
        if self.IDENTITY_FIELDS.intersection(kwargs) and self.filter(observations__isnull=False).exists():
            raise ValidationError('A series with observations has immutable identity dimensions.')
        if 'data_version' in kwargs:
            raise ValidationError('Series data_version can only be advanced by the publication lifecycle.')
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, **kwargs):
        if self.IDENTITY_FIELDS.intersection(fields) or 'data_version' in fields:
            raise ValidationError('Series identity and version fields cannot be bulk-updated.')
        return super().bulk_update(objs, fields, **kwargs)


class MarketDataSeries(models.Model):
    objects = MarketDataSeriesQuerySet.as_manager()

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

    IDENTITY_FIELDS = (
        'instrument_id', 'exchange', 'source', 'price_type', 'currency', 'unit',
        'pricing_methodology', 'adjustment_methodology', 'market_timezone',
    )

    def save(self, *args, **kwargs):
        using = kwargs.get('using') or self._state.db or 'market_data'
        if using != 'market_data':
            raise ValidationError('MarketDataSeries must be stored in the market_data database.')
        if not self._state.adding and self.pk:
            previous = type(self).objects.using(using).filter(pk=self.pk).values(
                *self.IDENTITY_FIELDS, 'data_version'
            ).first()
            if previous:
                changed = [field for field in self.IDENTITY_FIELDS if previous[field] != getattr(self, field)]
                if changed and self.observations.exists():
                    raise ValidationError(
                        'Series identity cannot change after observations exist: ' + ', '.join(changed)
                    )
                if self.data_version < previous['data_version']:
                    raise ValidationError('Series data_version cannot decrease.')
        self.full_clean(validate_unique=False, validate_constraints=False)
        kwargs['using'] = using
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.observations.exists():
            raise ValidationError('A series with observations cannot be deleted.')
        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"Series({self.instrument_id} - {self.exchange}:{self.price_type} [{self.currency}])"
