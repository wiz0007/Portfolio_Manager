import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.market_data.models.common import CrossDbQuerySet
from apps.market_data.models.coverage import PriceType, QuotationUnit
from apps.market_data.models.instrument import Instrument


class ObservationStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Review'
    PUBLISHED = 'PUBLISHED', 'Published'
    REJECTED = 'REJECTED', 'Rejected'


class TrustClass(models.TextChoices):
    VERIFIED_OFFICIAL = 'VERIFIED_OFFICIAL', 'Verified Official'
    VERIFIED_PERMITTED_SECONDARY = 'VERIFIED_PERMITTED_SECONDARY', 'Verified Permitted Secondary'
    MANUAL_VERIFIED = 'MANUAL_VERIFIED', 'Manual Verified'
    SYNTHETIC = 'SYNTHETIC', 'Synthetic'
    UNVERIFIED = 'UNVERIFIED', 'Unverified'
    CORRECTED = 'CORRECTED', 'Corrected'


class PriceObservation(models.Model):
    """
    Append-only, auditable price observation record.
    Follows lifecycle: draft -> pending_review -> published.
    Published observations are immutable; corrections create new observations chained via correction_of.
    """

    objects = CrossDbQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument_id = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        help_text="Canonical Instrument UUID (Primary DB)",
    )
    instrument_ref = models.ForeignKey(
        'market_data.MarketInstrumentReference',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='observations',
        db_index=True,
    )
    series = models.ForeignKey(
        'market_data.MarketDataSeries',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='observations',
        db_index=True,
    )
    price_type = models.CharField(
        max_length=32,
        choices=PriceType.choices,
        default=PriceType.LTP,
        db_index=True,
    )
    value = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        help_text='Observed price, NAV, or valuation amount in Decimal format.',
    )
    open_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=10, default='INR')
    unit = models.CharField(
        max_length=32,
        choices=QuotationUnit.choices,
        default=QuotationUnit.UNITS,
    )
    effective_at = models.DateTimeField(
        db_index=True,
        help_text='Market effective date/timestamp in UTC.',
    )
    source = models.CharField(max_length=64, default='MANUAL_VERIFIED')
    source_reference = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Evidence or reference, e.g. NSE website URL, AMFI bulletin, Circular ID.',
    )
    notes = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=32,
        choices=ObservationStatus.choices,
        default=ObservationStatus.DRAFT,
        db_index=True,
    )
    trust_class = models.CharField(
        max_length=32,
        choices=TrustClass.choices,
        default=TrustClass.VERIFIED_OFFICIAL,
        db_index=True,
    )
    is_synthetic = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Explicit flag identifying synthetic development observation.',
    )
    recorded_by_id = models.UUIDField(null=True, blank=True, db_index=True, help_text="Actor User UUID (Primary DB)")
    published_by_id = models.UUIDField(null=True, blank=True, db_index=True, help_text="Publisher User UUID (Primary DB)")
    published_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')

    correction_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrections',
        help_text='Original observation this record supersedes.',
    )
    correction_reason = models.TextField(
        blank=True,
        default='',
        help_text='Mandatory explanation if this is a correction.',
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'price_observations'
        ordering = ['-effective_at', '-created_at']
        indexes = [
            models.Index(fields=['instrument_id', 'status', '-effective_at'], name='obs_inst_status_eff_idx'),
            models.Index(fields=['status', '-created_at'], name='obs_status_created_idx'),
            models.Index(fields=['effective_at'], name='obs_effective_idx'),
            models.Index(fields=['instrument_id', 'effective_at', 'price_type'], name='obs_inst_eff_type_idx'),
            models.Index(fields=['trust_class'], name='obs_trust_class_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['instrument_id', 'effective_at', 'price_type', 'source'],
                condition=models.Q(status=ObservationStatus.PUBLISHED),
                name='uniq_published_obs',
            )
        ]

    def __init__(self, *args, **kwargs):
        inst = kwargs.pop('instrument', None)
        rec = kwargs.pop('recorded_by', None)
        pub = kwargs.pop('published_by', None)
        super().__init__(*args, **kwargs)
        if inst is not None:
            self.instrument_id = getattr(inst, 'id', inst)
            self._cached_instrument = inst if hasattr(inst, 'id') else None
        if rec is not None:
            self.recorded_by_id = getattr(rec, 'id', rec)
            self._cached_recorded_by = rec if hasattr(rec, 'id') else None
        if pub is not None:
            self.published_by_id = getattr(pub, 'id', pub)
            self._cached_published_by = pub if hasattr(pub, 'id') else None
        if not self._state.db and 'market_data' in getattr(settings, 'DATABASES', {}):
            self._state.db = 'market_data'

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

    @property
    def recorded_by(self):
        if hasattr(self, '_cached_recorded_by') and self._cached_recorded_by is not None:
            return self._cached_recorded_by
        if not self.recorded_by_id:
            return None
        from apps.users.models import User
        self._cached_recorded_by = User.objects.using('default').filter(id=self.recorded_by_id).first()
        return self._cached_recorded_by

    @recorded_by.setter
    def recorded_by(self, value):
        self.recorded_by_id = getattr(value, 'id', value) if value else None
        self._cached_recorded_by = value

    @property
    def published_by(self):
        if hasattr(self, '_cached_published_by') and self._cached_published_by is not None:
            return self._cached_published_by
        if not self.published_by_id:
            return None
        from apps.users.models import User
        self._cached_published_by = User.objects.using('default').filter(id=self.published_by_id).first()
        return self._cached_published_by

    @published_by.setter
    def published_by(self, value):
        self.published_by_id = getattr(value, 'id', value) if value else None
        self._cached_published_by = value

    def clean(self):
        super().clean()
        if self.value is not None and self.value <= Decimal('0'):
            raise ValidationError({'value': 'Price observation value must be strictly positive.'})
        if self.open_price is not None and self.open_price <= Decimal('0'):
            raise ValidationError({'open_price': 'Open price must be positive.'})
        if self.high_price is not None and self.low_price is not None:
            if self.high_price < self.low_price:
                raise ValidationError({'high_price': 'High price cannot be lower than Low price.'})
        if self.effective_at and self.effective_at > timezone.now() + timezone.timedelta(minutes=5):
            raise ValidationError({'effective_at': 'Effective timestamp cannot be in the future.'})
        if self.correction_of and not self.correction_reason:
            raise ValidationError({'correction_reason': 'Correction reason is required when correcting an observation.'})

    def submit_for_review(self) -> None:
        """
        Transition draft observation to pending_review.
        """
        if self.status != ObservationStatus.DRAFT:
            raise ValidationError(
                f"Cannot submit observation in status '{self.status}' for review. Must be in DRAFT."
            )
        self.status = ObservationStatus.PENDING_REVIEW
        self.save(update_fields=['status', 'updated_at'])

    def publish(self, publisher) -> None:
        """
        Transition observation to published. Once published, record is immutable.
        Atomic on secondary database ('market_data'). Emits durable publication outbox event.
        """
        if self.status == ObservationStatus.PUBLISHED:
            return
        if self.status != ObservationStatus.PENDING_REVIEW:
            raise ValidationError(
                f"Cannot publish observation in status '{self.status}'. Must be in PENDING_REVIEW."
            )
        if not publisher:
            raise ValidationError('A publisher must be specified to publish an observation.')

        from django.db import transaction

        from apps.market_data.models.publication_event import MarketDataPublicationEvent

        with transaction.atomic(using='market_data'):
            self.status = ObservationStatus.PUBLISHED
            self.published_by = publisher
            self.published_at = timezone.now()

            # Increment series monotonic data version
            if self.series:
                self.series.data_version = (self.series.data_version or 0) + 1
                self.series.last_published_at = self.published_at
                self.series.save(using='market_data', update_fields=['data_version', 'last_published_at', 'updated_at'])

            self.save(using='market_data')

            # Create durable publication event in secondary outbox
            MarketDataPublicationEvent.objects.using('market_data').create(
                observation_id=self.id,
                instrument_id=self.instrument_id,
                series_id=self.series_id,
                effective_at=self.effective_at,
                price_type=self.price_type,
                value=self.value,
                currency=self.currency,
                data_version=self.series.data_version if self.series else 1,
            )

            # Update coverage last_published_at
            if self.instrument and self.instrument.coverage:
                cov = self.instrument.coverage
                cov.last_published_at = self.published_at
                cov.save(using='market_data', update_fields=['last_published_at', 'updated_at'])

            # Mark any corresponding worklist item as COMPLETED
            from apps.market_data.models.worklist import MarketDataWorklistItem, WorklistItemStatus
            eff_date = self.effective_at.date() if hasattr(self.effective_at, 'date') else self.effective_at
            MarketDataWorklistItem.objects.using('market_data').filter(
                instrument_id=self.instrument_id,
                effective_date=eff_date,
            ).update(
                status=WorklistItemStatus.COMPLETED,
                last_published_price=self.value,
                last_published_date=self.published_at,
            )

    def reject(self, reviewer, reason: str) -> None:
        if self.status == ObservationStatus.PUBLISHED:
            raise ValidationError('Cannot reject an already published observation.')
        self.status = ObservationStatus.REJECTED
        self.rejection_reason = reason
        self.published_by = reviewer
        self.save()
