import logging
import re
from typing import Any, Dict, List, Set

from apps.ai_insights.schemas.explanation import AIExplanationSchema

logger = logging.getLogger(__name__)

STANDARD_DISCLAIMER = (
    "This explanation is generated for educational and informational purposes only. "
    "It does not constitute financial, investment, legal, or tax advice. "
    "Past performance is not indicative of future results."
)

ALLOWED_METRIC_KEYS: Set[str] = {
    'current_market_value',
    'total_invested_capital',
    'current_cost_basis',
    'cost_basis',
    'realized_pnl',
    'unrealized_pnl',
    'total_pnl',
    'absolute_return_pct',
    'cagr_pct',
    'xirr_pct',
    'twr_pct',
    'active_holdings_count',
    'closed_holdings_count',
    'market_value',
    'market_price',
    'category_allocation',
    'asset_allocation',
    'top_holdings',
    'unvalued_holdings',
}

HTML_TAG_PATTERN = re.compile(r'<[^>]*>')


class AIResponseValidator:
    """
    Validates, post-processes, and sanitizes model output.
    Ensures safe markup, verifies cited metrics against known keys,
    guarantees regulatory disclaimers, and surfaces data completeness warnings.
    """

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Removes potentially dangerous raw HTML while preserving basic markdown formatting.
        """
        if not text:
            return ""
        # Strip raw script/object/iframe tags if any
        cleaned = re.sub(r'<\s*(script|iframe|object|embed|form|link|style)[^>]*>.*?<\s*/\s*\1\s*>', '', text, flags=re.IGNORECASE | re.DOTALL)
        # Strip stray event handlers
        cleaned = re.sub(r'\bon\w+\s*=', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    @classmethod
    def validate_and_sanitize(
        cls,
        schema: AIExplanationSchema,
        portfolio_context: Dict[str, Any],
    ) -> AIExplanationSchema:
        """
        Validates schema fields, normalizes cited metrics, and attaches mandatory disclaimers.
        """
        # 1. Sanitize main answer text
        sanitized_answer = cls.sanitize_text(schema.answer)
        if not sanitized_answer:
            sanitized_answer = "No explanation could be generated based on the provided portfolio data."

        # 2. Sanitize key points
        sanitized_points: List[str] = []
        for point in schema.key_points:
            cleaned_point = cls.sanitize_text(point)
            if cleaned_point:
                sanitized_points.append(cleaned_point)

        # 3. Sanitize and augment limitations
        sanitized_limits: List[str] = [cls.sanitize_text(lim) for lim in schema.limitations if cls.sanitize_text(lim)]
        
        # Cross-reference with context completeness warnings
        data_comp = portfolio_context.get('data_completeness', {})
        context_warnings = data_comp.get('warnings', [])
        for warning in context_warnings:
            if warning not in sanitized_limits:
                sanitized_limits.append(warning)

        # 4. Filter referenced metrics
        normalized_metrics: List[str] = []
        for m in schema.referenced_metrics:
            m_clean = m.strip().lower().replace(" ", "_")
            if m_clean in ALLOWED_METRIC_KEYS and m_clean not in normalized_metrics:
                normalized_metrics.append(m_clean)

        # 5. Ensure disclaimer is populated
        disclaimer = schema.disclaimer.strip() if schema.disclaimer else ""
        if not disclaimer or len(disclaimer) < 10:
            disclaimer = STANDARD_DISCLAIMER

        return AIExplanationSchema(
            answer=sanitized_answer,
            key_points=sanitized_points,
            limitations=sanitized_limits,
            referenced_metrics=normalized_metrics,
            disclaimer=disclaimer,
        )
