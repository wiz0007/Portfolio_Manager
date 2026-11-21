from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from core.permissions import IsAuthenticatedAndEmailVerified as IsAuthenticated
from rest_framework.response import Response

from apps.assets.api.v1.serializers import (
    InvestmentCreateSerializer,
    InvestmentDetailSerializer,
    InvestmentListSerializer,
    InvestmentUpdateSerializer,
)
from apps.assets.models import Investment
from apps.portfolios.models import Portfolio


class InvestmentListCreateView(generics.ListCreateAPIView):
    """
    List investments for a specific portfolio (or user), or record a new investment.
    Guarantees strict user and portfolio ownership boundaries.
    """

    permission_classes = [IsAuthenticated]

    def get_portfolio(self):
        portfolio_id = self.kwargs.get('portfolio_id') or self.request.query_params.get('portfolio_id')
        if not portfolio_id:
            return None
        return get_object_or_404(Portfolio, id=portfolio_id, user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InvestmentCreateSerializer
        return InvestmentListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Investment.objects.filter(user=user)

        portfolio_id = self.kwargs.get('portfolio_id') or self.request.query_params.get('portfolio_id')
        if portfolio_id:
            # Enforce that portfolio belongs to this user
            portfolio = self.get_portfolio()
            qs = qs.filter(portfolio=portfolio)

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        asset_type = self.request.query_params.get('asset_type')
        if asset_type:
            qs = qs.filter(asset_type=asset_type)

        return qs.select_related('portfolio').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        portfolio_id = self.kwargs.get('portfolio_id')
        if portfolio_id:
            portfolio = self.get_portfolio()
            data['portfolio'] = str(portfolio.id)

        serializer = self.get_serializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return full detail serializer upon creation
        detail_serializer = InvestmentDetailSerializer(instance, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="List Portfolio Investments",
        description="Returns investment holdings owned by the user, optionally filtered by portfolio or category.",
        responses={200: InvestmentListSerializer(many=True)},
        tags=["Investments"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Record New Investment",
        description="Persists a new investment holding, asset-specific details, and initial transaction.",
        request=InvestmentCreateSerializer,
        responses={
            201: InvestmentDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Portfolio not found or unauthorized"),
        },
        tags=["Investments"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class InvestmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific investment holding.
    Cross-user or cross-portfolio attempts return 404 without leaking holding metadata.
    """

    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return InvestmentUpdateSerializer
        return InvestmentDetailSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Investment.objects.filter(user=user)

        portfolio_id = self.kwargs.get('portfolio_id')
        if portfolio_id:
            # Verify portfolio ownership
            get_object_or_404(Portfolio, id=portfolio_id, user=user)
            qs = qs.filter(portfolio_id=portfolio_id)

        return qs.select_related('portfolio')

    @extend_schema(
        summary="Retrieve Investment Detail",
        description="Returns full investment specifications, child details, ledger transactions, and valuations.",
        responses={
            200: InvestmentDetailSerializer,
            404: OpenApiResponse(description="Investment not found or unauthorized"),
        },
        tags=["Investments"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update Investment",
        description="Modifies editable investment fields and nested child attributes.",
        request=InvestmentUpdateSerializer,
        responses={
            200: InvestmentDetailSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Investment not found or unauthorized"),
        },
        tags=["Investments"],
    )
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        detail_serializer = InvestmentDetailSerializer(updated_instance, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete Investment",
        description="Removes an investment holding and all associated child extensions.",
        responses={
            204: OpenApiResponse(description="Investment deleted successfully"),
            404: OpenApiResponse(description="Investment not found or unauthorized"),
        },
        tags=["Investments"],
    )
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.transactions.exists() or instance.valuations.exists():
            return Response(
                {'detail': 'An investment with transaction or valuation history cannot be deleted. Archive functionality must be used instead.'},
                status=status.HTTP_409_CONFLICT,
            )
        return super().delete(request, *args, **kwargs)
