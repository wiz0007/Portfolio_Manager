import logging
import time
from typing import Any, Dict, Optional, Tuple

import openai
from django.conf import settings
from openai import OpenAI

from apps.ai_insights.schemas.explanation import AIExplanationSchema

logger = logging.getLogger(__name__)


class AIProviderException(Exception):
    """Base exception for all AI provider operations."""
    code = "AI_PROVIDER_ERROR"

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        if code:
            self.code = code


class AINotConfiguredError(AIProviderException):
    code = "AI_NOT_CONFIGURED"


class AIAuthenticationError(AIProviderException):
    code = "AI_AUTH_ERROR"


class AIRateLimitError(AIProviderException):
    code = "AI_RATE_LIMIT"


class AITimeoutError(AIProviderException):
    code = "AI_TIMEOUT"


class AIConnectionError(AIProviderException):
    code = "AI_CONNECTION_ERROR"


class AIInvalidRequestError(AIProviderException):
    code = "AI_INVALID_REQUEST"


class AIRefusalError(AIProviderException):
    code = "AI_REFUSAL"


class OpenAIResponsesClient:
    """
    Authoritative server-side adapter for OpenAI Responses API.
    Provides structured JSON responses, timeout enforcement, transient retry,
    and safe exception normalization without leaking credentials or internal prompts.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'OPENAI_API_KEY', '')
        self.model = model or getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        self.timeout = getattr(settings, 'OPENAI_REQUEST_TIMEOUT', 30)
        self.max_tokens = getattr(settings, 'OPENAI_MAX_OUTPUT_TOKENS', 1000)
        self._client: Optional[OpenAI] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_client(self) -> OpenAI:
        if not self.is_configured:
            raise AINotConfiguredError("OpenAI API key is not configured on the server.")
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                timeout=float(self.timeout),
                max_retries=2,
            )
        return self._client

    def generate_explanation(
        self,
        instructions: str,
        user_input: str,
        model_override: Optional[str] = None,
    ) -> Tuple[AIExplanationSchema, Dict[str, Any]]:
        """
        Executes a Responses API structured request.
        Returns (parsed_schema, usage_metadata).
        """
        client = self.get_client()
        active_model = model_override or self.model

        start_time = time.time()
        try:
            # We invoke client.responses.parse using AIExplanationSchema for strict structured output
            response = client.responses.parse(
                model=active_model,
                instructions=instructions,
                input=user_input,
                parse_as=AIExplanationSchema,
                max_output_tokens=self.max_tokens,
            )

            latency = round(time.time() - start_time, 3)

            # Check if model refused
            if hasattr(response, 'refusal') and response.refusal:
                raise AIRefusalError(f"Model refused the request: {response.refusal}")

            # Extract parsed output
            parsed_output = getattr(response, 'output_parsed', None)
            if not parsed_output:
                # If parse_as returned in response.output or text
                raw_text = getattr(response, 'output_text', '')
                if raw_text:
                    parsed_output = AIExplanationSchema.model_validate_json(raw_text)
                else:
                    raise AIProviderException("Empty response received from OpenAI.")

            usage_info = {
                'model': active_model,
                'latency_seconds': latency,
                'prompt_tokens': getattr(getattr(response, 'usage', None), 'input_tokens', 0),
                'completion_tokens': getattr(getattr(response, 'usage', None), 'output_tokens', 0),
                'total_tokens': getattr(getattr(response, 'usage', None), 'total_tokens', 0),
            }

            return parsed_output, usage_info

        except AINotConfiguredError:
            raise
        except openai.AuthenticationError as e:
            logger.error("OpenAI Authentication Error: %s", str(e))
            raise AIAuthenticationError("Invalid or unauthorized OpenAI API credentials.", code="AI_AUTH_ERROR") from e
        except openai.RateLimitError as e:
            logger.warning("OpenAI Rate Limit / Quota Exceeded: %s", str(e))
            raise AIRateLimitError("OpenAI rate limit or usage quota exceeded. Please try again later.", code="AI_RATE_LIMIT") from e
        except openai.APITimeoutError as e:
            logger.warning("OpenAI API Timeout after %s seconds: %s", self.timeout, str(e))
            raise AITimeoutError("OpenAI request timed out.", code="AI_TIMEOUT") from e
        except openai.APIConnectionError as e:
            logger.error("OpenAI Connection Failure: %s", str(e))
            raise AIConnectionError("Could not connect to OpenAI API servers.", code="AI_CONNECTION_ERROR") from e
        except openai.BadRequestError as e:
            logger.error("OpenAI Bad Request: %s", str(e))
            raise AIInvalidRequestError(f"Invalid request sent to OpenAI: {e!s}", code="AI_INVALID_REQUEST") from e
        except Exception as e:
            logger.exception("Unexpected error in OpenAI Responses API: %s", str(e))
            raise AIProviderException(f"OpenAI service error: {e!s}") from e
