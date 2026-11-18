import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.market_data.models.coverage import PriceType, QuotationUnit
from apps.market_data.models.instrument import Instrument


class ObservationStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PENDING_REVIEW = 'PENDING_REVIEW', 'Pending Review'
    PUBLISHED = 'PUBLISHED', 'Published'
    REJECTED = 'REJECTED', 'Rejected'


class PriceObservation(models.Model):
    """
    Append-only, auditable price observation record.
    Follows lifecycle: draft -> pending_review -> published.
    Published observations are immutable; corrections create new observations chained via correction_of.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
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
    is_synthetic = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Explicit flag identifying synthetic development observation.',
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recorded_observations',
        db_index=True,
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_observations',
    )
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
            models.Index(fields=['instrument', 'status', '-effective_at'], name='obs_inst_status_eff_idx'),
            models.Index(fields=['status', '-created_at'], name='obs_status_created_idx'),
            models.Index(fields=['effective_at'], name='obs_effective_idx'),
        ]

    def clean(self):
        super().clean()
        if self.value is not None and self.value <= Decimal('0'):
            raise ValidationError({'value': 'Price observation value must be strictly positive.'})
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
        Synchronizes to MarketDataPoint, coverage, and worklists.
        """
        if self.status == ObservationStatus.PUBLISHED:
            return
        if self.status != ObservationStatus.PENDING_REVIEW:
            raise ValidationError(
                f"Cannot publish observation in status '{self.status}'. Must be in PENDING_REVIEW."
            )
        if not publisher:
            raise ValidationError('A publisher must be specified to publish an observation.')
        self.status = ObservationStatus.PUBLISHED
        self.published_by = publisher
        self.published_at = timezone.now()
        self.save()

        # 1. Sync to MarketDataPoint
        from apps.market_data.models.market_data_point import MarketDataPoint
        MarketDataPoint.objects.update_or_create(
            instrument=self.instrument,
            timestamp=self.effective_at,
            interval='1D',
            provider=self.source or 'MANUAL_VERIFIED',
            defaults={
                'price': self.value,
                'close_price': self.value,
                'is_synthetic': self.is_synthetic,
            },
        )

        # 2. Update coverage last_published_at
        if hasattr(self.instrument, 'coverage'):
            cov = self.instrument.coverage
            cov.last_published_at = self.published_at
            cov.save(update_fields=['last_published_at', 'updated_at'])

        # 3. Mark any corresponding worklist item as COMPLETED
        from apps.market_data.models.worklist import MarketDataWorklistItem, WorklistItemStatus
        eff_date = self.effective_at.date() if hasattr(self.effective_at, 'date') else self.effective_at
        MarketDataWorklistItem.objects.filter(
            instrument=self.instrument,
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
