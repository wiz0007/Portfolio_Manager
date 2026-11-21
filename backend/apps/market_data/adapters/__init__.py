import json
import ssl
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal
from typing import List, Optional

from apps.market_data.models.coverage import QuotationUnit
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.observation import PriceType, TrustClass

# Strict TLS certificate verification
SSL_CTX = ssl.create_default_context()
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}


@dataclass
class NormalizedObservation:
    instrument_id: str
    effective_at: datetime
    price_type: str
    value: Decimal
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    volume: Optional[int] = None
    currency: str = 'INR'
    unit: str = QuotationUnit.UNITS
    source: str = 'PERMITTED_SECONDARY_FEED'
    source_reference: str = ''
    trust_class: str = TrustClass.VERIFIED_PERMITTED_SECONDARY
    is_synthetic: bool = False


class BaseHistoricalAdapter(ABC):
    @abstractmethod
    def supports(self, instrument: Instrument) -> bool:
        pass

    @abstractmethod
    def fetch_history(self, instrument: Instrument, start_date: date, end_date: date) -> List[NormalizedObservation]:
        pass


class EquityIndexAdapter(BaseHistoricalAdapter):
    """
    Acquires daily historical OHLCV for supported NSE/BSE listed equities and
    explicitly mapped benchmark indices, using Yahoo Finance as a permitted secondary feed.
    """

    INDEX_TICKER_MAP = {
        'NIFTY 50': '^NSEI',
        'NIFTY NEXT 50': '^NSMIDCP',
        'BANKNIFTY': '^NSEBANK',
        'NIFTY BANK': '^NSEBANK',
        'SENSEX': '^BSESN',
        'BSE SENSEX': '^BSESN',
        'NIFTY IT': '^CNXIT',
        'NIFTY AUTO': '^CNXAUTO',
        'NIFTY PHARMA': '^CNXPHARMA',
        'NIFTY FMCG': '^CNXFMCG',
        'NIFTY METAL': '^CNXMETAL',
        'NIFTY REALTY': '^CNXREALTY',
        'NIFTY ENERGY': '^CNXENERGY',
        'NIFTY INFRA': '^CNXINFRA',
        'NIFTY MIDCAP 50': '^NSEMDCP50',
        'NIFTY MIDCAP 100': '^NSEMDCP100',
        'NIFTY MIDCAP 150': '^NSEMIDCAP150',
        'NIFTY SMALLCAP 50': '^NSESMLCAP50',
        'NIFTY SMALLCAP 100': '^NSESMLCAP100',
        'NIFTY SMALLCAP 250': '^NSESMLCAP250',
        'NIFTY 100': '^CNX100',
        'NIFTY 200': '^CNX200',
        'NIFTY 500': '^CNX500',
        'NIFTY PSU BANK': '^CNXPSUBANK',
        'BSE BANKEX': '^BSEBANK',
    }

    def supports(self, instrument: Instrument) -> bool:
        # Yahoo chart mapping is only asserted for listed equities and supported indices.
        # Do not infer that property, bonds or deposits have equivalent market series.
        return instrument.asset_class in (AssetClass.EQUITY, AssetClass.INDEX)

    def _resolve_ticker(self, instrument: Instrument) -> Optional[str]:
        sym = instrument.symbol.upper()
        if instrument.asset_class == AssetClass.INDEX:
            return self.INDEX_TICKER_MAP.get(sym)

        clean_sym = sym.replace('&', '%26')
        if instrument.exchange not in ('NSE', 'BSE'):
            return None
        if instrument.exchange == 'BSE':
            return f"{clean_sym}.BO"
        return f"{clean_sym}.NS"

    def fetch_history(self, instrument: Instrument, start_date: date, end_date: date) -> List[NormalizedObservation]:
        ticker = self._resolve_ticker(instrument)
        if not ticker:
            return []

        # Request full 5-year historical window
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5y"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as res:
                payload = json.loads(res.read().decode('utf-8'))
        except Exception:
            return []

        chart_res = payload.get('chart', {}).get('result')
        if not chart_res:
            return []

        res_data = chart_res[0]
        timestamps = res_data.get('timestamp', [])
        indicators = res_data.get('indicators', {})
        quote_list = indicators.get('quote', [{}])[0]

        closes = quote_list.get('close', [])
        opens = quote_list.get('open', [])
        highs = quote_list.get('high', [])
        lows = quote_list.get('low', [])
        volumes = quote_list.get('volume', [])

        is_index = instrument.asset_class == AssetClass.INDEX
        price_type = PriceType.CLOSE if is_index else PriceType.LTP
        quotation_unit = (
            QuotationUnit.UNITS
            if is_index
            else (
                QuotationUnit.SHARES
                if instrument.asset_class == AssetClass.EQUITY and instrument.product_type == 'EQUITY'
                else QuotationUnit.UNITS
            )
        )

        observations: List[NormalizedObservation] = []
        source_name = 'YAHOO_FINANCE_FEED'
        source_ref = f"https://finance.yahoo.com/quote/{ticker}"

        for idx, ts in enumerate(timestamps):
            try:
                c_val = closes[idx] if idx < len(closes) else None
                if c_val is None:
                    continue
                dec_close = Decimal(f"{float(c_val):.4f}")
                if dec_close <= Decimal('0'):
                    continue

                obs_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                market_date = obs_dt.astimezone(ZoneInfo('Asia/Kolkata')).date()
                if market_date < start_date or market_date > end_date:
                    continue

                o_val = opens[idx] if idx < len(opens) and opens[idx] is not None else None
                h_val = highs[idx] if idx < len(highs) and highs[idx] is not None else None
                l_val = lows[idx] if idx < len(lows) and lows[idx] is not None else None
                v_val = volumes[idx] if idx < len(volumes) and volumes[idx] is not None else None

                dec_open = Decimal(f"{float(o_val):.4f}") if o_val and o_val > 0 else dec_close
                dec_high = Decimal(f"{float(h_val):.4f}") if h_val and h_val > 0 else dec_close
                dec_low = Decimal(f"{float(l_val):.4f}") if l_val and l_val > 0 else dec_close

                # Guarantee valid OHLC boundaries
                if dec_high < dec_low:
                    dec_high = max(dec_open, dec_close)
                    dec_low = min(dec_open, dec_close)

                observations.append(
                    NormalizedObservation(
                        instrument_id=str(instrument.id),
                        effective_at=obs_dt,
                        price_type=price_type,
                        value=dec_close,
                        open_price=dec_open,
                        high_price=dec_high,
                        low_price=dec_low,
                        volume=int(v_val) if v_val and v_val > 0 else None,
                        currency='INR',
                        unit=quotation_unit,
                        source=source_name,
                        source_reference=source_ref,
                        trust_class=TrustClass.VERIFIED_PERMITTED_SECONDARY,
                        is_synthetic=False,
                    )
                )
            except Exception:
                continue

        return observations


class MutualFundAdapter(BaseHistoricalAdapter):
    """
    Acquires daily historical NAV observations from MFAPI open financial aggregator.
    Correctly labeled as secondary permitted feed rather than official exchange.
    """

    def supports(self, instrument: Instrument) -> bool:
        return instrument.asset_class == AssetClass.MUTUAL_FUND and bool(instrument.scheme_code)

    def fetch_history(self, instrument: Instrument, start_date: date, end_date: date) -> List[NormalizedObservation]:
        scheme_code = instrument.scheme_code
        if not scheme_code:
            return []

        url = f"https://api.mfapi.in/mf/{scheme_code}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as res:
                payload = json.loads(res.read().decode('utf-8'))
        except Exception:
            return []

        nav_entries = payload.get('data', [])
        observations: List[NormalizedObservation] = []
        source_name = 'MFAPI_AGGREGATOR'
        source_ref = f"https://api.mfapi.in/mf/{scheme_code}"

        for entry in nav_entries:
            try:
                date_str = entry.get('date', '')
                nav_str = entry.get('nav', '')
                if not date_str or not nav_str:
                    continue

                # date format: DD-MM-YYYY
                entry_date = datetime.strptime(date_str, '%d-%m-%Y').date()
                if entry_date < start_date or entry_date > end_date:
                    continue

                dec_nav = Decimal(nav_str)
                if dec_nav <= Decimal('0'):
                    continue

                # Mid-day NAV publication timestamp
                eff_dt = datetime(entry_date.year, entry_date.month, entry_date.day, 16, 0, 0, tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(timezone.utc)
                observations.append(
                    NormalizedObservation(
                        instrument_id=str(instrument.id),
                        effective_at=eff_dt,
                        price_type=PriceType.NAV,
                        value=dec_nav,
                        open_price=dec_nav,
                        high_price=dec_nav,
                        low_price=dec_nav,
                        volume=None,
                        currency='INR',
                        unit=QuotationUnit.UNITS,
                        source=source_name,
                        source_reference=source_ref,
                        trust_class=TrustClass.VERIFIED_PERMITTED_SECONDARY,
                        is_synthetic=False,
                    )
                )
            except Exception:
                continue

        observations.sort(key=lambda o: o.effective_at)
        return observations


class CommodityAdapter(BaseHistoricalAdapter):
    """
    Placeholder for commodity history. No production commodity feed is currently
    integrated, so this adapter explicitly advertises no support and returns no data.
    """

    def supports(self, instrument: Instrument) -> bool:
        # No approved production commodity spot/history feed is currently integrated.
        return False

    def fetch_history(self, instrument: Instrument, start_date: date, end_date: date) -> List[NormalizedObservation]:
        return []
