import uuid

from django.db import models


class SyncEventStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Synchronization'
    PROCESSED = 'PROCESSED', 'Successfully Processed'
    FAILED = 'FAILED', 'Synchronization Failed'


class InstrumentSyncEvent(models.Model):
    """
    Durable Outbox record on the Primary Database ('default')
    tracking canonical instrument changes for asynchronous, reliable,
    and idempotent synchronization to the Market Data Storage Database.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument_id = models.UUIDField(db_index=True)
    identity_version = models.PositiveIntegerField(default=1)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=SyncEventStatus.choices,
        default=SyncEventStatus.PENDING,
        db_index=True,
    )
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'instrument_sync_events'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='sync_status_created_idx'),
            models.Index(fields=['instrument_id', 'identity_version'], name='sync_inst_ver_idx'),
        ]

    def __str__(self) -> str:
        return f"SyncEvent {self.instrument_id} v{self.identity_version} ({self.status})"
