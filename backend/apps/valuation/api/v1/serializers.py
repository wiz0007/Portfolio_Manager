from datetime import date
from decimal import Decimal

from rest_framework import serializers

from apps.assets.models.valuations import InvestmentValuation


class ManualValuationCreateSerializer(serializers.Serializer):
    """
    Validates user input for recording a manual valuation snapshot.
    """
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('0.0001'))
    valuation_date = serializers.DateField(default=date.today)
    valuation_method = serializers.CharField(max_length=50, default='MANUAL')
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')

    def validate_valuation_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("Valuation date cannot be in the future.")
        return value


class ValuationSnapshotSerializer(serializers.ModelSerializer):
    """
    Read serializer for historical InvestmentValuation records.
    """
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, coerce_to_string=True)

    class Meta:
        model = InvestmentValuation
        fields = [
            'id',
            'investment_id',
            'valuation_date',
            'amount',
            'currency',
            'valuation_method',
            'source',
            'source_reference',
            'observed_at',
            'notes',
            'metadata',
            'created_at',
        ]
        read_only_fields = fields


class PerformanceMetricSerializer(serializers.Serializer):
    """
    Standardized payload for investment holding performance metrics.
    """
    investment_id = serializers.UUIDField()
    display_name = serializers.CharField()
    category = serializers.CharField()
    asset_type = serializers.CharField()
    currency = serializers.CharField()
    invested_amount = serializers.CharField()
    current_value = serializers.CharField()
    absolute_gain_loss = serializers.CharField()
    percentage_gain_loss = serializers.CharField()
    is_gain = serializers.BooleanField()
    last_valuation_date = serializers.DateField(allow_null=True)
    valuation_method = serializers.CharField()
    source = serializers.CharField()


class ProjectionRequestSerializer(serializers.Serializer):
    """
    Validates parameters for the future-value projection calculation engine.
    """
    time_horizon_years = serializers.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('5.00'), min_value=Decimal('0.10'), max_value=Decimal('50.00')
    )
    monthly_contribution = serializers.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'), min_value=Decimal('0.00')
    )
    contribution_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True, min_value=Decimal('0.00')
    )
    contribution_timing = serializers.ChoiceField(
        choices=['END_OF_PERIOD', 'BEGINNING_OF_PERIOD'],
        default='END_OF_PERIOD',
    )
    compounding_frequency_per_year = serializers.IntegerField(default=12, min_value=1, max_value=365)
    contribution_frequency_per_year = serializers.IntegerField(default=12, min_value=1, max_value=365, required=False)
    custom_annual_rate = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, allow_null=True, min_value=Decimal('0.00'), max_value=Decimal('500.00')
    )
    scenarios = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
    )
