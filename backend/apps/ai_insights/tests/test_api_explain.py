from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.ai_insights.providers.openai_client import (
    AIRateLimitError,
    AIRefusalError,
    AITimeoutError,
)
from apps.ai_insights.schemas.explanation import AIExplanationSchema


@pytest.mark.django_db
class TestAIInsightsAPI:

    def test_status_endpoint_authenticated(self, auth_client):
        response = auth_client.get('/api/v1/ai/status/')
        assert response.status_code == status.HTTP_200_OK
        assert 'is_configured' in response.data
        assert 'model' in response.data

    def test_explain_unauthenticated(self, sample_portfolio):
        unauth_client = APIClient()
        response = unauth_client.post(
            '/api/v1/ai/explain/',
            {'portfolio_id': str(sample_portfolio.id), 'question': 'How is my portfolio doing?'},
            format='json',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_explain_other_users_portfolio(self, auth_client, other_portfolio):
        # other_portfolio belongs to other_user
        response = auth_client.post(
            '/api/v1/ai/explain/',
            {'portfolio_id': str(other_portfolio.id), 'question': 'How is my portfolio doing?'},
            format='json',
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_explain_unconfigured_openai_fallback(self, auth_client, sample_portfolio):
        with patch('apps.ai_insights.services.insight_generator.OpenAIResponsesClient.is_configured', False):
            response = auth_client.post(
                '/api/v1/ai/explain/',
                {'portfolio_id': str(sample_portfolio.id), 'question': 'Explain my returns'},
                format='json',
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data['usage']['is_configured'] is False
            assert "unconfigured" in response.data['explanation']['answer'].lower()

    def test_explain_successful_mocked_openai_response(self, auth_client, sample_portfolio):
        mock_explanation = AIExplanationSchema(
            answer="Your portfolio is valued at $10,000 with strong allocation in Equities.",
            key_points=["Equities comprise 70% of your holdings", "XIRR stands at 14.2%"],
            limitations=["Crypto prices are as of yesterday"],
            referenced_metrics=["current_market_value", "xirr_pct"],
            disclaimer="Educational only.",
        )
        mock_usage = {
            'model': 'gpt-4o-mini',
            'latency_seconds': 1.12,
            'prompt_tokens': 450,
            'completion_tokens': 120,
            'total_tokens': 570,
        }

        with patch('apps.ai_insights.services.insight_generator.OpenAIResponsesClient.is_configured', True), \
             patch('apps.ai_insights.services.insight_generator.OpenAIResponsesClient.generate_explanation', return_value=(mock_explanation, mock_usage)):
            
            response = auth_client.post(
                '/api/v1/ai/explain/',
                {
                    'portfolio_id': str(sample_portfolio.id),
                    'question': 'Can you explain why my return increased this month?',
                    'focus_area': 'performance',
                },
                format='json',
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.data
            assert 'explanation' in data
            assert 'usage' in data
            assert data['explanation']['answer'] == mock_explanation.answer
            assert len(data['explanation']['key_points']) == 2
            assert data['usage']['prompt_tokens'] == 450
            assert data['usage']['is_configured'] is True

    def test_explain_rate_limit_error(self, auth_client, sample_portfolio):
        with patch('apps.ai_insights.services.insight_generator.OpenAIResponsesClient.is_configured', True), \
             patch('apps.ai_insights.services.insight_generator.OpenAIResponsesClient.generate_explanation', side_effect=AIRateLimitError("Rate limit exceeded")):
            
            response = auth_client.post(
                '/api/v1/ai/explain/',
                {'portfolio_id': str(sample_portfolio.id), 'question': 'Explain everything'},
                format='json',
            )

            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert response.data['error']['code'] == 'AI_RATE_LIMIT'

    def test_explain_timeout_error(self, auth_client, sample_portfolio):
        with patch('apps.ai_insights.services.insight_generator.OpenAIResponsesClient.is_configured', True), \
             patch('apps.ai_insights.services.insight_generator.OpenAIResponsesClient.generate_explanation', side_effect=AITimeoutError("Timed out")):
            
            response = auth_client.post(
                '/api/v1/ai/explain/',
                {'portfolio_id': str(sample_portfolio.id), 'question': 'Explain everything'},
                format='json',
            )

            assert response.status_code == status.HTTP_504_GATEWAY_TIMEOUT
            assert response.data['error']['code'] == 'AI_TIMEOUT'

    def test_explain_refusal_error(self, auth_client, sample_portfolio):
        with patch('apps.ai_insights.services.insight_generator.OpenAIResponsesClient.is_configured', True), \
             patch('apps.ai_insights.services.insight_generator.OpenAIResponsesClient.generate_explanation', side_effect=AIRefusalError("Model refused: financial advice not permitted")):
            
            response = auth_client.post(
                '/api/v1/ai/explain/',
                {'portfolio_id': str(sample_portfolio.id), 'question': 'Should I buy Tesla stock right now?'},
                format='json',
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'refused' in response.data['error']['message']
