from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class QuoteData:
    """Normalized quote payload produced by any provider."""
    symbol: str
    price: Decimal
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    volume: Optional[int] = None
    change_amount: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    provider: str = 'UNKNOWN'
    is_synthetic: bool = False
    currency: str = 'INR'


@dataclass
class HistoricalPoint:
    """Normalized historical OHLCV data point."""
    timestamp: datetime
    price: Decimal
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    volume: Optional[int] = None
    change_amount: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None


@dataclass
class ProviderCapabilities:
    """Declaration of market data vendor capabilities."""
    realtime: bool = False
    intraday: bool = False
    daily_eod: bool = True
    historical: bool = True
    supported_asset_classes: List[str] = field(default_factory=lambda: ['EQUITY'])


@dataclass
class ProviderHealth:
    """Health inspection payload for a market data vendor."""
    name: str
    is_available: bool
    latency_ms: Optional[float] = None
    last_checked: datetime = field(default_factory=datetime.utcnow)
    message: str = 'OK'
    mode: str = 'PRODUCTION'
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseMarketDataProvider(ABC):
    """
    Abstract Base Class for all market data provider adapters.
    Guarantees provider independence across backend and frontend consumers.
    """

    provider_name: str = 'BASE'

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Returns provider capabilities."""
        pass

    @abstractmethod
    def get_quote(self, instrument) -> QuoteData:
        """Fetch normalized quote for a single instrument."""
        pass

    def get_quotes(self, instruments: List[Any]) -> Dict[str, QuoteData]:
        """Fetch quotes for multiple instruments (default sequential fallback)."""
        results: Dict[str, QuoteData] = {}
        for inst in instruments:
            try:
                results[inst.symbol] = self.get_quote(inst)
            except Exception:
                continue
        return results

    @abstractmethod
    def get_history(
        self,
        instrument,
        start_date: date,
        end_date: date,
        interval: str = '1D',
    ) -> List[HistoricalPoint]:
        """Fetch historical timeseries points."""
        pass

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """Inspect and report adapter connectivity and credential status."""
        pass
