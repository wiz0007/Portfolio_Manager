from rest_framework import serializers


class DashboardUserSerializer(serializers.Serializer):
    """Basic user information for the dashboard overview."""

    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)


class RecentPortfolioSerializer(serializers.Serializer):
    """Recent portfolio summary for dashboard display."""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    base_currency = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True, required=False)


class SelectedPortfolioSerializer(serializers.Serializer):
    """Details of the currently selected portfolio filter."""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    base_currency = serializers.CharField(read_only=True)


class CurrencySummarySerializer(serializers.Serializer):
    """Aggregated financial metrics for a specific currency."""

    currency = serializers.CharField(read_only=True)
    total_current_value = serializers.CharField(read_only=True)
    total_invested_capital = serializers.CharField(read_only=True)
    absolute_gain_loss = serializers.CharField(read_only=True)
    gain_loss_percentage = serializers.CharField(read_only=True, allow_null=True)
    valued_investment_count = serializers.IntegerField(read_only=True)
    unvalued_investment_count = serializers.IntegerField(read_only=True)
    total_investment_count = serializers.IntegerField(read_only=True)


class DataCompletenessSerializer(serializers.Serializer):
    """Overview of valuation completeness across active holdings."""

    total_active_holdings = serializers.IntegerField(read_only=True)
    valued_holdings = serializers.IntegerField(read_only=True)
    unvalued_holdings = serializers.IntegerField(read_only=True)
    stale_holdings = serializers.IntegerField(read_only=True)
    missing_price_holdings = serializers.IntegerField(read_only=True)
    completeness_percentage = serializers.FloatField(read_only=True)


class DashboardOverviewSerializer(serializers.Serializer):
    """Aggregated portfolio dashboard overview state."""

    user = DashboardUserSerializer(read_only=True)
    portfolio_count = serializers.IntegerField(read_only=True, default=0)
    recent_portfolios = RecentPortfolioSerializer(many=True, read_only=True, default=list)
    selected_portfolio = SelectedPortfolioSerializer(read_only=True, allow_null=True)
    is_combined = serializers.BooleanField(read_only=True, default=True)
    active_investment_count = serializers.IntegerField(read_only=True, default=0)
    summary = CurrencySummarySerializer(read_only=True, allow_null=True)
    totals_by_currency = serializers.DictField(child=CurrencySummarySerializer(), read_only=True, default=dict)
    data_completeness = DataCompletenessSerializer(read_only=True, required=False)
    calculated_at = serializers.CharField(read_only=True)


class AssetClassAllocationItemSerializer(serializers.Serializer):
    category = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    total_value = serializers.CharField(read_only=True)
    percentage = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)


class PortfolioAllocationItemSerializer(serializers.Serializer):
    portfolio_id = serializers.UUIDField(read_only=True)
    portfolio_name = serializers.CharField(read_only=True)
    total_value = serializers.CharField(read_only=True)
    percentage = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)


class TopHoldingAllocationItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    total_value = serializers.CharField(read_only=True)
    percentage = serializers.CharField(read_only=True)


class AssetAllocationResponseSerializer(serializers.Serializer):
    currency = serializers.CharField(read_only=True)
    denominator_value = serializers.CharField(read_only=True)
    valued_count = serializers.IntegerField(read_only=True)
    unvalued_count = serializers.IntegerField(read_only=True)
    has_unvalued_assets = serializers.BooleanField(read_only=True)
    asset_class_allocation = AssetClassAllocationItemSerializer(many=True, read_only=True)
    portfolio_allocation = PortfolioAllocationItemSerializer(many=True, read_only=True)
    top_holdings_allocation = TopHoldingAllocationItemSerializer(many=True, read_only=True)
    allocations_by_currency = serializers.DictField(read_only=True, required=False)


class HoldingOverviewItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    asset_type = serializers.CharField(read_only=True)
    portfolio_id = serializers.UUIDField(read_only=True)
    portfolio_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    currency = serializers.CharField(read_only=True)
    quantity = serializers.CharField(read_only=True, allow_null=True)
    invested_capital = serializers.CharField(read_only=True)
    current_value = serializers.CharField(read_only=True)
    absolute_gain_loss = serializers.CharField(read_only=True)
    gain_loss_percentage = serializers.CharField(read_only=True, allow_null=True)
    valuation_date = serializers.CharField(read_only=True, allow_null=True)
    valuation_source = serializers.CharField(read_only=True, allow_null=True)
    valuation_status = serializers.CharField(read_only=True, default='VALUED')
    price_freshness = serializers.CharField(read_only=True)
    is_stale = serializers.BooleanField(read_only=True)


class HoldingsOverviewResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True)
    limit = serializers.IntegerField(read_only=True)
    offset = serializers.IntegerField(read_only=True)
    results = HoldingOverviewItemSerializer(many=True, read_only=True)


class RecentActivityItemSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    investment_id = serializers.UUIDField(read_only=True)
    investment_name = serializers.CharField(read_only=True)
    portfolio_id = serializers.UUIDField(read_only=True)
    portfolio_name = serializers.CharField(read_only=True)
    transaction_type = serializers.CharField(read_only=True)
    transaction_date = serializers.CharField(read_only=True)
    units = serializers.CharField(read_only=True)
    price_per_unit = serializers.CharField(read_only=True)
    amount = serializers.CharField(read_only=True)
    gross_amount = serializers.CharField(read_only=True, allow_null=True)
    fees = serializers.CharField(read_only=True)
    taxes = serializers.CharField(read_only=True)
    net_cash_flow = serializers.CharField(read_only=True, allow_null=True)
    currency = serializers.CharField(read_only=True)
    notes = serializers.CharField(read_only=True, allow_blank=True)
    created_at = serializers.CharField(read_only=True)


class DataQualityCategorySerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True)
    label = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    items = serializers.ListField(child=serializers.DictField(), read_only=True)


class DataQualityResponseSerializer(serializers.Serializer):
    overall_status = serializers.CharField(read_only=True)
    total_active_holdings = serializers.IntegerField(read_only=True)
    categories = serializers.DictField(child=DataQualityCategorySerializer(), read_only=True)
