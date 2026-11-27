"""CoinGecko HTTP API client."""
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from django.conf import settings

from apps.market_data.providers.coingecko.constants import DEFAULT_BASE_URL, DEMO_API_HEADER
from apps.market_data.providers.coingecko.exceptions import (
    CoinGeckoAPIError,
    CoinGeckoAuthenticationError,
    CoinGeckoNotFoundError,
    CoinGeckoRateLimitError,
)

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    """Authenticated backend client for CoinGecko Demo API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (base_url or getattr(settings, 'COINGECKO_BASE_URL', DEFAULT_BASE_URL)).rstrip('/')
        self.api_key = api_key if api_key is not None else getattr(settings, 'COINGECKO_API_KEY', '')
        self.timeout = timeout or getattr(settings, 'COINGECKO_REQUEST_TIMEOUT', 20)

    def _build_request(self, path: str, params: Optional[Dict[str, Any]] = None) -> urllib.request.Request:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                url = f"{url}?{urllib.parse.urlencode(clean_params)}"

        headers = {
            'User-Agent': 'PortfolioManager-Crypto/1.0',
            'Accept': 'application/json',
        }
        if self.api_key:
            headers[DEMO_API_HEADER] = self.api_key

        return urllib.request.Request(url, headers=headers)

    def _execute(self, request: urllib.request.Request, max_retries: int = 2) -> Any:
        attempts = 0
        last_exception = None

        while attempts <= max_retries:
            attempts += 1
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    charset = response.headers.get_content_charset() or 'utf-8'
                    body = response.read().decode(charset)
                    return json.loads(body)
            except urllib.error.HTTPError as e:
                # Sanitize log: never log header values
                logger.warning("CoinGecko HTTP request returned status %d for %s", e.code, request.get_full_url())
                if e.code in (401, 403):
                    raise CoinGeckoAuthenticationError(f"Authentication failed with status {e.code}") from e
                if e.code == 404:
                    raise CoinGeckoNotFoundError("Requested coin or resource was not found") from e
                if e.code == 429:
                    raise CoinGeckoRateLimitError("CoinGecko API rate limit exceeded") from e
                if e.code >= 500:
                    last_exception = e
                    if attempts <= max_retries:
                        time.sleep(0.5 * attempts)
                        continue
                    raise CoinGeckoAPIError(f"Server error {e.code} from CoinGecko", status_code=e.code) from e
                raise CoinGeckoAPIError(f"Client error {e.code} from CoinGecko", status_code=e.code) from e
            except urllib.error.URLError as e:
                last_exception = e
                if attempts <= max_retries:
                    time.sleep(0.5 * attempts)
                    continue
                raise CoinGeckoAPIError(f"Network error contacting CoinGecko: {e.reason}") from e
            except json.JSONDecodeError as e:
                raise CoinGeckoAPIError(f"Invalid JSON payload returned by CoinGecko: {e}") from e

        if last_exception:
            raise CoinGeckoAPIError(f"Request failed after {max_retries} retries: {last_exception}")

    def ping(self) -> bool:
        """Connectivity check endpoint."""
        req = self._build_request('ping')
        res = self._execute(req, max_retries=1)
        return isinstance(res, dict) and 'gecko_says' in res

    def get_coins_list(self) -> List[Dict[str, str]]:
        """Retrieve full supported coins list."""
        req = self._build_request('coins/list')
        data = self._execute(req)
        if not isinstance(data, list):
            raise CoinGeckoAPIError("Expected list response from coins/list")
        return data

    def get_simple_price(
        self,
        ids: List[str],
        vs_currency: str = 'inr',
        include_market_cap: bool = True,
        include_24hr_vol: bool = True,
        include_24hr_change: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """Retrieve price and 24h summary for multiple coin IDs."""
        if not ids:
            return {}
        params = {
            'ids': ','.join(ids),
            'vs_currencies': vs_currency.lower(),
            'include_market_cap': 'true' if include_market_cap else 'false',
            'include_24hr_vol': 'true' if include_24hr_vol else 'false',
            'include_24hr_change': 'true' if include_24hr_change else 'false',
        }
        req = self._build_request('simple/price', params=params)
        data = self._execute(req)
        if not isinstance(data, dict):
            raise CoinGeckoAPIError("Expected dictionary response from simple/price")
        return data

    def get_markets(
        self,
        ids: Optional[List[str]] = None,
        vs_currency: str = 'inr',
        order: str = 'market_cap_desc',
        per_page: int = 100,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """Retrieve market details including price, cap, volume, and 24h high/low."""
        params = {
            'vs_currency': vs_currency.lower(),
            'order': order,
            'per_page': per_page,
            'page': page,
            'sparkline': 'false',
        }
        if ids:
            params['ids'] = ','.join(ids)
        req = self._build_request('coins/markets', params=params)
        data = self._execute(req)
        if not isinstance(data, list):
            raise CoinGeckoAPIError("Expected list response from coins/markets")
        return data

    def get_market_chart(
        self,
        coin_id: str,
        days: int = 30,
        vs_currency: str = 'inr',
        interval: Optional[str] = 'daily',
    ) -> Dict[str, Any]:
        """Retrieve historical market chart data (prices, market caps, total volumes)."""
        params = {
            'vs_currency': vs_currency.lower(),
            'days': days,
        }
        if interval:
            params['interval'] = interval
        req = self._build_request(f'coins/{coin_id}/market_chart', params=params)
        data = self._execute(req)
        if not isinstance(data, dict):
            raise CoinGeckoAPIError(f"Expected dict response for market_chart of {coin_id}")
        return data
