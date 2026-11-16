from rest_framework import serializers

from apps.market_data.models.instrument import Instrument
from apps.market_data.models.market_data_point import MarketDataPoint
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


class QuoteSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='instrument.symbol', read_only=True)
    currency = serializers.CharField(source='instrument.currency', read_only=True)

    class Meta:
        model = MarketDataPoint
        fields = [
            'id',
            'instrument_id',
            'symbol',
            'price',
            'open_price',
            'high_price',
            'low_price',
            'close_price',
            'volume',
            'change_amount',
            'change_percent',
            'provider',
            'is_synthetic',
            'interval',
            'currency',
            'timestamp',
        ]


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
        quote = obj.latest_quote
        if quote:
            return QuoteSerializer(quote).data
        return None


class HistoricalPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketDataPoint
        fields = [
            'timestamp',
            'price',
            'open_price',
            'high_price',
            'low_price',
            'close_price',
            'volume',
            'change_amount',
            'change_percent',
            'interval',
            'is_synthetic',
        ]
