import uuid

from django.db import models

from apps.market_data.models.instrument import Instrument


class MarketDataPoint(models.Model):
    """Deprecated legacy quote table retained only for migration/reconciliation.

    It is not an authoritative history source. Canonical instrument identity is a
    scalar UUID because this model is owned by market_data while Instrument is
    owned by default.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument_id = models.UUIDField(db_index=True, db_column='instrument_id')
    timestamp = models.DateTimeField(db_index=True)
    price = models.DecimalField(max_digits=18, decimal_places=4)
    open_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    close_price = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    change_amount = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    change_percent = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    provider = models.CharField(max_length=32, db_index=True)
    is_synthetic = models.BooleanField(default=False, db_index=True)
    interval = models.CharField(max_length=16, default='1D', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'market_data_points'
        ordering = ['-timestamp']
        unique_together = ('instrument_id', 'timestamp', 'interval', 'provider')
        indexes = [
            models.Index(fields=['instrument_id', '-timestamp'], name='mdp_inst_time_idx'),
            models.Index(fields=['instrument_id', 'interval', '-timestamp'], name='mdp_inst_int_time_idx'),
            models.Index(fields=['provider', 'is_synthetic'], name='mdp_prov_synth_idx'),
        ]

    def __init__(self, *args, **kwargs):
        instrument = kwargs.pop('instrument', None)
        super().__init__(*args, **kwargs)
        if instrument is not None:
            self.instrument_id = getattr(instrument, 'id', instrument)

    @property
    def instrument(self):
        return Instrument.objects.using('default').filter(pk=self.instrument_id).first()

    def __str__(self):
        instrument = self.instrument
        symbol = instrument.symbol if instrument else str(self.instrument_id)
        synthetic = ' [DEMO]' if self.is_synthetic else ''
        return f'{symbol} @ {self.price} ({self.timestamp:%Y-%m-%d %H:%M}){synthetic}'
