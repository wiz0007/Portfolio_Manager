from decimal import Decimal

from rest_framework import serializers


class WatchlistAddSerializer(serializers.Serializer):
    instrument_id = serializers.UUIDField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='', max_length=1000)
    target_price = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=18,
        decimal_places=4,
    )

    def validate_target_price(self, value):
        if value is not None and value <= Decimal('0'):
            raise serializers.ValidationError('Target price must be strictly positive.')
        return value


class WatchlistInstrumentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    symbol = serializers.CharField()
    name = serializers.CharField()
    asset_class = serializers.CharField()
    product_type = serializers.CharField(allow_blank=True)
    exchange = serializers.CharField(allow_blank=True)
    currency = serializers.CharField()
    isin = serializers.CharField(allow_null=True, allow_blank=True)
    scheme_code = serializers.CharField(allow_null=True, allow_blank=True)
    sector = serializers.CharField(allow_blank=True)
    industry = serializers.CharField(allow_blank=True)
    status = serializers.CharField()


class PriceMovementSerializer(serializers.Serializer):
    change_amount = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    change_percent = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    previous_price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    previous_effective_at = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    notes = serializers.CharField(allow_blank=True)


class MarketDataAnnotationSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    currency = serializers.CharField()
    unit = serializers.CharField()
    effective_at = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    source = serializers.CharField()
    source_reference = serializers.CharField(allow_blank=True)
    is_synthetic = serializers.BooleanField()
    notes = serializers.CharField(allow_blank=True)
    movement = PriceMovementSerializer()


class WatchlistItemResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    instrument = WatchlistInstrumentSerializer()
    notes = serializers.CharField(allow_blank=True)
    target_price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    market_data = MarketDataAnnotationSerializer()
