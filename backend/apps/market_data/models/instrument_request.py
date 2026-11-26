import uuid

from django.conf import settings
from django.db import models

from apps.market_data.models.instrument import AssetClass, Instrument


class InstrumentRequestStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Review'
    MATCHED = 'MATCHED', 'Matched to Existing Instrument'
    APPROVED = 'APPROVED', 'Approved as Canonical Instrument'
    MORE_INFO_REQUESTED = 'MORE_INFO_REQUESTED', 'More Information Requested'
    REJECTED = 'REJECTED', 'Rejected'
    DUPLICATE = 'DUPLICATE', 'Marked Duplicate'


class InstrumentRequest(models.Model):
    """
    User-submitted request for an instrument not yet present in the canonical catalogue.
    Undergoes operator verification before approval or matching.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instrument_requests',
        db_index=True,
        db_constraint=False,
    )
    raw_name = models.CharField(max_length=255)
    asset_class = models.CharField(
        max_length=32,
        choices=AssetClass.choices,
        default=AssetClass.EQUITY,
        db_index=True,
    )
    product_type = models.CharField(max_length=64, blank=True, default='')
    symbol = models.CharField(max_length=64, blank=True, default='', db_index=True)
    exchange = models.CharField(max_length=32, blank=True, default='')
    isin = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    scheme_code = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    notes = models.TextField(blank=True, default='')

    status = models.CharField(
        max_length=32,
        choices=InstrumentRequestStatus.choices,
        default=InstrumentRequestStatus.PENDING,
        db_index=True,
    )
    matched_instrument = models.ForeignKey(
        Instrument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_requests',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_instrument_requests',
        db_constraint=False,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instrument_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='req_status_time_idx'),
            models.Index(fields=['user', 'status'], name='req_user_status_idx'),
            models.Index(fields=['symbol', 'exchange'], name='req_sym_exch_idx'),
        ]

    def __str__(self) -> str:
        return f"Request({self.raw_name} - {self.status}) by {self.user.email}"
