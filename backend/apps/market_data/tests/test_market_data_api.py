from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.market_data_point import MarketDataPoint
from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
from apps.market_data.models.reference_data import (
    InstrumentReferenceData,
    MarketCapCategory,
)
from apps.market_data.providers.demo_provider import DemoMarketDataProvider
from apps.market_data.providers.registry import provider_registry
from apps.market_data.services.market_data_service import MarketDataService

User = get_user_model()


@pytest.fixture
def auth_client():
    user = User.objects.create_user(
        email='trader@portfoliomanager.local',
        password='StrongPassword123!',
        full_name='Market Trader',
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def sample_instruments():
    # Equities
    reliance = Instrument.objects.create(
        symbol='RELIANCE',
        name='Reliance Industries Ltd.',
        asset_class=AssetClass.EQUITY,
        exchange='NSE',
        currency='INR',
        isin='INE002A01018',
        is_active=True,
    )
    InstrumentReferenceData.objects.create(
        instrument=reliance,
        sector='Energy',
        industry='Oil & Gas',
        market_cap_category=MarketCapCategory.LARGE_CAP,
    )

    tcs = Instrument.objects.create(
        symbol='TCS',
        name='Tata Consultancy Services Ltd.',
        asset_class=AssetClass.EQUITY,
        exchange='NSE',
        currency='INR',
        isin='INE467B01029',
        is_active=True,
    )

    # Mutual fund
    ppfas = Instrument.objects.create(
        symbol='122639',
        name='Parag Parikh Flexi Cap Fund - Direct Plan - Growth',
        asset_class=AssetClass.MUTUAL_FUND,
        exchange='AMFI',
        currency='INR',
        isin='INF879O01018',
        is_active=True,
    )

    # Index
    nifty = Instrument.objects.create(
        symbol='NIFTY50',
        name='NIFTY 50 Index',
        asset_class=AssetClass.INDEX,
        exchange='NSE',
        currency='INR',
        is_active=True,
    )

    # Inactive instrument
    inactive = Instrument.objects.create(
        symbol='DELISTED',
        name='Old Delisted Corp',
        asset_class=AssetClass.EQUITY,
        exchange='BSE',
        is_active=False,
    )

    return {
        'reliance': reliance,
        'tcs': tcs,
        'ppfas': ppfas,
        'nifty': nifty,
        'inactive': inactive,
    }


@pytest.mark.django_db
class TestInstrumentAPI:
    """Tests corresponding to INS-001, INS-002, INS-003."""

    def test_unauthenticated_instruments_access_rejected(self):
        client = APIClient()
        response = client.get('/api/v1/instruments/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_ins_001_list_and_filter_instruments(self, auth_client, sample_instruments):
        client, _ = auth_client

        # List all active instruments
        response = client.get('/api/v1/instruments/?is_active=true')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        symbols = [item['symbol'] for item in results]
        assert 'RELIANCE' in symbols
        assert 'TCS' in symbols
        assert '122639' in symbols
        assert 'DELISTED' not in symbols

        # Filter by asset class
        response = client.get('/api/v1/instruments/?asset_class=MUTUAL_FUND')
        assert response.status_code == status.HTTP_200_OK
        mf_results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert len(mf_results) == 1
        assert mf_results[0]['symbol'] == '122639'

        # Filter by exchange
        response = client.get('/api/v1/instruments/?exchange=AMFI')
        assert response.status_code == status.HTTP_200_OK
        ex_results = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert len(ex_results) == 1
        assert ex_results[0]['exchange'] == 'AMFI'

    def test_ins_002_fuzzy_search_instruments(self, auth_client, sample_instruments):
        client, _ = auth_client

        # Search by symbol
        response = client.get('/api/v1/instruments/search/?q=RELI')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]['symbol'] == 'RELIANCE'

        # Search by company name
        response = client.get('/api/v1/instruments/search/?q=Consultancy')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]['symbol'] == 'TCS'

        # Search by ISIN
        response = client.get('/api/v1/instruments/search/?q=INF879O01018')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['symbol'] == '122639'

        # Blank search returns empty list
        response = client.get('/api/v1/instruments/search/?q=')
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_ins_003_retrieve_instrument_detail_with_reference_data(self, auth_client, sample_instruments):
        client, _ = auth_client
        inst = sample_instruments['reliance']

        response = client.get(f'/api/v1/instruments/{inst.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data['id'] == str(inst.id)
        assert data['symbol'] == 'RELIANCE'
        assert data['reference_data'] is not None
        assert data['reference_data']['sector'] == 'Energy'
        assert data['reference_data']['market_cap_category'] == 'LARGE_CAP'


@pytest.mark.django_db
class TestMarketDataAPI:
    """Tests corresponding to MKT-001, MKT-002, MKT-003, MKT-004, MKT-005."""

    def test_mkt_001_latest_quote_single_and_bulk(self, auth_client, sample_instruments):
        client, _ = auth_client
        reliance = sample_instruments['reliance']

        # Single quote retrieval
        response = client.get(f'/api/v1/market-data/quotes/{reliance.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data['symbol'] == 'RELIANCE'
        assert Decimal(data['price']) > 0
        assert data['is_synthetic'] is True
        assert data['provider'] == 'DEMO'

        # Bulk quote retrieval by symbol list
        response = client.get('/api/v1/market-data/quotes/?symbols=RELIANCE,TCS')
        assert response.status_code == status.HTTP_200_OK
        assert 'RELIANCE' in response.data
        assert 'TCS' in response.data
        assert Decimal(response.data['RELIANCE']['price']) > 0
        assert Decimal(response.data['TCS']['price']) > 0

        # Non-existent instrument ID returns 404
        response = client.get('/api/v1/market-data/quotes/00000000-0000-0000-0000-000000000000/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_mkt_002_historical_timeseries_retrieval(self, auth_client, sample_instruments):
        client, _ = auth_client
        tcs = sample_instruments['tcs']

        # Request 15 days of history
        response = client.get(f'/api/v1/market-data/history/{tcs.id}/?days=15&interval=1D')
        assert response.status_code == status.HTTP_200_OK
        points = response.data
        assert len(points) >= 5
        for p in points:
            assert 'timestamp' in p
            assert Decimal(p['price']) > 0
            assert p['is_synthetic'] is True

    def test_mkt_003_provider_registry_resolution(self, sample_instruments):
        reliance = sample_instruments['reliance']
        ppfas = sample_instruments['ppfas']

        # In default DEMO mode, DEMO provider handles requests
        prov_rel = provider_registry.get_provider_for_instrument(reliance)
        assert prov_rel.provider_name == 'DEMO'

        # Provider list contains DEMO, AMFI, TRUEDATA
        providers = provider_registry.list_providers()
        names = [p['name'] for p in providers]
        assert 'DEMO' in names
        assert 'AMFI' in names
        assert 'TRUEDATA' in names

    def test_mkt_004_provider_health_check_api(self, auth_client):
        client, _ = auth_client
        response = client.get('/api/v1/market-data/health/')
        assert response.status_code == status.HTTP_200_OK
        reports = {r['name']: r for r in response.data}
        assert 'DEMO' in reports
        assert reports['DEMO']['is_available'] is True
        assert reports['DEMO']['mode'] == 'DEMO'
        assert 'TRUEDATA' in reports
        assert reports['TRUEDATA']['mode'] == 'PENDING_CREDENTIALS'

    def test_mkt_005_demo_provider_deterministic_behavior(self, sample_instruments):
        demo = DemoMarketDataProvider()
        reliance = sample_instruments['reliance']

        quote = demo.get_quote(reliance)
        assert quote.symbol == 'RELIANCE'
        assert quote.is_synthetic is True
        # Researched anchor for RELIANCE is 1344.80, variations should stay within +/- 5%
        assert Decimal('1200.0000') <= quote.price <= Decimal('1500.0000')

        # Historical series length and bounds
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=20)
        history = demo.get_history(reliance, start, today)
        assert len(history) >= 10
        for pt in history:
            assert Decimal('1000.0000') <= pt.price <= Decimal('1700.0000')

    def test_market_overview_endpoint(self, auth_client, sample_instruments):
        client, _ = auth_client
        response = client.get('/api/v1/market-data/overview/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert 'indices' in data
        assert 'equities' in data
        assert 'mutual_funds' in data
        assert data['is_demo_mode'] is True
        assert 'DEMO DATA' in data['demo_notice']
