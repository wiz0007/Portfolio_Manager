import uuid
from typing import TYPE_CHECKING, Optional

from django.db import models

if TYPE_CHECKING:
    from apps.market_data.models.market_data_point import MarketDataPoint


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

    def save(self, *args, **kwargs):
        # Keep is_active and status synchronized bidirectionally
        if not self.is_active and self.status == InstrumentStatus.ACTIVE:
            self.status = InstrumentStatus.INACTIVE
        elif self.status != InstrumentStatus.ACTIVE:
            self.is_active = False
        else:
            self.is_active = True

        is_new = self._state.adding
        if not is_new and self.pk:
            # Monotonically increment identity version on update
            self.identity_version = (self.identity_version or 0) + 1

        super().save(*args, **kwargs)

        # Durable outbox record on Primary Database ('default')
        try:
            from apps.market_data.services.sync_service import InstrumentIdentitySyncService
            InstrumentIdentitySyncService.record_sync_event(self)
        except Exception:
            pass

    def __str__(self) -> str:
        exchange_str = f" ({self.exchange})" if self.exchange else ""
        return f"{self.symbol}{exchange_str} - {self.name}"

    @property
    def latest_quote(self) -> Optional['MarketDataPoint']:
        """Returns the most recent market data point for this instrument."""
        return self.data_points.order_by('-timestamp').first()

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
