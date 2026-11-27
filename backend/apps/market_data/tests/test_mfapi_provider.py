"""Unit tests for MFAPI provider client and adapter."""
import io
import json
import urllib.error
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase, override_settings

from apps.market_data.providers.base import QuoteData
from apps.market_data.providers.mfapi.adapter import MFAPIMarketDataProvider
from apps.market_data.providers.mfapi.client import MFAPIClient
from apps.market_data.providers.mfapi.exceptions import (
    MFAPINotFoundError,
)
from apps.market_data.providers.mfapi.serializers import classify_scheme, serialize_nav_data


class MockHTTPResponse:
    def __init__(self, data, status: int = 200, charset: str = 'utf-8'):
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


class MFAPISerializerTests(SimpleTestCase):
    def test_classify_direct_growth(self):
        res = classify_scheme("Parag Parikh Flexi Cap Fund - Direct Plan - Growth")
        self.assertEqual(res['plan_type'], 'DIRECT')
        self.assertEqual(res['option_type'], 'GROWTH')

    def test_classify_regular_idcw(self):
        res = classify_scheme("HDFC Top 100 Fund - Regular Plan - IDCW Option")
        self.assertEqual(res['plan_type'], 'REGULAR')
        self.assertEqual(res['option_type'], 'IDCW')

    def test_serialize_nav_data_sorting(self):
        raw = [
            {'date': '26-11-2026', 'nav': '105.5000'},
            {'date': '24-11-2026', 'nav': '104.2000'},
            {'date': '25-11-2026', 'nav': '105.0000'},
        ]
        res = serialize_nav_data(raw)
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0]['date'], '24-11-2026')
        self.assertEqual(res[1]['date'], '25-11-2026')
        self.assertEqual(res[2]['date'], '26-11-2026')
        self.assertEqual(res[2]['nav'], Decimal('105.5000'))


class MFAPIClientTests(SimpleTestCase):
    @patch('urllib.request.urlopen')
    def test_search_schemes(self, mock_urlopen):
        mock_urlopen.return_value = MockHTTPResponse([
            {'schemeCode': 120503, 'schemeName': 'Tata Digital India Fund - Direct Plan - Growth'}
        ])
        client = MFAPIClient()
        results = client.search_schemes('Tata')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['schemeCode'], 120503)

    @patch('urllib.request.urlopen')
    def test_get_scheme_not_found(self, mock_urlopen):
        err = urllib.error.HTTPError(
            url='https://api.mfapi.in/mf/999999',
            code=404,
            msg='Not Found',
            hdrs={},
            fp=io.BytesIO(b'{"status": "FAIL", "message": "Scheme not found"}'),
        )
        mock_urlopen.side_effect = err
        client = MFAPIClient()
        with self.assertRaises(MFAPINotFoundError):
            client.get_scheme('999999')


class MFAPIAdapterTests(TestCase):
    databases = {'default', 'market_data'}

    def setUp(self):
        self.mock_client = MagicMock()
        self.adapter = MFAPIMarketDataProvider(client=self.mock_client)

    def test_capabilities(self):
        caps = self.adapter.capabilities
        self.assertEqual(caps.supported_asset_classes, ['MUTUAL_FUND'])
        self.assertTrue(caps.daily_eod)
        self.assertTrue(caps.historical)
        self.assertFalse(caps.realtime)

    def test_get_quote(self):
        inst = MagicMock()
        inst.id = '00000000-0000-0000-0000-000000000002'
        inst.symbol = '122639'
        inst.scheme_code = '122639'
        inst.asset_class = 'MUTUAL_FUND'

        self.mock_client.get_scheme.return_value = {
            'meta': {
                'fund_house': 'PPFAS Mutual Fund',
                'scheme_name': 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth',
                'scheme_code': 122639,
            },
            'data': [
                {'date': '24-11-2026', 'nav': '93.5000'},
                {'date': '25-11-2026', 'nav': '94.2590'},
            ],
            'status': 'SUCCESS',
        }

        quote = self.adapter.get_quote(inst)
        self.assertIsInstance(quote, QuoteData)
        self.assertEqual(quote.price, Decimal('94.2590'))
        self.assertEqual(quote.provider, 'MFAPI')
        self.assertFalse(quote.is_synthetic)
        self.assertEqual(quote.currency, 'INR')
        self.assertEqual(quote.change_amount, Decimal('0.7590'))

    def test_get_history(self):
        inst = MagicMock()
        inst.id = '00000000-0000-0000-0000-000000000002'
        inst.symbol = '122639'
        inst.scheme_code = '122639'

        self.mock_client.get_scheme.return_value = {
            'meta': {'scheme_name': 'Parag Parikh Flexi Cap'},
            'data': [
                {'date': '24-11-2026', 'nav': '93.5000'},
                {'date': '25-11-2026', 'nav': '94.2590'},
            ],
        }

        points = self.adapter.get_history(inst, start_date=date(2026, 11, 24), end_date=date(2026, 11, 25))
        self.assertEqual(len(points), 2)
        self.assertEqual(points[0].price, Decimal('93.5000'))
        self.assertEqual(points[1].price, Decimal('94.2590'))

    @override_settings(MFAPI_ENABLED=False)
    def test_health_check_disabled(self):
        health = self.adapter.health_check()
        self.assertFalse(health.is_available)
        self.assertIn('disabled', health.message.lower())

    @override_settings(MFAPI_ENABLED=True)
    def test_health_check_available(self):
        self.mock_client.ping.return_value = True
        health = self.adapter.health_check()
        self.assertTrue(health.is_available)
        self.assertIn('online', health.message.lower())
