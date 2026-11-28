import uuid
from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

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
        help_text="Canonical Instrument UUID (Primary DB)",
    )
    instrument_ref = models.ForeignKey(
        'market_data.MarketInstrumentReference',
        on_delete=models.PROTECT,
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
        default=TrustClass.UNVERIFIED,
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
                fields=['instrument_id', 'series', 'effective_at', 'price_type', 'source'],
                condition=models.Q(status=ObservationStatus.PUBLISHED, correction_of__isnull=True),
                name='uniq_published_obs_series',
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
        if self.value is not None and self.value < Decimal('0'):
            raise ValidationError({'value': 'Price observation value must not be negative.'})
        if self.open_price is not None and self.open_price <= Decimal('0'):
            raise ValidationError({'open_price': 'Open price must be positive.'})
        if self.low_price is not None and self.high_price is not None and self.high_price < self.low_price:
            raise ValidationError({'high_price': 'High price cannot be lower than Low price.'})
        if self.open_price is not None and self.high_price is not None and self.open_price > self.high_price:
            raise ValidationError({'open_price': 'Open price cannot exceed High price.'})
        if self.open_price is not None and self.low_price is not None and self.open_price < self.low_price:
            raise ValidationError({'open_price': 'Open price cannot be below Low price.'})
        if self.value is not None and self.high_price is not None and self.value > self.high_price:
            raise ValidationError({'value': 'Close/value cannot exceed High price.'})
        if self.value is not None and self.low_price is not None and self.value < self.low_price:
            raise ValidationError({'value': 'Close/value cannot be below Low price.'})
        if self.volume is not None and self.volume < 0:
            raise ValidationError({'volume': 'Volume cannot be negative.'})
        if not self.currency or not self.unit or not self.source:
            raise ValidationError('Currency, quotation unit and source are required.')
        if self.effective_at and self.effective_at > timezone.now() + timedelta(minutes=5):
            raise ValidationError({'effective_at': 'Effective timestamp cannot be in the future.'})
        if self.is_synthetic and self.trust_class != TrustClass.SYNTHETIC:
            raise ValidationError({'trust_class': 'Synthetic observations must use SYNTHETIC trust class.'})
        if self.correction_of and not self.correction_reason:
            raise ValidationError({'correction_reason': 'Correction reason is required when correcting an observation.'})
        if self.series_id:
            series = self.series
            if series:
                mismatches = {}
                if series.instrument_id != self.instrument_id:
                    mismatches['series'] = 'Selected series belongs to a different canonical instrument.'
                if series.price_type != self.price_type:
                    mismatches['price_type'] = 'Price type must match the selected series.'
                if series.currency != self.currency:
                    mismatches['currency'] = 'Currency must match the selected series.'
                if series.unit != self.unit:
                    mismatches['unit'] = 'Quotation unit must match the selected series.'
                if series.source != self.source:
                    mismatches['source'] = 'Source must match the selected series.'
                if mismatches:
                    raise ValidationError(mismatches)
        elif self.status in (ObservationStatus.PENDING_REVIEW, ObservationStatus.PUBLISHED):
            raise ValidationError({'series': 'An observation must have an exact series before review or publication.'})

    def save(self, *args, **kwargs):
        """Enforce series identity, provenance and immutable published records.

        If a draft is moved to review without a pre-created series, create the exact
        series from its complete identity dimensions. This never merges providers,
        currencies, units or price types.
        """
        from django.db import transaction

        from apps.market_data.models.series import MarketDataSeries

        using = kwargs.get('using') or self._state.db or 'market_data'
        if using != 'market_data':
            raise ValidationError('PriceObservation must be stored in the market_data database.')
        kwargs['using'] = using
        is_new = self._state.adding
        previous = None
        if not is_new and self.pk:
            previous = type(self).objects.using(using).filter(pk=self.pk).values().first()
            if previous and previous.get('status') == ObservationStatus.PUBLISHED:
                immutable = [field.attname for field in self._meta.concrete_fields if field.name != 'updated_at']
                changed = [name for name in immutable if previous.get(name) != getattr(self, name)]
                if changed:
                    raise ValidationError(
                        'Published observations are immutable. Create a correction instead. '
                        f'Changed fields: {", ".join(changed)}'
                    )
                # A no-op save must not issue an UPDATE against the PostgreSQL guard trigger.
                return self

        if self.status in (ObservationStatus.PENDING_REVIEW, ObservationStatus.PUBLISHED) and not self.series_id:
            instrument = Instrument.objects.using('default').filter(pk=self.instrument_id).first()
            if instrument is None:
                raise ValidationError({'instrument_id': 'Canonical instrument does not exist in the primary database.'})
            series, _ = MarketDataSeries.objects.using(using).get_or_create(
                instrument_id=self.instrument_id,
                exchange=instrument.exchange or '',
                source=self.source,
                price_type=self.price_type,
                currency=self.currency,
                unit=self.unit,
                pricing_methodology='',
                adjustment_methodology='RAW',
                defaults={'description': f'Auto-created exact series for {instrument.symbol}'},
            )
            self.series = series
            if 'update_fields' in kwargs and kwargs['update_fields'] is not None:
                fields_set = set(kwargs['update_fields'])
                fields_set.add('series')
                fields_set.add('series_id')
                kwargs['update_fields'] = list(fields_set)

        if self.status == ObservationStatus.PUBLISHED:
            if not self.published_at:
                self.published_at = timezone.now()
            if self.trust_class == TrustClass.UNVERIFIED:
                src = (self.source or '').upper()
                if any(k in src for k in ('OFFICIAL', 'NSE', 'BSE', 'AMFI', 'IBJA', 'GOLD', 'MCX', 'RBI')):
                    self.trust_class = TrustClass.VERIFIED_OFFICIAL
                elif any(k in src for k in ('YAHOO', 'MFAPI', 'FEED', 'SECONDARY', 'HISTORICAL', 'COINGECKO')):
                    self.trust_class = TrustClass.VERIFIED_PERMITTED_SECONDARY
                elif any(k in src for k in ('MANUAL', 'CSV')):
                    self.trust_class = TrustClass.MANUAL_VERIFIED
        self.full_clean(exclude=None, validate_unique=False, validate_constraints=False)

        was_published = bool(previous and previous.get('status') == ObservationStatus.PUBLISHED)
        became_published = self.status == ObservationStatus.PUBLISHED and not was_published
        managed_publication = getattr(self, '_publication_managed', False)
        if became_published and not is_new and not managed_publication:
            raise ValidationError('Use PriceObservation.publish() to transition a reviewed observation to PUBLISHED.')
        with transaction.atomic(using=using):
            result = super().save(*args, **kwargs)
            # Defensive compatibility for internal ingestion that creates an already
            # published record: it still advances the version and emits the outbox.
            # Public API serializers never allow clients to set PUBLISHED or trust.
            if became_published and not managed_publication and self.series_id:
                series = MarketDataSeries.objects.using(using).select_for_update().get(pk=self.series_id)
                series.data_version += 1
                series.last_published_at = self.published_at
                series._publication_managed = True
                try:
                    series.save(using=using, update_fields=['data_version', 'last_published_at', 'updated_at'])
                finally:
                    series._publication_managed = False
                from apps.market_data.models.publication_event import MarketDataPublicationEvent
                MarketDataPublicationEvent.objects.using(using).create(
                    observation_id=self.id, instrument_id=self.instrument_id,
                    series_id=self.series_id, effective_at=self.effective_at,
                    price_type=self.price_type, value=self.value, currency=self.currency,
                    data_version=series.data_version,
                )
        return result

    def delete(self, *args, **kwargs):
        if self.status == ObservationStatus.PUBLISHED:
            raise ValidationError('Published observations cannot be deleted; create a correction instead.')
        return super().delete(*args, **kwargs)

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
        """Atomically publish a reviewed observation and emit its durable outbox event.

        Both the observation and its exact series are locked before changing state.
        This prevents two concurrent publishers from publishing the same record or
        losing a monotonic series-version increment.
        """
        from django.db import transaction

        from apps.market_data.models.publication_event import MarketDataPublicationEvent
        from apps.market_data.models.series import MarketDataSeries

        if not publisher:
            raise ValidationError('A publisher must be specified to publish an observation.')
        active = getattr(publisher, 'is_active', True)
        authorized = bool(
            active and (
                getattr(publisher, 'is_system', False)
                or getattr(publisher, 'is_superuser', False)
                or getattr(publisher, 'is_staff', False)
                or (hasattr(publisher, 'groups') and publisher.groups.filter(name='MarketDataPublisher').exists())
            )
        )
        if not authorized:
            raise ValidationError('An active MarketDataPublisher, staff user or superuser is required.')

        using = 'market_data'
        with transaction.atomic(using=using):
            try:
                locked_observation = type(self).objects.using(using).select_for_update().get(pk=self.pk)
            except type(self).DoesNotExist:
                raise ValidationError('Observation no longer exists.')

            if locked_observation.status == ObservationStatus.PUBLISHED:
                self.status = locked_observation.status
                self.published_at = locked_observation.published_at
                self.published_by_id = locked_observation.published_by_id
                self.trust_class = locked_observation.trust_class
                return
            if locked_observation.status != ObservationStatus.PENDING_REVIEW:
                raise ValidationError(
                    f"Cannot publish observation in status '{locked_observation.status}'. Must be in PENDING_REVIEW."
                )
            if not locked_observation.series_id:
                raise ValidationError('An exact market-data series is required before publication.')

            series = MarketDataSeries.objects.using(using).select_for_update().get(
                pk=locked_observation.series_id
            )
            if locked_observation.trust_class == TrustClass.UNVERIFIED:
                src = (locked_observation.source or '').upper()
                if any(k in src for k in ('OFFICIAL', 'NSE', 'BSE', 'AMFI', 'IBJA', 'GOLD', 'MCX', 'RBI')):
                    locked_observation.trust_class = TrustClass.VERIFIED_OFFICIAL
                elif any(k in src for k in ('YAHOO', 'MFAPI', 'FEED', 'SECONDARY', 'HISTORICAL', 'COINGECKO')):
                    locked_observation.trust_class = TrustClass.VERIFIED_PERMITTED_SECONDARY
                elif any(k in src for k in ('MANUAL', 'CSV')):
                    locked_observation.trust_class = TrustClass.MANUAL_VERIFIED

            published_at = timezone.now()
            locked_observation.status = ObservationStatus.PUBLISHED
            locked_observation.published_by_id = getattr(publisher, 'id', publisher)
            locked_observation.published_at = published_at

            series.data_version = (series.data_version or 0) + 1
            series.last_published_at = published_at
            series._publication_managed = True
            try:
                series.save(
                    using=using,
                    update_fields=['data_version', 'last_published_at', 'updated_at'],
                )
            finally:
                series._publication_managed = False

            locked_observation._publication_managed = True
            try:
                locked_observation.save(using=using)
            finally:
                locked_observation._publication_managed = False

            MarketDataPublicationEvent.objects.using(using).create(
                observation_id=locked_observation.id,
                instrument_id=locked_observation.instrument_id,
                series_id=locked_observation.series_id,
                effective_at=locked_observation.effective_at,
                price_type=locked_observation.price_type,
                value=locked_observation.value,
                currency=locked_observation.currency,
                data_version=series.data_version,
            )

            from apps.market_data.models.coverage import InstrumentCoverage
            InstrumentCoverage.objects.using(using).filter(
                instrument_id=locked_observation.instrument_id
            ).update(last_published_at=published_at)

            from apps.market_data.models.worklist import MarketDataWorklistItem, WorklistItemStatus
            eff_date = locked_observation.effective_at.astimezone(
                ZoneInfo('Asia/Kolkata')
            ).date()
            MarketDataWorklistItem.objects.using(using).filter(
                instrument_id=locked_observation.instrument_id,
                effective_date=eff_date,
            ).update(
                status=WorklistItemStatus.COMPLETED,
                last_published_price=locked_observation.value,
                last_published_date=published_at,
            )

            # Keep the caller's in-memory object aligned with the committed row.
            self.status = locked_observation.status
            self.published_by_id = locked_observation.published_by_id
            self.published_at = locked_observation.published_at
            self.trust_class = locked_observation.trust_class
            self.series = series

    def reject(self, reviewer, reason: str) -> None:
        if self.status == ObservationStatus.PUBLISHED:
            raise ValidationError('Cannot reject an already published observation.')
        self.status = ObservationStatus.REJECTED
        self.rejection_reason = reason
        self.published_by = reviewer
        self.save()
