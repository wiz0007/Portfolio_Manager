from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.portfolios.api.v1.serializers import PortfolioSerializer
from apps.portfolios.models import Portfolio


class PortfolioListCreateView(generics.ListCreateAPIView):
    """
    List all portfolios belonging to the authenticated user, or create a new portfolio.
    Guarantees strict ownership isolation so users can never see other users' portfolios.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PortfolioSerializer

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="List User Portfolios",
        description="Returns all portfolios owned by the currently authenticated user.",
        responses={200: PortfolioSerializer(many=True)},
        tags=["Portfolios"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create Portfolio",
        description="Creates a new portfolio bound exclusively to the authenticated user.",
        request=PortfolioSerializer,
        responses={
            201: PortfolioSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
        tags=["Portfolios"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PortfolioDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific portfolio owned by the authenticated user.
    Attempts to access another user's portfolio return 404 without leaking existence.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PortfolioSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)

    @extend_schema(
        summary="Retrieve Portfolio",
        description="Retrieves portfolio metadata for the given UUID owned by the user.",
        responses={
            200: PortfolioSerializer,
            404: OpenApiResponse(description="Portfolio not found or unauthorized"),
        },
        tags=["Portfolios"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update Portfolio",
        description="Updates portfolio name, description, or base currency.",
        request=PortfolioSerializer,
        responses={
            200: PortfolioSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Portfolio not found or unauthorized"),
        },
        tags=["Portfolios"],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete Portfolio",
        description="Deletes a portfolio owned by the authenticated user.",
        responses={
            204: OpenApiResponse(description="Portfolio deleted successfully"),
            404: OpenApiResponse(description="Portfolio not found or unauthorized"),
        },
        tags=["Portfolios"],
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
