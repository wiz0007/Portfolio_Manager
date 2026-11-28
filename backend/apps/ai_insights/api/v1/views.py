import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_insights.api.v1.serializers import (
    AIExplainRequestSerializer,
    AIExplainResponseSerializer,
    AIStatusResponseSerializer,
)
from apps.ai_insights.providers.openai_client import (
    AIAuthenticationError,
    AIInvalidRequestError,
    AIProviderException,
    AIRateLimitError,
    AIRefusalError,
    AITimeoutError,
)
from apps.ai_insights.services.insight_generator import AIInsightService
from apps.assets.models.investment import Investment
from apps.portfolios.models import Portfolio
from core.permissions import IsAuthenticatedAndEmailVerified

logger = logging.getLogger(__name__)


class AIExplainView(APIView):
    """
    Generate an educational, context-grounded AI explanation for portfolio or holding analytics.
    Enforces strict user ownership, structured Pydantic output, and safe error normalization.
    """
    permission_classes = [IsAuthenticatedAndEmailVerified]

    @extend_schema(
        summary="Explain Portfolio Performance with AI",
        description=(
            "Generates a safe, non-advisory, context-grounded explanation of personal portfolio "
            "metrics, asset allocation, or holding performance using OpenAI Responses API."
        ),
        request=AIExplainRequestSerializer,
        responses={
            200: AIExplainResponseSerializer,
            400: "Invalid request payload or prompt refusal",
            404: "Portfolio or Investment not found or not owned by user",
            429: "OpenAI rate limit or quota exceeded",
            502: "OpenAI upstream communication failure",
            504: "OpenAI request timed out",
        },
        tags=["AI Insights"],
    )
    def post(self, request):
        serializer = AIExplainRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Verify portfolio ownership
        portfolio = get_object_or_404(Portfolio, id=data['portfolio_id'], user=request.user)

        # Verify investment ownership if specified
        investment = None
        if data.get('investment_id'):
            investment = get_object_or_404(
                Investment,
                id=data['investment_id'],
                portfolio=portfolio,
                user=request.user,
            )

        ai_service = AIInsightService()

        try:
            explanation_schema, usage_info = ai_service.explain_portfolio(
                user=request.user,
                portfolio=portfolio,
                question=data['question'],
                investment=investment,
                focus_area=data.get('focus_area'),
                as_of_date=data.get('as_of_date'),
            )

            response_data = {
                'explanation': explanation_schema.model_dump(),
                'usage': usage_info,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except AIRateLimitError as e:
            return Response(
                {
                    'error': {
                        'code': e.code,
                        'message': 'AI explanation service is currently experiencing high demand. Please try again shortly.',
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except AITimeoutError as e:
            return Response(
                {
                    'error': {
                        'code': e.code,
                        'message': 'AI explanation request timed out. Please try asking a more focused question.',
                    }
                },
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except AIRefusalError as e:
            return Response(
                {
                    'error': {
                        'code': e.code,
                        'message': str(e),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except AIAuthenticationError as e:
            logger.error("AI authentication failure: %s", str(e))
            return Response(
                {
                    'error': {
                        'code': e.code,
                        'message': 'AI provider authentication failed on the server. Please check server configuration.',
                    }
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except AIInvalidRequestError as e:
            return Response(
                {
                    'error': {
                        'code': e.code,
                        'message': str(e),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except AIProviderException as e:
            logger.error("AI provider unexpected error: %s", str(e))
            return Response(
                {
                    'error': {
                        'code': e.code,
                        'message': 'Unable to complete AI explanation due to an upstream service issue.',
                    }
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )


class AIStatusView(APIView):
    """
    Check if AI insights are configured and active on the server.
    """
    permission_classes = [IsAuthenticatedAndEmailVerified]

    @extend_schema(
        summary="Check AI Provider Status",
        description="Returns whether the OpenAI API key is configured and which model is selected.",
        responses={200: AIStatusResponseSerializer},
        tags=["AI Insights"],
    )
    def get(self, request):
        service = AIInsightService()
        return Response(
            {
                'is_configured': service.is_configured,
                'model': getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
            },
            status=status.HTTP_200_OK,
        )
