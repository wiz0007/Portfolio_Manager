"""Unit tests for CoinGecko provider client and adapter."""
import io
import json
import urllib.error
from datetime import date
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase, override_settings

from apps.market_data.providers.base import QuoteData
from apps.market_data.providers.coingecko.adapter import CoinGeckoMarketDataProvider
from apps.market_data.providers.coingecko.client import CoinGeckoClient
from apps.market_data.providers.coingecko.constants import DEMO_API_HEADER
from apps.market_data.providers.coingecko.exceptions import (
    CoinGeckoAuthenticationError,
    CoinGeckoNotFoundError,
    CoinGeckoRateLimitError,
)


class MockHTTPResponse:
    def __init__(self, data: Any, status: int = 200, charset: str = 'utf-8'):
        self.data = json.dumps(data).encode(charset) if not isinstance(data, bytes) else data
        self.status = status
        self.headers = MagicMock()
        self.headers.get_content_charset.return_value = charset
        self._io = io.BytesIO(self.data)

    def read(self):
        return self._io.read()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class CoinGeckoClientTests(SimpleTestCase):
    def test_request_headers_include_api_key_when_configured(self):
        client = CoinGeckoClient(base_url='https://api.coingecko.com/api/v3', api_key='test-key-123')
        req = client._build_request('ping')
        self.assertEqual(req.headers.get(DEMO_API_HEADER.capitalize()), 'test-key-123')

    def test_request_headers_omit_api_key_when_empty(self):
        client = CoinGeckoClient(base_url='https://api.coingecko.com/api/v3', api_key='')
        req = client._build_request('ping')
        self.assertNotIn(DEMO_API_HEADER.capitalize(), req.headers)

    @patch('urllib.request.urlopen')
    def test_ping_success(self, mock_urlopen):
        mock_urlopen.return_value = MockHTTPResponse({'gecko_says': '(V3) To the Moon!'})
        client = CoinGeckoClient(api_key='test-key')
        self.assertTrue(client.ping())

    @patch('urllib.request.urlopen')
    def test_client_handles_authentication_error(self, mock_urlopen):
        err = urllib.error.HTTPError(
            url='https://api.coingecko.com/api/v3/ping',
            code=401,
            msg='Unauthorized',
            hdrs={},
            fp=io.BytesIO(b'{"error": "Invalid API Key"}'),
        )
        mock_urlopen.side_effect = err
        client = CoinGeckoClient(api_key='invalid-key')
        with self.assertRaises(CoinGeckoAuthenticationError):
            client.ping()

    @patch('urllib.request.urlopen')
    def test_client_handles_rate_limit(self, mock_urlopen):
        err = urllib.error.HTTPError(
            url='https://api.coingecko.com/api/v3/coins/markets',
            code=429,
            msg='Too Many Requests',
            hdrs={},
            fp=io.BytesIO(b'{"status": {"error_code": 429}}'),
        )
        mock_urlopen.side_effect = err
        client = CoinGeckoClient()
        with self.assertRaises(CoinGeckoRateLimitError):
            client.get_markets(['bitcoin'])

    @patch('urllib.request.urlopen')
    def test_client_handles_not_found(self, mock_urlopen):
        err = urllib.error.HTTPError(
            url='https://api.coingecko.com/api/v3/coins/unknown/market_chart',
            code=404,
            msg='Not Found',
            hdrs={},
            fp=io.BytesIO(b'{"error": "coin not found"}'),
        )
        mock_urlopen.side_effect = err
        client = CoinGeckoClient()
        with self.assertRaises(CoinGeckoNotFoundError):
            client.get_market_chart('unknown')


class CoinGeckoAdapterTests(TestCase):
    databases = {'default', 'market_data'}

    def setUp(self):
        self.mock_client = MagicMock()
        self.adapter = CoinGeckoMarketDataProvider(client=self.mock_client)

    def test_capabilities(self):
        caps = self.adapter.capabilities
        self.assertEqual(caps.supported_asset_classes, ['CRYPTO'])
        self.assertTrue(caps.daily_eod)
        self.assertTrue(caps.historical)
        self.assertFalse(caps.realtime)

    def test_get_quote_returns_quote_data(self):
        inst = MagicMock()
        inst.id = '00000000-0000-0000-0000-000000000001'
        inst.symbol = 'BTC'
        inst.asset_class = 'CRYPTO'

        self.mock_client.get_markets.return_value = [
            {
                'id': 'bitcoin',
                'symbol': 'btc',
                'name': 'Bitcoin',
                'current_price': 8250000.50,
                'market_cap': 162000000000000,
                'total_volume': 3500000000,
                'high_24h': 8300000.0,
                'low_24h': 8150000.0,
                'price_change_24h': 120000.0,
                'price_change_percentage_24h': 1.47,
                'last_updated': '2026-11-26T12:00:00.000Z',
            }
        ]

        quote = self.adapter.get_quote(inst)
        self.assertIsInstance(quote, QuoteData)
        self.assertEqual(quote.symbol, 'BTC')
        self.assertEqual(quote.price, Decimal('8250000.50'))
        self.assertEqual(quote.provider, 'COINGECKO')
        self.assertFalse(quote.is_synthetic)
        self.assertEqual(quote.currency, 'INR')

    def test_get_history_returns_historical_points(self):
        inst = MagicMock()
        inst.id = '00000000-0000-0000-0000-000000000001'
        inst.symbol = 'ETH'
        inst.asset_class = 'CRYPTO'

        self.mock_client.get_market_chart.return_value = {
            'prices': [
                [1764115200000, 275000.0],
                [1764201600000, 280000.0],
            ],
            'total_volumes': [
                [1764115200000, 15000000],
                [1764201600000, 16000000],
            ],
            'market_caps': [
                [1764115200000, 33000000000],
                [1764201600000, 34000000000],
            ],
        }

        # Date range spanning 2025-11-25 to 2025-11-28
        start_d = date(2025, 11, 25)
        end_d = date(2025, 11, 28)
        points = self.adapter.get_history(inst, start_date=start_d, end_date=end_d)
        self.assertEqual(len(points), 2)
        self.assertEqual(points[0].price, Decimal('275000.0'))
        self.assertEqual(points[1].price, Decimal('280000.0'))

    @override_settings(COINGECKO_ENABLED=False)
    def test_health_check_disabled(self):
        health = self.adapter.health_check()
        self.assertFalse(health.is_available)
        self.assertIn('disabled', health.message.lower())

    @override_settings(COINGECKO_ENABLED=True, COINGECKO_API_KEY='')
    def test_health_check_unconfigured(self):
        health = self.adapter.health_check()
        self.assertFalse(health.is_available)
        self.assertIn('not configured', health.message.lower())

    @override_settings(COINGECKO_ENABLED=True, COINGECKO_API_KEY='valid-key')
    def test_health_check_available(self):
        self.mock_client.ping.return_value = True
        health = self.adapter.health_check()
        self.assertTrue(health.is_available)
        self.assertIn('online', health.message.lower())
