"""MFAPI HTTP client."""
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from django.conf import settings

from apps.market_data.providers.mfapi.constants import DEFAULT_BASE_URL
from apps.market_data.providers.mfapi.exceptions import (
    MFAPIConnectionError,
    MFAPIError,
    MFAPINotFoundError,
)

logger = logging.getLogger(__name__)


class MFAPIClient:
    """Client for MFAPI.in Indian Mutual Fund NAV API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (base_url or getattr(settings, 'MFAPI_BASE_URL', DEFAULT_BASE_URL)).rstrip('/')
        self.timeout = timeout or getattr(settings, 'MFAPI_REQUEST_TIMEOUT', 20)

    def _build_request(self, path: str, params: Optional[Dict[str, Any]] = None) -> urllib.request.Request:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                url = f"{url}?{urllib.parse.urlencode(clean_params)}"

        headers = {
            'User-Agent': 'PortfolioManager-MFAPI/1.0',
            'Accept': 'application/json',
        }
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
                logger.warning("MFAPI HTTP request returned status %d for %s", e.code, request.get_full_url())
                if e.code == 404:
                    raise MFAPINotFoundError("Mutual fund scheme not found") from e
                if e.code >= 500:
                    last_exception = e
                    if attempts <= max_retries:
                        time.sleep(0.5 * attempts)
                        continue
                    raise MFAPIConnectionError(f"Server error {e.code} from MFAPI", status_code=e.code) from e
                raise MFAPIError(f"Client error {e.code} from MFAPI") from e
            except urllib.error.URLError as e:
                last_exception = e
                if attempts <= max_retries:
                    time.sleep(0.5 * attempts)
                    continue
                raise MFAPIConnectionError(f"Network error contacting MFAPI: {e.reason}") from e
            except json.JSONDecodeError as e:
                raise MFAPIError(f"Invalid JSON returned by MFAPI: {e}") from e

        if last_exception:
            raise MFAPIConnectionError(f"Request failed after {max_retries} retries: {last_exception}")

    def ping(self) -> bool:
        """Health check using search endpoint."""
        try:
            req = self._build_request('mf/search', params={'q': 'HDFC'})
            res = self._execute(req, max_retries=1)
            return isinstance(res, list)
        except Exception:
            return False

    def search_schemes(self, query: str) -> List[Dict[str, Any]]:
        """Search mutual fund schemes by name or code."""
        if not query or len(query.strip()) < 2:
            return []
        req = self._build_request('mf/search', params={'q': query.strip()})
        res = self._execute(req)
        if not isinstance(res, list):
            raise MFAPIError("Expected list response for scheme search")
        return res

    def get_scheme(self, scheme_code: str) -> Dict[str, Any]:
        """Fetch scheme metadata and all historical NAV entries."""
        code = str(scheme_code).strip()
        if not code:
            raise ValueError("scheme_code must not be empty")
        req = self._build_request(f'mf/{code}')
        res = self._execute(req)
        if not isinstance(res, dict) or 'data' not in res:
            raise MFAPIError(f"Unexpected response structure for scheme {code}")
        return res
