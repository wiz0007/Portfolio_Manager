import logging
import urllib.request
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from apps.market_data.providers.base import (
    BaseMarketDataProvider,
    HistoricalPoint,
    ProviderCapabilities,
    ProviderHealth,
    QuoteData,
)

logger = logging.getLogger(__name__)

# Researched fallback anchors for development/demo testing
# Explicitly flagged with is_synthetic=True and fixed anchor date (November 15, 2026)
AMFI_SCHEME_FALLBACKS: Dict[str, Dict[str, str]] = {
    '122639': {
        'name': 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth',
        'nav': '94.2590',
        'date': '2026-11-15',
    },
    '118834': {
        'name': 'Mirae Asset Large Cap Fund - Direct Plan - Growth Option',
        'nav': '124.5000',
        'date': '2026-11-15',
    },
    '119598': {
        'name': 'SBI Bluechip Fund - Direct Plan - Growth',
        'nav': '88.7500',
        'date': '2026-11-15',
    },
    '101181': {
        'name': 'HDFC Top 100 Fund - Growth',
        'nav': '1120.3500',
        'date': '2026-11-15',
    },
}


class AMFIMarketDataProvider(BaseMarketDataProvider):
    """
    AMFI India Mutual Fund NAV Provider.
    Retrieves official daily Net Asset Value for Indian mutual fund schemes.
    Preserves strict data provenance and marks offline samples as synthetic.
    """

    provider_name = 'AMFI'
    AMFI_NAV_URL = 'https://www.amfiindia.com/spages/NAVAll.txt'

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            realtime=False,
            intraday=False,
            daily_eod=True,
            historical=False,
            supported_asset_classes=['MUTUAL_FUND'],
        )

    def _fetch_amfi_nav(self, scheme_code: str) -> Optional[Tuple[Decimal, datetime]]:
        """Attempt to fetch live NAV text file from AMFI with timeout."""
        try:
            req = urllib.request.Request(
                self.AMFI_NAV_URL,
                headers={'User-Agent': 'PortfolioManager/1.0'},
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                lines = response.read().decode('utf-8', errors='ignore').splitlines()
                for line in lines:
                    parts = line.split(';')
                    if len(parts) >= 6 and parts[0].strip() == scheme_code:
                        try:
                            nav_val = Decimal(parts[4].strip())
                            # Date format in AMFI: DD-Mon-YYYY (e.g. 15-Nov-2026)
                            date_str = parts[5].strip()
                            try:
                                obs_date = datetime.strptime(date_str, '%d-%b-%Y').date()
                                obs_dt = datetime(obs_date.year, obs_date.month, obs_date.day, 16, 0, tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc)
                            except Exception:
                                obs_dt = datetime.now(timezone.utc)
                            return nav_val, obs_dt
                        except Exception:
                            break
        except Exception as e:
            logger.info("AMFI live fetch not accessible, inspecting local anchors: %s", str(e))
        return None

    def get_quote(self, instrument) -> QuoteData:
        symbol = instrument.symbol.strip()
        scheme_code = symbol

        # Check provider mapping if symbol is not purely numeric
        if not scheme_code.isdigit():
            from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
            mapping = ProviderInstrumentMapping.objects.using('market_data').filter(
                instrument_id=instrument.id, provider_name='AMFI', is_primary=True
            ).first() or ProviderInstrumentMapping.objects.using('market_data').filter(
                instrument_id=instrument.id, provider_name='AMFI'
            ).first()
            if mapping:
                scheme_code = mapping.provider_symbol

        live_result = self._fetch_amfi_nav(scheme_code)

        if live_result is not None:
            nav, obs_time = live_result
            return QuoteData(
                symbol=instrument.symbol,
                price=nav,
                close_price=nav,
                timestamp=obs_time,
                provider=self.provider_name,
                is_synthetic=False,
                currency='INR',
            )

        # Static NAV anchors are synthetic development fixtures only.
        from django.conf import settings
        if getattr(settings, 'MARKET_DATA_PROVIDER_MODE', 'DEMO').upper() == 'DEMO' and scheme_code in AMFI_SCHEME_FALLBACKS:
            fallback = AMFI_SCHEME_FALLBACKS[scheme_code]
            nav = Decimal(fallback['nav'])
            obs_date = datetime.strptime(fallback['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            return QuoteData(
                symbol=instrument.symbol,
                price=nav,
                close_price=nav,
                timestamp=obs_date,
                provider=f"{self.provider_name}_DEMO_FALLBACK",
                is_synthetic=True,
                currency='INR',
            )

        # Do NOT invent an arbitrary fallback such as 100.0000; raise explicit error
        raise ValueError(
            f"Current NAV is unavailable for AMFI scheme '{scheme_code}'. "
            "Live network connection was unreachable and no static anchor is configured."
        )

    def get_history(
        self,
        instrument,
        start_date: date,
        end_date: date,
        interval: str = '1D',
    ) -> List[HistoricalPoint]:
        # AMFI NAVAll.txt only publishes current day closing NAV; timeseries is unsupported
        raise NotImplementedError(
            "AMFI NAV provider does not support historical timeseries queries. "
            "Use DEMO provider or configured historical market data provider."
        )

    def health_check(self) -> ProviderHealth:
        import time
        started = time.monotonic()
        available = False
        message = 'AMFI endpoint is unreachable.'
        try:
            req = urllib.request.Request(self.AMFI_NAV_URL, headers={'User-Agent': 'PortfolioManager/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                available = response.status == 200
                message = 'AMFI NAV endpoint responded successfully.' if available else f'AMFI returned HTTP {response.status}.'
        except Exception as exc:
            message = f'AMFI health check failed: {exc.__class__.__name__}'
        latency = round((time.monotonic() - started) * 1000, 2) if available else None
        return ProviderHealth(
            name=self.provider_name, is_available=available, latency_ms=latency,
            last_checked=datetime.now(timezone.utc), message=message,
            mode='PRODUCTION', metadata={'endpoint': self.AMFI_NAV_URL},
        )
