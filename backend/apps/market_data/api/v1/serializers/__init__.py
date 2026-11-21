from rest_framework import serializers

from apps.market_data.models.instrument import Instrument
from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
from apps.market_data.models.reference_data import InstrumentReferenceData


class ProviderMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderInstrumentMapping
        fields = ['provider_name', 'provider_symbol', 'is_primary']


class InstrumentReferenceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstrumentReferenceData
        fields = [
            'sector',
            'industry',
            'market_cap_category',
            'lot_size',
            'tick_size',
            'website',
            'details',
        ]


class QuoteSerializer(serializers.Serializer):
    symbol = serializers.CharField(source='instrument.symbol', read_only=True)

    id = serializers.CharField(allow_null=True)
    instrument_id = serializers.CharField()
    price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    open_price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    high_price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    low_price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    close_price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    volume = serializers.IntegerField(allow_null=True)
    change_amount = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    change_percent = serializers.DecimalField(max_digits=8, decimal_places=4, allow_null=True)
    provider = serializers.CharField()
    is_synthetic = serializers.BooleanField()
    interval = serializers.CharField()
    timestamp = serializers.DateTimeField(allow_null=True)
    currency = serializers.CharField()
    status = serializers.CharField()
    notes = serializers.CharField(allow_blank=True)


class InstrumentSerializer(serializers.ModelSerializer):
    reference_data = InstrumentReferenceDataSerializer(read_only=True)
    latest_quote = serializers.SerializerMethodField()

    class Meta:
        model = Instrument
        fields = [
            'id',
            'symbol',
            'name',
            'asset_class',
            'exchange',
            'currency',
            'isin',
            'is_active',
            'reference_data',
            'latest_quote',
            'created_at',
            'updated_at',
        ]

    def get_latest_quote(self, obj: Instrument):
        resolved_map = self.context.get('resolved_prices', {})
        resolved = resolved_map.get(obj.id)
        if resolved is None:
            quote = obj.latest_quote
            return QuoteSerializer(quote).data if quote else None
        if resolved.price is None:
            return {
                'instrument_id': str(obj.id), 'symbol': obj.symbol,
                'price': None, 'currency': resolved.currency,
                'status': resolved.status, 'source': resolved.source,
                'is_synthetic': resolved.is_synthetic, 'notes': resolved.notes,
            }
        return {
            'id': resolved.observation_id,
            'instrument_id': str(obj.id), 'symbol': obj.symbol,
            'price': str(resolved.price), 'open_price': None, 'high_price': None,
            'low_price': None, 'close_price': str(resolved.price), 'volume': None,
            'change_amount': None, 'change_percent': None,
            'provider': resolved.source, 'is_synthetic': resolved.is_synthetic,
            'interval': '1D', 'timestamp': resolved.effective_at,
            'currency': resolved.currency, 'status': resolved.status,
            'notes': resolved.notes, 'series_id': resolved.series_id,
            'observation_id': resolved.observation_id, 'data_version': resolved.data_version,
        }
