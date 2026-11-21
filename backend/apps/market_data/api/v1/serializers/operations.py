from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.market_data.models.coverage import (
    CollectionCadence,
    InstrumentCoverage,
    PriceType,
    QuotationUnit,
)
from apps.market_data.models.instrument import AssetClass
from apps.market_data.models.instrument_request import (
    InstrumentRequest,
    InstrumentRequestStatus,
)
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.models.worklist import (
    MarketDataWorklist,
    MarketDataWorklistItem,
)

# --- Instrument Request Serializers ---

class InstrumentRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    matched_instrument_symbol = serializers.CharField(
        source='matched_instrument.symbol',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = InstrumentRequest
        fields = [
            'id',
            'user_email',
            'raw_name',
            'asset_class',
            'product_type',
            'symbol',
            'exchange',
            'isin',
            'scheme_code',
            'notes',
            'status',
            'matched_instrument',
            'matched_instrument_symbol',
            'reviewed_by',
            'reviewed_at',
            'rejection_reason',
            'created_at',
            'updated_at',
        ]
        validators = []
        read_only_fields = [
            'id',
            'status',
            'matched_instrument',
            'reviewed_by',
            'reviewed_at',
            'rejection_reason',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        user = self.context['request'].user
        symbol = attrs.get('symbol', '').strip().upper()
        exchange = attrs.get('exchange', '').strip().upper()
        raw_name = attrs.get('raw_name', '').strip()

        # Deduplication check for pending requests
        existing = InstrumentRequest.objects.filter(
            status=InstrumentRequestStatus.PENDING,
            user=user,
        )
        if symbol and exchange:
            if existing.filter(symbol__iexact=symbol, exchange__iexact=exchange).exists():
                raise serializers.ValidationError(
                    f"You already have a pending request for {symbol} on {exchange}."
                )
        elif raw_name:
            if existing.filter(raw_name__iexact=raw_name).exists():
                raise serializers.ValidationError(
                    f"You already have a pending request for '{raw_name}'."
                )

        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class InstrumentRequestApproveSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=64, required=True)
    name = serializers.CharField(max_length=255, required=True)
    asset_class = serializers.ChoiceField(choices=AssetClass.choices, required=True)
    exchange = serializers.CharField(max_length=32, required=False, allow_blank=True, default='')
    currency = serializers.CharField(max_length=10, default='INR')
    isin = serializers.CharField(max_length=32, required=False, allow_blank=True, allow_null=True)
    scheme_code = serializers.CharField(max_length=32, required=False, allow_blank=True, allow_null=True)
    product_type = serializers.CharField(max_length=64, required=False, allow_blank=True, default='')

    # Price Coverage Policy parameters
    cadence = serializers.ChoiceField(
        choices=CollectionCadence.choices,
        default=CollectionCadence.EVERY_TRADING_DAY,
    )
    price_type = serializers.ChoiceField(
        choices=PriceType.choices,
        default=PriceType.LTP,
    )
    unit = serializers.ChoiceField(
        choices=QuotationUnit.choices,
        default=QuotationUnit.UNITS,
    )
    freshness_hours = serializers.IntegerField(default=24, min_value=1)


class InstrumentRequestMatchSerializer(serializers.Serializer):
    instrument_id = serializers.UUIDField(required=True)


class InstrumentRequestRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, min_length=5)


# --- Instrument Coverage Serializers ---

class InstrumentCoverageSerializer(serializers.ModelSerializer):
    instrument = serializers.UUIDField(source='instrument_id')
    symbol = serializers.CharField(source='instrument.symbol', read_only=True)
    canonical_name = serializers.CharField(source='instrument.name', read_only=True)
    asset_class = serializers.CharField(source='instrument.asset_class', read_only=True)

    class Meta:
        model = InstrumentCoverage
        fields = [
            'id',
            'instrument',
            'symbol',
            'canonical_name',
            'asset_class',
            'price_type',
            'currency',
            'unit',
            'cadence',
            'market_timezone',
            'freshness_hours',
            'grace_period_hours',
            'preferred_source',
            'status',
            'last_attempt_at',
            'last_published_at',
            'inclusion_reason',
            'notes',
            'created_at',
            'updated_at',
        ]
        validators = []
        read_only_fields = ['id', 'last_attempt_at', 'last_published_at', 'created_at', 'updated_at']


# --- Price Observation Serializers ---

class PriceObservationSerializer(serializers.ModelSerializer):
    instrument = serializers.UUIDField(source='instrument_id')
    symbol = serializers.CharField(source='instrument.symbol', read_only=True)
    instrument_name = serializers.CharField(source='instrument.name', read_only=True)
    recorded_by = serializers.UUIDField(source='recorded_by_id', read_only=True)
    recorded_by_email = serializers.CharField(source='recorded_by.email', read_only=True)
    published_by = serializers.UUIDField(source='published_by_id', read_only=True)
    published_by_email = serializers.CharField(source='published_by.email', read_only=True)

    class Meta:
        model = PriceObservation
        fields = [
            'id',
            'instrument',
            'symbol',
            'instrument_name',
            'series',
            'price_type',
            'value',
            'currency',
            'unit',
            'effective_at',
            'source',
            'source_reference',
            'notes',
            'status',
            'is_synthetic',
            'trust_class',
            'recorded_by',
            'recorded_by_email',
            'published_by',
            'published_by_email',
            'published_at',
            'rejection_reason',
            'correction_of',
            'correction_reason',
            'created_at',
            'updated_at',
        ]
        validators = []
        extra_kwargs = {'series': {'required': True}}
        read_only_fields = [
            'id',
            'status',
            'is_synthetic',
            'trust_class',
            'recorded_by',
            'published_by',
            'published_at',
            'rejection_reason',
            'created_at',
            'updated_at',
        ]

    def validate_value(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError("Price observation value must be strictly positive.")
        return value

    def validate_effective_at(self, effective_at):
        if effective_at > timezone.now() + timezone.timedelta(minutes=5):
            raise serializers.ValidationError("Effective timestamp cannot be in the future.")
        return effective_at

    def create(self, validated_data):
        validated_data['recorded_by_id'] = getattr(self.context['request'].user, 'id', None)
        validated_data['status'] = ObservationStatus.DRAFT
        return super().create(validated_data)


class PriceObservationCorrectionSerializer(serializers.Serializer):
    value = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('0.0001'))
    effective_at = serializers.DateTimeField(required=False)
    source = serializers.CharField(max_length=64, default='MANUAL_CORRECTION')
    source_reference = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    correction_reason = serializers.CharField(required=True, min_length=5)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


# --- Worklist Serializers ---

class MarketDataWorklistItemSerializer(serializers.ModelSerializer):
    instrument = serializers.UUIDField(source='instrument_id', read_only=True)

    class Meta:
        model = MarketDataWorklistItem
        fields = [
            'id',
            'worklist',
            'instrument',
            'coverage',
            'canonical_name',
            'symbol',
            'exchange',
            'isin',
            'asset_class',
            'product_type',
            'expected_price_type',
            'currency',
            'unit',
            'effective_date',
            'due_reason',
            'status',
            'last_published_price',
            'last_published_date',
            'source_guidance',
            'notes',
        ]


class MarketDataWorklistSerializer(serializers.ModelSerializer):
    items = MarketDataWorklistItemSerializer(many=True, read_only=True)

    class Meta:
        model = MarketDataWorklist
        fields = [
            'id',
            'worklist_date',
            'status',
            'total_items',
            'completed_items',
            'metadata',
            'items',
            'generated_at',
            'updated_at',
        ]
