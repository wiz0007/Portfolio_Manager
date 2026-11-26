from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assets.models.investment import Investment
from apps.assets.models.valuations import InvestmentValuation
from apps.valuation.api.v1.serializers import (
    ManualValuationCreateSerializer,
    PerformanceMetricSerializer,
    ProjectionRequestSerializer,
    ValuationSnapshotSerializer,
)
from apps.valuation.services.calculation.projection_engine import ProjectionEngine
from apps.valuation.services.valuation_orchestrator import ValuationOrchestrator
from core.permissions import IsAuthenticatedAndEmailVerified


class BaseInvestmentScopedView(APIView):
    """
    Base view providing verified ownership lookup for an investment holding.
    """
    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get_investment(self, investment_id) -> Investment:
        try:
            return Investment.objects.select_related('portfolio', 'instrument').get(
                id=investment_id,
                portfolio__user=self.request.user,
            )
        except (Investment.DoesNotExist, ValueError):
            raise NotFound(detail="Investment not found.")


class InvestmentCalculateValuationView(BaseInvestmentScopedView):
    """
    POST /api/v1/investments/<id>/valuations/calculate/
    Executes the asset's deterministic valuation strategy, records an immutable snapshot,
    and updates the investment's current_value.
    """

    def post(self, request, investment_id):
        investment = self.get_investment(investment_id)
        snapshot = ValuationOrchestrator.calculate_and_record(
            investment=investment,
            user=request.user,
        )
        serializer = ValuationSnapshotSerializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvestmentValuationListCreateView(BaseInvestmentScopedView):
    """
    GET /api/v1/investments/<id>/valuations/ - List historical snapshots.
    POST /api/v1/investments/<id>/valuations/ - Record a manual valuation snapshot.
    """

    def get(self, request, investment_id):
        investment = self.get_investment(investment_id)
        snapshots = investment.valuations.order_by('-valuation_date', '-created_at')
        serializer = ValuationSnapshotSerializer(snapshots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, investment_id):
        investment = self.get_investment(investment_id)
        input_serializer = ManualValuationCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        data = input_serializer.validated_data
        snapshot = ValuationOrchestrator.record_manual_valuation(
            investment=investment,
            amount=data['amount'],
            valuation_date=data['valuation_date'],
            user=request.user,
            notes=data.get('notes', ''),
            valuation_method=data.get('valuation_method', 'MANUAL'),
        )

        serializer = ValuationSnapshotSerializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InvestmentValuationDetailView(BaseInvestmentScopedView):
    """
    GET /api/v1/investments/<id>/valuations/<valuation_id>/ - Retrieve single snapshot.
    """

    def get(self, request, investment_id, id):
        investment = self.get_investment(investment_id)
        try:
            snapshot = InvestmentValuation.objects.get(id=id, investment=investment)
        except (InvestmentValuation.DoesNotExist, ValueError):
            raise NotFound(detail="Valuation snapshot not found.")

        serializer = ValuationSnapshotSerializer(snapshot)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InvestmentPerformanceView(BaseInvestmentScopedView):
    """
    GET /api/v1/investments/<id>/performance/
    Returns acquisition cost, current value, absolute gain/loss, and return %.
    """

    def get(self, request, investment_id):
        investment = self.get_investment(investment_id)
        metrics = ValuationOrchestrator.get_performance_metrics(investment)
        serializer = PerformanceMetricSerializer(metrics)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InvestmentProjectionCalculateView(BaseInvestmentScopedView):
    """
    POST /api/v1/investments/<id>/projections/calculate/
    Pure calculation of future value scenarios (conservative, base, optimistic, custom).
    Does not mutate the investment.
    """

    def post(self, request, investment_id):
        investment = self.get_investment(investment_id)
        serializer = ProjectionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        projections = ProjectionEngine.calculate_projection(
            investment=investment,
            time_horizon_years=data.get('time_horizon_years', Decimal('5.00')),
            monthly_contribution=data.get('monthly_contribution', Decimal('0.00')),
            contribution_amount=data.get('contribution_amount'),
            contribution_timing=data.get('contribution_timing', 'END_OF_PERIOD'),
            compounding_frequency_per_year=data.get('compounding_frequency_per_year', 12),
            contribution_frequency_per_year=data.get('contribution_frequency_per_year', 12),
            custom_annual_rate=data.get('custom_annual_rate'),
            selected_scenarios=data.get('scenarios'),
        )

        return Response(projections, status=status.HTTP_200_OK)
