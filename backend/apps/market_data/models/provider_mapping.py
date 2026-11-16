import uuid

from django.db import models

from apps.market_data.models.instrument import Instrument


class ProviderInstrumentMapping(models.Model):
    """
    Maps a canonical Instrument to external vendor-specific symbols
    (e.g., RELIANCE -> TrueData: 'RELIANCE-EQ', AMFI: '122639', Yahoo: 'RELIANCE.NS').
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name='provider_mappings',
    )
    provider_name = models.CharField(max_length=32, db_index=True)
    provider_symbol = models.CharField(max_length=128)
    is_primary = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'provider_instrument_mappings'
        unique_together = ('provider_name', 'provider_symbol')
        indexes = [
            models.Index(fields=['provider_name', 'instrument'], name='pim_prov_inst_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.provider_name}:{self.provider_symbol} -> {self.instrument.symbol}"
