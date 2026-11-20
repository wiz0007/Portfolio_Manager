import uuid

from django.db import models


class PublicationEventStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Valuation Refresh'
    PROCESSED = 'PROCESSED', 'Valuations Successfully Refreshed'
    FAILED = 'FAILED', 'Processing Failed'


class MarketDataPublicationEvent(models.Model):
    """
    Durable Outbox record on the Secondary Database ('market_data')
    emitted atomically when a price observation is published or corrected.
    Processed by an idempotent valuation processor on the Primary Database.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    observation_id = models.UUIDField(db_index=True)
    instrument_id = models.UUIDField(db_index=True)
    series_id = models.UUIDField(null=True, blank=True, db_index=True)
    effective_at = models.DateTimeField(db_index=True)
    price_type = models.CharField(max_length=32, db_index=True)
    value = models.DecimalField(max_digits=18, decimal_places=4)
    currency = models.CharField(max_length=10, default='INR')
    data_version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=PublicationEventStatus.choices,
        default=PublicationEventStatus.PENDING,
        db_index=True,
    )
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'market_data_publication_events'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='pub_event_status_idx'),
            models.Index(fields=['instrument_id', 'effective_at'], name='pub_event_inst_eff_idx'),
        ]

    def __str__(self) -> str:
        return f"PubEvent {self.observation_id} inst={self.instrument_id} val={self.value} ({self.status})"
