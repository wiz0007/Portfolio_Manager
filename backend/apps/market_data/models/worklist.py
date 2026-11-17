import uuid

from django.db import models

from apps.market_data.models.coverage import InstrumentCoverage
from apps.market_data.models.instrument import Instrument


class WorklistStatus(models.TextChoices):
    GENERATED = 'GENERATED', 'Generated'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'


class DueReason(models.TextChoices):
    FIRST_PRICE = 'FIRST_PRICE', 'Due for First Price'
    DUE_TODAY = 'DUE_TODAY', 'Scheduled Today'
    STALE = 'STALE', 'Stale / Missing Price'
    CONFLICT = 'CONFLICT', 'Conflicting Observations'
    PENDING_APPROVAL = 'PENDING_APPROVAL', 'Awaiting Identity Approval'
    SKIPPED_HOLIDAY = 'SKIPPED_HOLIDAY', 'Skipped Holiday or Off-Market'


class WorklistItemStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Price Collection'
    COMPLETED = 'COMPLETED', 'Price Collected & Published'
    SKIPPED = 'SKIPPED', 'Skipped / No Trade'


class MarketDataWorklist(models.Model):
    """
    Daily master worklist tracking instruments requiring manual price collection for a specific calendar date.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    worklist_date = models.DateField(unique=True, db_index=True)
    status = models.CharField(
        max_length=32,
        choices=WorklistStatus.choices,
        default=WorklistStatus.GENERATED,
    )
    total_items = models.PositiveIntegerField(default=0)
    completed_items = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'market_data_worklists'
        ordering = ['-worklist_date']

    def __str__(self) -> str:
        return f"Worklist({self.worklist_date} - {self.completed_items}/{self.total_items})"


class MarketDataWorklistItem(models.Model):
    """
    Discrete collection task item inside a daily worklist.
    Has a stable item ID for versioned CSV import reconciliation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    worklist = models.ForeignKey(
        MarketDataWorklist,
        on_delete=models.CASCADE,
        related_name='items',
        db_index=True,
    )
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name='worklist_items',
        db_index=True,
    )
    coverage = models.ForeignKey(
        InstrumentCoverage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='worklist_items',
    )
    canonical_name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=64, db_index=True)
    exchange = models.CharField(max_length=32, blank=True, default='')
    isin = models.CharField(max_length=32, blank=True, null=True)
    asset_class = models.CharField(max_length=32)
    product_type = models.CharField(max_length=64, blank=True, default='')

    expected_price_type = models.CharField(max_length=32)
    currency = models.CharField(max_length=10, default='INR')
    unit = models.CharField(max_length=32, default='UNITS')
    effective_date = models.DateField(db_index=True)
    due_reason = models.CharField(
        max_length=32,
        choices=DueReason.choices,
        default=DueReason.DUE_TODAY,
    )
    status = models.CharField(
        max_length=32,
        choices=WorklistItemStatus.choices,
        default=WorklistItemStatus.PENDING,
        db_index=True,
    )

    last_published_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    last_published_date = models.DateTimeField(null=True, blank=True)
    source_guidance = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'market_data_worklist_items'
        ordering = ['asset_class', 'symbol']
        unique_together = ('worklist', 'instrument')
        indexes = [
            models.Index(fields=['worklist', 'status'], name='wli_wl_status_idx'),
            models.Index(fields=['effective_date', 'status'], name='wli_eff_status_idx'),
        ]

    def __str__(self) -> str:
        return f"WorklistItem({self.symbol} [{self.effective_date}]: {self.status})"
