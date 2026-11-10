from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.api.v1.serializers.dashboard import DashboardOverviewSerializer
from apps.dashboard.services.dashboard_service import DashboardService


class DashboardOverviewView(APIView):
    """
    Retrieve personalized dashboard overview for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dashboard Overview",
        description="Returns personalized dashboard overview statistics and recent portfolio summaries.",
        responses={
            200: DashboardOverviewSerializer,
            401: OpenApiResponse(description="Unauthenticated"),
        },
        tags=["Dashboard"]
    )
    def get(self, request):
        data = DashboardService.get_user_dashboard_overview(request.user)
        serializer = DashboardOverviewSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
