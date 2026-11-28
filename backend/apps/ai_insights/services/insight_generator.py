import logging
from datetime import date
from typing import Any, Dict, Optional, Tuple

from apps.ai_insights.providers.openai_client import (
    OpenAIResponsesClient,
)
from apps.ai_insights.schemas.explanation import AIExplanationSchema
from apps.ai_insights.services.context_builder import AIContextBuilder
from apps.ai_insights.services.prompt_builder import AIPromptBuilder
from apps.ai_insights.services.response_validator import AIResponseValidator
from apps.assets.models.investment import Investment
from apps.portfolios.models import Portfolio

logger = logging.getLogger(__name__)

UNCONFIGURED_FALLBACK_TEXT = (
    "AI explanations are currently unconfigured on this environment. "
    "To enable AI-assisted portfolio insights, please configure the `OPENAI_API_KEY` "
    "environment variable on your server."
)


class AIInsightService:
    """
    Authoritative application service orchestrating AI-assisted portfolio explanations.
    Coordinates context extraction, prompt preparation, OpenAI Responses API execution,
    and rigorous post-validation.
    """

    def __init__(self, client: Optional[OpenAIResponsesClient] = None):
        self.client = client or OpenAIResponsesClient()

    @property
    def is_configured(self) -> bool:
        return self.client.is_configured

    def explain_portfolio(
        self,
        user: Any,
        portfolio: Portfolio,
        question: str,
        investment: Optional[Investment] = None,
        focus_area: Optional[str] = None,
        as_of_date: Optional[date] = None,
        model_override: Optional[str] = None,
    ) -> Tuple[AIExplanationSchema, Dict[str, Any]]:
        """
        Generates an educational, context-grounded financial explanation.
        Handles missing API keys gracefully without crashing or throwing 500 errors.
        """
        # 1. Build authoritative context snapshot from canonical domain services
        context = AIContextBuilder.build_portfolio_context(
            user=user,
            portfolio=portfolio,
            investment=investment,
            as_of_date=as_of_date,
        )

        # 2. Check if OpenAI is configured
        if not self.is_configured:
            logger.info("AI explanation requested but OpenAI API key is not configured.")
            fallback_schema = AIExplanationSchema(
                answer=UNCONFIGURED_FALLBACK_TEXT,
                key_points=[
                    "OpenAI API key is missing or blank.",
                    "Portfolio performance calculations remain fully functional and accurate.",
                ],
                limitations=["AI narrative generation is disabled in this environment."],
                referenced_metrics=[],
                disclaimer="This is an informational notice regarding system configuration.",
            )
            usage_info = {
                'model': 'none',
                'latency_seconds': 0.0,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0,
                'is_configured': False,
            }
            return fallback_schema, usage_info

        # 3. Assemble system prompt and user input with XML delimiters
        instructions = AIPromptBuilder.get_system_instructions()
        user_input = AIPromptBuilder.build_user_message(
            question=question,
            portfolio_context=context,
            focus_area=focus_area,
        )

        # 4. Invoke OpenAI Responses API
        raw_schema, usage_info = self.client.generate_explanation(
            instructions=instructions,
            user_input=user_input,
            model_override=model_override,
        )
        usage_info['is_configured'] = True

        # 5. Validate, sanitize, and attach data completeness warnings
        validated_schema = AIResponseValidator.validate_and_sanitize(
            schema=raw_schema,
            portfolio_context=context,
        )

        return validated_schema, usage_info
