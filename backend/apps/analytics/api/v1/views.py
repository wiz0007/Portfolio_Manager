from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.api.v1.serializers import (
    AllocationResponseSerializer,
    BenchmarkComparisonResponseSerializer,
    DateRangeFilterSerializer,
    InvestmentPerformanceResponseSerializer,
    PortfolioPerformanceResponseSerializer,
)
from apps.analytics.services.allocation_service import AllocationAnalyticsService
from apps.analytics.services.benchmark_service import BenchmarkService
from apps.analytics.services.investment_performance_service import InvestmentPerformanceService
from apps.analytics.services.portfolio_performance_service import PortfolioPerformanceService
from apps.assets.models.investment import Investment
from apps.market_data.models.instrument import Instrument
from apps.portfolios.models import Portfolio
from core.permissions import IsAuthenticatedAndEmailVerified


class InvestmentPerformanceView(APIView):
    """Retrieve personal holding performance, historical curve, and timeline for an investment."""
    permission_classes = [IsAuthenticatedAndEmailVerified]

    @extend_schema(
        summary="Investment Performance Analytics",
        description="Returns transaction-aware historical holding value, remaining cost basis, realized/unrealized P/L, CAGR, and XIRR.",
        parameters=[
            OpenApiParameter('start_date', str, OpenApiParameter.QUERY, required=False, description='YYYY-MM-DD start date'),
            OpenApiParameter('end_date', str, OpenApiParameter.QUERY, required=False, description='YYYY-MM-DD end date'),
        ],
        responses={200: InvestmentPerformanceResponseSerializer},
        tags=["Analytics"],
    )
    def get(self, request, pk):
        investment = get_object_or_404(Investment, id=pk, user=request.user)

        filter_serializer = DateRangeFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        start_d = filter_serializer.validated_data.get('start_date')
        end_d = filter_serializer.validated_data.get('end_date')

        result = InvestmentPerformanceService.get_investment_performance(
            investment=investment,
            start_date=start_d,
            end_date=end_d,
        )

        serializer = InvestmentPerformanceResponseSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PortfolioPerformanceView(APIView):
    """Retrieve portfolio performance, capital contributions, and multi-holding time-series."""
    permission_classes = [IsAuthenticatedAndEmailVerified]

    @extend_schema(
        summary="Portfolio Performance Analytics",
        description="Returns historical portfolio market value, invested capital, money-weighted XIRR, and holding summaries.",
        parameters=[
            OpenApiParameter('start_date', str, OpenApiParameter.QUERY, required=False, description='YYYY-MM-DD start date'),
            OpenApiParameter('end_date', str, OpenApiParameter.QUERY, required=False, description='YYYY-MM-DD end date'),
        ],
        responses={200: PortfolioPerformanceResponseSerializer},
        tags=["Analytics"],
    )
    def get(self, request, pk):
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)

        filter_serializer = DateRangeFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        start_d = filter_serializer.validated_data.get('start_date')
        end_d = filter_serializer.validated_data.get('end_date')

        result = PortfolioPerformanceService.get_portfolio_performance(
            portfolio=portfolio,
            start_date=start_d,
            end_date=end_d,
        )

        serializer = PortfolioPerformanceResponseSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PortfolioAllocationView(APIView):
    """Retrieve current asset allocation breakdown for a portfolio."""
    permission_classes = [IsAuthenticatedAndEmailVerified]

    @extend_schema(
        summary="Portfolio Allocation Analytics",
        description="Returns asset class and holding allocation percentages.",
        responses={200: AllocationResponseSerializer},
        tags=["Analytics"],
    )
    def get(self, request, pk):
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        result = AllocationAnalyticsService.get_allocation(user=request.user, portfolio=portfolio)
        serializer = AllocationResponseSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BenchmarkListView(APIView):
    """List available benchmark indices for comparison."""
    permission_classes = [IsAuthenticatedAndEmailVerified]

    @extend_schema(
        summary="Available Benchmarks",
        description="Returns supported benchmark indices (e.g. NIFTY 50, SENSEX).",
        tags=["Analytics"],
    )
    def get(self, request):
        benchmarks = BenchmarkService.get_available_benchmarks()
        return Response(benchmarks, status=status.HTTP_200_OK)


class PortfolioBenchmarkComparisonView(APIView):
    """Compare portfolio historical performance against a benchmark index."""
    permission_classes = [IsAuthenticatedAndEmailVerified]

    @extend_schema(
        summary="Portfolio Benchmark Comparison",
        description="Returns normalized base-100 comparison series and relative performance (Excess Return).",
        parameters=[
            OpenApiParameter('benchmark_id', str, OpenApiParameter.QUERY, required=True, description='UUID of benchmark index'),
            OpenApiParameter('start_date', str, OpenApiParameter.QUERY, required=False, description='YYYY-MM-DD start date'),
            OpenApiParameter('end_date', str, OpenApiParameter.QUERY, required=False, description='YYYY-MM-DD end date'),
        ],
        responses={200: BenchmarkComparisonResponseSerializer},
        tags=["Analytics"],
    )
    def get(self, request, pk):
        portfolio = get_object_or_404(Portfolio, id=pk, user=request.user)
        bench_id = request.query_params.get('benchmark_id')
        if not bench_id:
            return Response({'detail': 'benchmark_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        benchmark = get_object_or_404(Instrument, id=bench_id, asset_class='INDEX')

        filter_serializer = DateRangeFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        start_d = filter_serializer.validated_data.get('start_date')
        end_d = filter_serializer.validated_data.get('end_date')

        result = BenchmarkService.compare_portfolio_to_benchmark(
            portfolio=portfolio,
            benchmark_instrument=benchmark,
            start_date=start_d,
            end_date=end_d,
        )

        serializer = BenchmarkComparisonResponseSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)
