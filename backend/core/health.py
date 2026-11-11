import logging

from django.db import connection
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    System health check endpoint verifying application availability and database connectivity.
    Returns 200 OK when the database is accessible.
    Returns 503 Service Unavailable when the database cannot be reached.
    Guarantees no internal database errors, credentials, or hostnames are leaked.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="System Health Check",
        description="Reports application availability and database connectivity.",
        responses={
            200: OpenApiResponse(description="System and database healthy"),
            503: OpenApiResponse(description="Database unavailable"),
        },
        tags=["System"],
    )
    def get(self, request):
        try:
            connection.ensure_connection()
            return Response(
                {"status": "healthy", "database": "connected"},
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception("Health check database probe failed")
            return Response(
                {"status": "unhealthy", "database": "unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
