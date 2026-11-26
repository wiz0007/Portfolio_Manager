import uuid

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


class InstrumentStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    MATURED = 'MATURED', 'Matured'
    DELISTED = 'DELISTED', 'Delisted'
    INACTIVE = 'INACTIVE', 'Inactive'


class InstrumentQuerySet(models.QuerySet):
    IDENTITY_FIELDS = {
        'symbol', 'name', 'asset_class', 'product_type', 'exchange', 'currency',
        'isin', 'scheme_code', 'security_code', 'status', 'is_active', 'identity_version',
    }

    def update(self, **kwargs):
        from django.core.exceptions import ValidationError
        if self.IDENTITY_FIELDS.intersection(kwargs):
            raise ValidationError(
                'Canonical instrument identity must be changed through Instrument.save() so its outbox event is recorded.'
            )
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, **kwargs):
        from django.core.exceptions import ValidationError
        if self.IDENTITY_FIELDS.intersection(fields):
            raise ValidationError(
                'Bulk identity updates are disabled. Save each Instrument so its outbox event is recorded.'
            )
        return super().bulk_update(objs, fields, **kwargs)

    def bulk_create(self, objs, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Bulk creation of canonical instruments is disabled; save each Instrument to emit its outbox event.')


class Instrument(models.Model):
    objects = InstrumentQuerySet.as_manager()

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
    product_type = models.CharField(max_length=64, blank=True, default='', db_index=True)
    exchange = models.CharField(max_length=32, blank=True, default='', db_index=True)
    currency = models.CharField(max_length=10, default='INR')
    isin = models.CharField(max_length=32, blank=True, null=True, unique=True)
    scheme_code = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    security_code = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    status = models.CharField(
        max_length=32,
        choices=InstrumentStatus.choices,
        default=InstrumentStatus.ACTIVE,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    identity_version = models.PositiveIntegerField(
        default=1,
        help_text='Monotonically increasing identity version for secondary projection sync.',
    )
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instruments'
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol', 'exchange'], name='inst_sym_exch_idx'),
            models.Index(fields=['asset_class', 'is_active'], name='inst_class_active_idx'),
            models.Index(fields=['status'], name='inst_status_idx'),
            models.Index(fields=['name'], name='inst_name_idx'),
            models.Index(fields=['scheme_code'], name='inst_scheme_idx'),
        ]

    IDENTITY_FIELDS = (
        'symbol', 'name', 'asset_class', 'product_type', 'exchange',
        'currency', 'isin', 'scheme_code', 'security_code', 'status', 'is_active',
    )

    def save(self, *args, **kwargs):
        """Atomically persist canonical identity and its primary-database outbox row."""
        from django.db import transaction

        using = kwargs.get('using') or self._state.db or 'default'
        if using != 'default':
            raise ValueError('Canonical Instrument records must be saved to the default database.')
        kwargs['using'] = using

        if not self.is_active and self.status == InstrumentStatus.ACTIVE:
            self.status = InstrumentStatus.INACTIVE
        elif self.status != InstrumentStatus.ACTIVE:
            self.is_active = False
        else:
            self.is_active = True

        with transaction.atomic(using=using):
            is_new = self._state.adding
            identity_changed = is_new
            if not is_new and self.pk:
                previous = type(self).objects.using(using).select_for_update().filter(pk=self.pk).values(
                    *self.IDENTITY_FIELDS, 'identity_version'
                ).first()
                if previous:
                    candidate_fields = set(self.IDENTITY_FIELDS)
                    if kwargs.get('update_fields') is not None:
                        candidate_fields &= set(kwargs['update_fields'])
                    identity_changed = any(
                        previous[field] != getattr(self, field) for field in candidate_fields
                    )
                    self.identity_version = int(previous['identity_version'] or 1) + (1 if identity_changed else 0)

            if kwargs.get('update_fields') is not None and identity_changed:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'identity_version', 'updated_at'}

            super().save(*args, **kwargs)
            if identity_changed:
                from apps.market_data.services.sync_service import InstrumentIdentitySyncService
                # Event insertion failure rolls back the canonical instrument write.
                InstrumentIdentitySyncService.record_sync_event(self)

    def to_sync_payload(self) -> dict:
        return {
            'symbol': self.symbol,
            'name': self.name,
            'asset_class': self.asset_class,
            'product_type': self.product_type or '',
            'exchange': self.exchange or '',
            'currency': self.currency or 'INR',
            'isin': self.isin,
            'scheme_code': self.scheme_code,
            'security_code': self.security_code,
            'is_active': self.is_active,
            'identity_version': self.identity_version or 1,
        }

    def __str__(self) -> str:
        exchange_str = f" ({self.exchange})" if self.exchange else ""
        return f"{self.symbol}{exchange_str} - {self.name}"

    @property
    def latest_quote(self):
        """Compatibility accessor backed exclusively by the authoritative resolver."""
        from apps.market_data.services.market_data_service import MarketDataService
        quote = MarketDataService.get_latest_quote(self)
        return quote if quote.price is not None else None

    @property
    def coverage(self):
        """Cross-database property resolving coverage policy from secondary DB."""
        if hasattr(self, '_cached_coverage') and self._cached_coverage is not None:
            return self._cached_coverage
        from apps.market_data.models.coverage import InstrumentCoverage
        self._cached_coverage = InstrumentCoverage.objects.using('market_data').filter(instrument_id=self.id).first()
        return self._cached_coverage

    @coverage.setter
    def coverage(self, value):
        self._cached_coverage = value

    @property
    def observations(self):
        """Cross-database property resolving observations from secondary DB."""
        from apps.market_data.models.observation import PriceObservation
        return PriceObservation.objects.using('market_data').filter(instrument_id=self.id)

    @property
    def worklist_items(self):
        """Cross-database property resolving worklist items from secondary DB."""
        from apps.market_data.models.worklist import MarketDataWorklistItem
        return MarketDataWorklistItem.objects.using('market_data').filter(instrument_id=self.id)
