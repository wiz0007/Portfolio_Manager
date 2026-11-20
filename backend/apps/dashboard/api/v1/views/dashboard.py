from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.api.v1.serializers.dashboard import (
    AssetAllocationResponseSerializer,
    DashboardOverviewSerializer,
    DataQualityResponseSerializer,
    HoldingsOverviewResponseSerializer,
    RecentActivityItemSerializer,
)
from apps.dashboard.services.dashboard_service import DashboardService
from apps.watchlists.api.v1.serializers import WatchlistItemResponseSerializer


class DashboardOverviewView(APIView):
    """
    Retrieve personalized dashboard overview for the authenticated user.
    Supports optional portfolio scoping via ?portfolio_id=<uuid>.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dashboard Overview",
        description="Returns aggregated financial metrics, portfolio counts, recent portfolios, and valuation completeness.",
        parameters=[
            OpenApiParameter(
                name='portfolio_id',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Optional UUID to scope metrics to an individual user portfolio.',
            ),
        ],
        responses={
            200: DashboardOverviewSerializer,
            401: OpenApiResponse(description="Unauthenticated"),
            404: OpenApiResponse(description="Portfolio not found or unauthorized"),
        },
        tags=["Dashboard"],
    )
    def get(self, request):
        portfolio_id = request.query_params.get('portfolio_id')
        try:
            data = DashboardService.get_user_dashboard_overview(request.user, portfolio_id=portfolio_id)
        except (ObjectDoesNotExist, ValidationError):
            return Response(
                {"detail": f"Portfolio '{portfolio_id}' not found or does not belong to the user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DashboardOverviewSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssetAllocationView(APIView):
    """
    Retrieve asset allocation breakdown by asset class, portfolio, and top holdings.
    Calculates allocation percentages from authoritative current eligible valuations.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Asset Allocation Breakdown",
        description="Returns asset class and portfolio allocation percentages calculated from current eligible valuations.",
        parameters=[
            OpenApiParameter(
                name='portfolio_id',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Optional UUID to scope allocation to an individual portfolio.',
            ),
            OpenApiParameter(
                name='currency',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Optional currency code (e.g. INR, USD) to filter allocation metrics.',
            ),
        ],
        responses={
            200: AssetAllocationResponseSerializer,
            401: OpenApiResponse(description="Unauthenticated"),
            404: OpenApiResponse(description="Portfolio not found"),
        },
        tags=["Dashboard"],
    )
    def get(self, request):
        portfolio_id = request.query_params.get('portfolio_id')
        currency = request.query_params.get('currency')
        try:
            data = DashboardService.get_asset_allocation(
                request.user,
                portfolio_id=portfolio_id,
                currency=currency,
            )
        except (ObjectDoesNotExist, ValidationError):
            return Response(
                {"detail": f"Portfolio '{portfolio_id}' not found or does not belong to the user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AssetAllocationResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HoldingsOverviewView(APIView):
    """
    Retrieve concise holdings overview with filtering, sorting, pagination, and data freshness.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Holdings Overview",
        description="Returns concise investment holdings with gain/loss calculations, valuation dates, and price freshness.",
        parameters=[
            OpenApiParameter(
                name='portfolio_id',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter holdings by portfolio UUID.',
            ),
            OpenApiParameter(
                name='category',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter holdings by asset category (e.g. equity, mutual_funds, cash).',
            ),
            OpenApiParameter(
                name='sort_by',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Sort key: 'current_value', 'invested_capital', 'gain_loss', or 'display_name'.",
            ),
            OpenApiParameter(
                name='order',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Sort direction: 'asc' or 'desc' (default 'desc').",
            ),
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Page limit (default 20, max 100).',
            ),
            OpenApiParameter(
                name='offset',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Page offset (default 0).',
            ),
        ],
        responses={
            200: HoldingsOverviewResponseSerializer,
            401: OpenApiResponse(description="Unauthenticated"),
            404: OpenApiResponse(description="Portfolio not found"),
        },
        tags=["Dashboard"],
    )
    def get(self, request):
        portfolio_id = request.query_params.get('portfolio_id')
        category = request.query_params.get('category')
        sort_by = request.query_params.get('sort_by', 'current_value')
        order = request.query_params.get('order', 'desc')
        is_active_param = request.query_params.get('is_active')
        is_active = is_active_param.lower() in ('true', '1') if is_active_param is not None else True

        try:
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))
        except ValueError:
            limit = 20
            offset = 0

        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        try:
            data = DashboardService.get_holdings_overview(
                request.user,
                portfolio_id=portfolio_id,
                category=category,
                is_active=is_active,
                sort_by=sort_by,
                order=order,
                limit=limit,
                offset=offset,
            )
        except (ObjectDoesNotExist, ValidationError):
            return Response(
                {"detail": f"Portfolio '{portfolio_id}' not found or does not belong to the user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = HoldingsOverviewResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecentActivityView(APIView):
    """
    Retrieve recent persisted investment transactions.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Recent Investment Activity",
        description="Returns recent persisted investment transactions with canonical gross amounts, fees, and taxes.",
        parameters=[
            OpenApiParameter(
                name='portfolio_id',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Filter transactions by portfolio UUID.',
            ),
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Number of transactions to return (default 10, max 50).',
            ),
        ],
        responses={
            200: RecentActivityItemSerializer(many=True),
            401: OpenApiResponse(description="Unauthenticated"),
            404: OpenApiResponse(description="Portfolio not found"),
        },
        tags=["Dashboard"],
    )
    def get(self, request):
        portfolio_id = request.query_params.get('portfolio_id')
        try:
            limit = int(request.query_params.get('limit', 10))
        except ValueError:
            limit = 10

        try:
            data = DashboardService.get_recent_activity(
                request.user,
                portfolio_id=portfolio_id,
                limit=limit,
            )
        except (ObjectDoesNotExist, ValidationError):
            return Response(
                {"detail": f"Portfolio '{portfolio_id}' not found or does not belong to the user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RecentActivityItemSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DataQualityView(APIView):
    """
    Retrieve data reliability diagnostics and valuation status counts.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Valuation Data Quality Diagnostics",
        description="Returns breakdown of successfully valued, stale, missing, unverified, and unsupported holdings.",
        parameters=[
            OpenApiParameter(
                name='portfolio_id',
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Scope data quality diagnostics to an individual portfolio.',
            ),
        ],
        responses={
            200: DataQualityResponseSerializer,
            401: OpenApiResponse(description="Unauthenticated"),
            404: OpenApiResponse(description="Portfolio not found"),
        },
        tags=["Dashboard"],
    )
    def get(self, request):
        portfolio_id = request.query_params.get('portfolio_id')
        try:
            data = DashboardService.get_data_quality(request.user, portfolio_id=portfolio_id)
        except (ObjectDoesNotExist, ValidationError):
            return Response(
                {"detail": f"Portfolio '{portfolio_id}' not found or does not belong to the user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DataQualityResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WatchlistPreviewView(APIView):
    """
    Retrieve top user watchlist items for dashboard preview.
    Reuses existing central WatchlistService and MarketPriceResolver.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Watchlist Preview",
        description="Returns top watchlist holdings with published prices, freshness, and 24h movement.",
        parameters=[
            OpenApiParameter(
                name='limit',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Number of watchlist items to preview (default 5, max 10).',
            ),
        ],
        responses={
            200: WatchlistItemResponseSerializer(many=True),
            401: OpenApiResponse(description="Unauthenticated"),
        },
        tags=["Dashboard"],
    )
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 5))
        except ValueError:
            limit = 5

        data = DashboardService.get_watchlist_preview(request.user, limit=limit)
        serializer = WatchlistItemResponseSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
