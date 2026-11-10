from rest_framework import serializers


class DashboardUserSerializer(serializers.Serializer):
    """Basic user information for the dashboard overview."""
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)


class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer representing the aggregated dashboard state."""
    user = DashboardUserSerializer(read_only=True)
    portfolio_count = serializers.IntegerField(read_only=True, default=0)
    recent_portfolios = serializers.ListField(
        child=serializers.DictField(),
        read_only=True,
        default=list
    )
