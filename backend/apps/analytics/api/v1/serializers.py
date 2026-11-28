from rest_framework import serializers


class DateRangeFilterSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, attrs):
        start = attrs.get('start_date')
        end = attrs.get('end_date')
        if start and end and start > end:
            raise serializers.ValidationError({"start_date": "start_date cannot be greater than end_date."})
        return attrs


class HoldingPointSerializer(serializers.Serializer):
    date = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=18, decimal_places=4)
    cost_basis = serializers.DecimalField(max_digits=18, decimal_places=4)
    market_price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    market_value = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    unrealized_pnl = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    realized_pnl = serializers.DecimalField(max_digits=18, decimal_places=4)
    total_pnl = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    is_price_available = serializers.BooleanField()
    valuation_source = serializers.CharField()


class InvestmentTimelineEntrySerializer(serializers.Serializer):
    id = serializers.CharField()
    date = serializers.CharField()
    type = serializers.CharField()
    units = serializers.CharField()
    price_per_unit = serializers.CharField()
    gross_amount = serializers.CharField()
    fees = serializers.CharField()
    taxes = serializers.CharField()
    net_cash_flow = serializers.CharField()
    notes = serializers.CharField(allow_blank=True, required=False)


class InvestmentPerformanceResponseSerializer(serializers.Serializer):
    investment_id = serializers.CharField()
    currency = serializers.CharField()
    current_quantity = serializers.DecimalField(max_digits=18, decimal_places=4)
    initial_invested_capital = serializers.DecimalField(max_digits=18, decimal_places=4)
    net_invested_capital = serializers.DecimalField(max_digits=18, decimal_places=4)
    current_cost_basis = serializers.DecimalField(max_digits=18, decimal_places=4)
    current_market_price = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    current_market_value = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    realized_pnl = serializers.DecimalField(max_digits=18, decimal_places=4)
    unrealized_pnl = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    total_pnl = serializers.DecimalField(max_digits=18, decimal_places=4, allow_null=True)
    absolute_return_pct = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    cagr_pct = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    xirr_pct = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    xirr_status = serializers.CharField()
    first_transaction_date = serializers.CharField(allow_null=True)
    latest_transaction_date = serializers.CharField(allow_null=True)
    timeline = InvestmentTimelineEntrySerializer(many=True)
    history = HoldingPointSerializer(many=True)
    data_completeness = serializers.DictField()


class PortfolioTimeSeriesPointSerializer(serializers.Serializer):
    date = serializers.CharField()
    market_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    invested_capital = serializers.DecimalField(max_digits=18, decimal_places=2)
    realized_pnl = serializers.DecimalField(max_digits=18, decimal_places=2)
    unrealized_pnl = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_pnl = serializers.DecimalField(max_digits=18, decimal_places=2)
    net_cash_flow_on_date = serializers.DecimalField(max_digits=18, decimal_places=2)
    twr_cumulative_pct = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)


class PortfolioPerformanceResponseSerializer(serializers.Serializer):
    portfolio_id = serializers.CharField()
    portfolio_name = serializers.CharField()
    currency = serializers.CharField()
    current_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_invested_capital = serializers.DecimalField(max_digits=18, decimal_places=2)
    current_cost_basis = serializers.DecimalField(max_digits=18, decimal_places=2)
    realized_pnl = serializers.DecimalField(max_digits=18, decimal_places=2)
    unrealized_pnl = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_pnl = serializers.DecimalField(max_digits=18, decimal_places=2)
    absolute_return_pct = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    cagr_pct = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    xirr_pct = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    xirr_status = serializers.CharField()
    twr_pct = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    active_holdings_count = serializers.IntegerField()
    closed_holdings_count = serializers.IntegerField()
    history = PortfolioTimeSeriesPointSerializer(many=True)
    holdings_summary = serializers.ListField(child=serializers.DictField())
    data_completeness = serializers.DictField()


class AllocationItemSerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()
    market_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    percentage = serializers.DecimalField(max_digits=6, decimal_places=2)
    holding_count = serializers.IntegerField()


class AllocationResponseSerializer(serializers.Serializer):
    portfolio_id = serializers.CharField(allow_null=True)
    currency = serializers.CharField()
    total_market_value = serializers.DecimalField(max_digits=18, decimal_places=2)
    by_asset_category = AllocationItemSerializer(many=True)
    by_instrument = AllocationItemSerializer(many=True)


class NormalizedPointSerializer(serializers.Serializer):
    date = serializers.CharField()
    target_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    benchmark_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    target_raw = serializers.DecimalField(max_digits=18, decimal_places=4)
    benchmark_raw = serializers.DecimalField(max_digits=18, decimal_places=4)


class BenchmarkComparisonResponseSerializer(serializers.Serializer):
    target_id = serializers.CharField()
    target_type = serializers.CharField()
    benchmark_id = serializers.CharField()
    benchmark_symbol = serializers.CharField()
    benchmark_name = serializers.CharField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    target_total_return_pct = serializers.DecimalField(max_digits=10, decimal_places=2)
    benchmark_total_return_pct = serializers.DecimalField(max_digits=10, decimal_places=2)
    excess_return_pct = serializers.DecimalField(max_digits=10, decimal_places=2)
    points = NormalizedPointSerializer(many=True)
