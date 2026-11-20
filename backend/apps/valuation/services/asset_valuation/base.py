from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from apps.assets.models.investment import Investment


class ValuationStatus:
    SUCCESS = 'SUCCESS'
    ESTIMATED = 'ESTIMATED'
    INCOMPLETE_INPUT = 'INCOMPLETE_INPUT'
    MARKET_DATA_UNAVAILABLE = 'MARKET_DATA_UNAVAILABLE'
    UNAVAILABLE = 'MARKET_DATA_UNAVAILABLE'
    STALE_DATA = 'STALE_DATA'
    INVALID_INSTRUMENT = 'INVALID_INSTRUMENT'
    UNSUPPORTED_METHOD = 'UNSUPPORTED_METHOD'
    UNSUPPORTED = 'UNSUPPORTED_METHOD'
    INVALID_FINANCIAL_INPUT = 'INVALID_FINANCIAL_INPUT'
    ERROR = 'ERROR'
    SYNTHETIC = 'SYNTHETIC'


class UnsupportedStrategyError(ValueError):
    """Raised when an asset category or product type cannot be mapped to a valid valuation strategy."""
    pass


@dataclass
class ValuationResult:
    """
    Standardized result contract emitted by all asset-specific valuation strategies.
    Deterministic: identical inputs and dates produce identical outputs.
    """
    current_value: Optional[Decimal]
    valuation_method: str
    source: str
    source_reference: str = ''
    observed_at: Optional[datetime] = None
    retrieved_at: Optional[datetime] = None
    calculated_at: Optional[datetime] = None
    status: str = ValuationStatus.SUCCESS
    is_synthetic: bool = False
    currency: str = 'INR'
    metadata: Dict[str, Any] = field(default_factory=dict)
    notes: str = ''

    def __post_init__(self):
        now_utc = datetime.now(timezone.utc)
        if not self.calculated_at:
            self.calculated_at = now_utc
        if not self.observed_at:
            self.observed_at = self.calculated_at
        if not self.retrieved_at:
            self.retrieved_at = self.calculated_at


class BaseAssetValuationStrategy(ABC):
    """
    Abstract base strategy for deterministic asset-specific valuations.
    """

    @abstractmethod
    def evaluate(
        self,
        investment: Investment,
        as_of: Optional[datetime] = None,
    ) -> ValuationResult:
        """
        Calculates the valuation for the given investment holding.
        Must be deterministic: identical inputs yield identical outputs.
        """
        pass
