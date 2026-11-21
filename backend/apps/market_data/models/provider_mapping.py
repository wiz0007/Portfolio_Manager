import uuid

from django.db import models

from apps.market_data.models.instrument import Instrument


class ProviderInstrumentMapping(models.Model):
    """Secondary-database provider symbol mapping; canonical instrument is a scalar UUID."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument_id = models.UUIDField(db_column='instrument_id', db_index=True, help_text='Canonical Instrument UUID in primary database')
    provider_name = models.CharField(max_length=32, db_index=True)
    provider_symbol = models.CharField(max_length=128)
    is_primary = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'provider_instrument_mappings'
        unique_together = ('provider_name', 'provider_symbol')
        indexes = [models.Index(fields=['provider_name', 'instrument_id'], name='pim_prov_inst_idx')]

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
        return f'{self.provider_name}:{self.provider_symbol} -> {symbol}'
