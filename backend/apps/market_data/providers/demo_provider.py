import hashlib
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Dict, List

from apps.market_data.providers.base import (
    BaseMarketDataProvider,
    HistoricalPoint,
    ProviderCapabilities,
    ProviderHealth,
    QuoteData,
)

# Researched Indian Market Price Anchors (November 2026)
RESEARCHED_ANCHORS: Dict[str, Decimal] = {
    'NIFTY50': Decimal('25265.6000'),
    'SENSEX': Decimal('82890.0000'),
    'RELIANCE': Decimal('1344.8000'),
    'TCS': Decimal('2405.0000'),
    'HDFCBANK': Decimal('813.5000'),
    'INFY': Decimal('1145.9000'),
    'ICICIBANK': Decimal('1585.0000'),
    'SBIN': Decimal('1090.5000'),
    'BHARTIARTL': Decimal('1840.0000'),
    'ITC': Decimal('475.5000'),
    'LT': Decimal('3550.0000'),
    '122639': Decimal('94.2590'),   # Parag Parikh Flexi Cap Direct Gr
    '118834': Decimal('124.5000'),  # Mirae Asset Large Cap Direct Gr
    '119598': Decimal('88.7500'),   # SBI Bluechip Direct Gr
    'GOLD24K': Decimal('7850.0000'), # Gold 24k (1g)
}


class DemoMarketDataProvider(BaseMarketDataProvider):
    """
    Deterministic Synthetic Market Data Provider.
    Enables complete development and testing without external API credentials.
    Uses researched November 2026 Indian market prices with realistic, reproducible variations.
    All data is strictly marked with `is_synthetic=True`.
    """

    provider_name = 'DEMO'

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            realtime=True,
            intraday=True,
            daily_eod=True,
            historical=True,
            supported_asset_classes=[
                'EQUITY',
                'MUTUAL_FUND',
                'COMMODITY',
                'FIXED_INCOME',
                'INDEX',
                'CASH_EQUIVALENT',
            ],
        )

    def _get_base_price(self, symbol: str) -> Decimal:
        sym_clean = symbol.upper().strip()
        if sym_clean in RESEARCHED_ANCHORS:
            return RESEARCHED_ANCHORS[sym_clean]
        # Deterministic fallback based on symbol MD5 hash
        digest = hashlib.md5(sym_clean.encode('utf-8')).hexdigest()
        val = int(digest[:6], 16) % 5000 + 100
        return Decimal(str(val))

    def _get_variation_factor(self, symbol: str, target_date: date) -> float:
        """Deterministic pseudo-random variation between -3.0% and +3.0%."""
        seed_str = f"{symbol.upper()}_{target_date.isoformat()}"
        digest = hashlib.sha256(seed_str.encode('utf-8')).hexdigest()
        raw_int = int(digest[:8], 16)
        # Normalize to [-0.03, +0.03]
        pct = ((raw_int % 6000) - 3000) / 100000.0
        return pct

    def get_quote(self, instrument) -> QuoteData:
        symbol = instrument.symbol.upper()
        now_utc = datetime.now(timezone.utc)
        today = now_utc.date()
        base_price = self._get_base_price(symbol)

        pct_change = self._get_variation_factor(symbol, today)
        price_float = float(base_price) * (1.0 + pct_change)
        price = Decimal(f"{price_float:.4f}")

        change_amt_float = float(base_price) * pct_change
        change_amount = Decimal(f"{change_amt_float:.4f}")
        change_percent = Decimal(f"{pct_change * 100:.4f}")

        # Derive plausible intraday high, low, open, close
        vol_factor = abs(pct_change) + 0.005
        high = Decimal(f"{(float(price) * (1.0 + vol_factor)):.4f}")
        low = Decimal(f"{(float(price) * (1.0 - vol_factor)):.4f}")
        open_p = Decimal(f"{(float(base_price) * (1.0 - pct_change * 0.2)):.4f}")

        # Deterministic volume
        digest = hashlib.md5(f"{symbol}_{today}".encode('utf-8')).hexdigest()
        volume = (int(digest[:6], 16) % 2000000) + 50000

        return QuoteData(
            symbol=instrument.symbol,
            price=price,
            open_price=open_p,
            high_price=high,
            low_price=low,
            close_price=price,
            volume=volume,
            change_amount=change_amount,
            change_percent=change_percent,
            timestamp=now_utc,
            provider=self.provider_name,
            is_synthetic=True,
            currency=getattr(instrument, 'currency', 'INR'),
        )

    def get_history(
        self,
        instrument,
        start_date: date,
        end_date: date,
        interval: str = '1D',
    ) -> List[HistoricalPoint]:
        symbol = instrument.symbol.upper()
        base_price = self._get_base_price(symbol)
        points: List[HistoricalPoint] = []

        curr = start_date
        # Running multiplier to simulate random walk
        cumulative_mult = 1.0

        while curr <= end_date:
            # Skip weekends for equity/bonds/indices
            if curr.weekday() < 5 or instrument.asset_class in ['CRYPTO', 'COMMODITY']:
                daily_pct = self._get_variation_factor(symbol, curr)
                cumulative_mult *= (1.0 + daily_pct)
                # Keep multiplier within sane bounds [0.70, 1.30] relative to base
                cumulative_mult = max(0.70, min(1.30, cumulative_mult))

                close_f = float(base_price) * cumulative_mult
                vol_f = abs(daily_pct) + 0.008
                high_f = close_f * (1.0 + vol_f)
                low_f = close_f * (1.0 - vol_f)
                open_f = close_f * (1.0 - daily_pct * 0.5)

                dt = datetime.combine(curr, time(15, 30, tzinfo=timezone.utc))
                h_digest = hashlib.md5(f"{symbol}_{curr}".encode('utf-8')).hexdigest()
                vol = (int(h_digest[:6], 16) % 1500000) + 25000

                change_amt = Decimal(f"{(close_f * daily_pct):.4f}")
                change_pct = Decimal(f"{(daily_pct * 100):.4f}")

                points.append(
                    HistoricalPoint(
                        timestamp=dt,
                        price=Decimal(f"{close_f:.4f}"),
                        open_price=Decimal(f"{open_f:.4f}"),
                        high_price=Decimal(f"{high_f:.4f}"),
                        low_price=Decimal(f"{low_f:.4f}"),
                        close_price=Decimal(f"{close_f:.4f}"),
                        volume=vol,
                        change_amount=change_amt,
                        change_percent=change_pct,
                    )
                )
            curr += timedelta(days=1)

        return points

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            name=self.provider_name,
            is_available=True,
            latency_ms=1.2,
            last_checked=datetime.now(timezone.utc),
            message='Synthetic demo provider online. Serving researched November 2026 prices.',
            mode='DEMO',
            metadata={
                'synthetic': True,
                'anchors_count': len(RESEARCHED_ANCHORS),
                'note': 'Synthetic prices, not live market quotations.',
            },
        )
