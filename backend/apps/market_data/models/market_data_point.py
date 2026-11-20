import uuid

from django.db import models

from apps.market_data.models.instrument import Instrument


class MarketDataPoint(models.Model):
    """
    Normalized, immutable historical or latest market quote for an instrument.
    All financial amounts use DecimalField(18, 4). Timestamps are UTC.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name='data_points',
        db_index=True,
        db_constraint=False,
    )
    timestamp = models.DateTimeField(db_index=True)
    price = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        help_text='Last traded price (LTP) or closing/NAV price.',
    )
    open_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    close_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    change_amount = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Absolute day price change.',
    )
    change_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Percentage change relative to previous close.',
    )

    provider = models.CharField(max_length=32, db_index=True)
    is_synthetic = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Explicit flag identifying synthetic demo data.',
    )
    interval = models.CharField(
        max_length=16,
        default='1D',
        db_index=True,
        help_text="Timeframe interval, e.g., '1D', '1H', 'REALTIME'.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'market_data_points'
        ordering = ['-timestamp']
        unique_together = ('instrument', 'timestamp', 'interval', 'provider')
        indexes = [
            models.Index(fields=['instrument', '-timestamp'], name='mdp_inst_time_idx'),
            models.Index(fields=['instrument', 'interval', '-timestamp'], name='mdp_inst_int_time_idx'),
            models.Index(fields=['provider', 'is_synthetic'], name='mdp_prov_synth_idx'),
        ]

    def __str__(self) -> str:
        synth = " [DEMO]" if self.is_synthetic else ""
        return f"{self.instrument.symbol} @ {self.price} ({self.timestamp.strftime('%Y-%m-%d %H:%M')}){synth}"
