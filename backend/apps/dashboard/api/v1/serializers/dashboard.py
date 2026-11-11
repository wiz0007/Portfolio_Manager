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
    updated_at = serializers.DateTimeField(read_only=True)


class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer representing the aggregated dashboard state."""

    user = DashboardUserSerializer(read_only=True)
    portfolio_count = serializers.IntegerField(read_only=True, default=0)
    recent_portfolios = RecentPortfolioSerializer(many=True, read_only=True, default=list)
