from typing import List

from pydantic import BaseModel, Field


class AIExplanationSchema(BaseModel):
    """
    Structured Output Schema for OpenAI Responses API.
    Guarantees strict JSON schema compliance for deterministic parsing.
    """
    answer: str = Field(
        ...,
        description="Comprehensive, factual, plain-language explanation addressing the user's question, grounded strictly in the provided portfolio context."
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Concise factual bullet points summarizing core observations (e.g., return breakdown, dominant asset classes)."
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Explicit caveats regarding missing prices, unvalued holdings, stale market data, or currency conversion boundaries."
    )
    referenced_metrics: List[str] = Field(
        default_factory=list,
        description="List of metric keys from the context actually cited in the answer (e.g., 'current_value', 'xirr_pct', 'cost_basis', 'realized_pnl', 'unrealized_pnl')."
    )
    disclaimer: str = Field(
        default="This explanation is educational and informational only. It does not constitute financial, investment, legal, or tax advice.",
        description="Standard regulatory non-advisory disclosure."
    )
