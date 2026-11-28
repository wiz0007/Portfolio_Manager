from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.assets.models.investment import AssetCategory, Investment
from apps.assets.models.transactions import InvestmentTransaction
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.observation import ObservationStatus, PriceObservation, TrustClass
from apps.market_data.models.series import MarketDataSeries
from apps.portfolios.models import Portfolio
from apps.users.models import User


@pytest.fixture
def auth_client():
    client = APIClient()
    user = User.objects.create_user(
        email='analytics_user@example.com',
        password='Password123!',
        full_name='Analytics User',
        email_verified_at='2026-01-01T00:00:00Z',
    )
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def sample_portfolio(auth_client):
    _, user = auth_client
    return Portfolio.objects.create(
        user=user,
        name='Tech Growth Portfolio',
        base_currency='INR',
    )


@pytest.fixture
def sample_stock_holding(sample_portfolio, auth_client):
    _, user = auth_client
    inst = Instrument.objects.create(
        symbol='INFY',
        name='Infosys Limited',
        asset_class=AssetClass.EQUITY,
        exchange='NSE',
        currency='INR',
    )
    series = MarketDataSeries.objects.using('market_data').create(
        instrument_id=inst.id,
        price_type='LTP',
        source='NSE_FEED',
        currency='INR',
        unit='UNITS',
        is_active=True,
    )
    PriceObservation.objects.using('market_data').create(
        series=series,
        instrument=inst,
        price_type='LTP',
        value=Decimal('1500.00'),
        currency='INR',
        unit='UNITS',
        effective_at='2026-11-20T10:00:00Z',
        source='NSE_FEED',
        trust_class=TrustClass.VERIFIED_OFFICIAL,
        status=ObservationStatus.PUBLISHED,
    )

    inv = Investment.objects.create(
        portfolio=sample_portfolio,
        user=user,
        instrument=inst,
        category=AssetCategory.EQUITY,
        asset_type='STOCK',
        display_name='Infosys Limited',
        currency='INR',
        initial_value=Decimal('10000.00'),
        current_value=Decimal('15000.00'),
    )

    # Initial purchase: 10 units @ 1000
    InvestmentTransaction.objects.create(
        investment=inv,
        portfolio=sample_portfolio,
        user=user,
        transaction_type='INITIAL_PURCHASE',
        transaction_date=date(2026, 1, 1),
        units=Decimal('10.0000'),
        price_per_unit=Decimal('1000.0000'),
        amount=Decimal('10000.0000'),
        gross_amount=Decimal('10000.0000'),
        net_cash_flow=Decimal('10000.0000'),
    )
    return inv


@pytest.mark.django_db
class TestAnalyticsAPIEndpoints:
    def test_investment_performance_endpoint(self, auth_client, sample_stock_holding):
        client, _user = auth_client
        url = f'/api/v1/analytics/investments/{sample_stock_holding.id}/performance/'
        res = client.get(url)
        assert res.status_code == 200
        data = res.json()
        assert data['investment_id'] == str(sample_stock_holding.id)
        assert Decimal(data['current_quantity']) == Decimal('10.0000')
        assert Decimal(data['current_market_price']) == Decimal('1500.0000')
        assert Decimal(data['current_market_value']) == Decimal('15000.0000')
        assert Decimal(data['unrealized_pnl']) == Decimal('5000.0000')
        assert Decimal(data['absolute_return_pct']) == Decimal('50.0000')

    def test_record_partial_sale_updates_performance(self, auth_client, sample_stock_holding, sample_portfolio):
        client, _user = auth_client
        tx_url = f'/api/v1/investments/{sample_stock_holding.id}/transactions/'
        tx_payload = {
            'transaction_type': 'SELL',
            'transaction_date': '2026-06-01',
            'units': '4.0000',
            'price_per_unit': '1600.0000',
            'fees': '50.0000',
        }
        tx_res = client.post(tx_url, tx_payload)
        assert tx_res.status_code == 201

        perf_url = f'/api/v1/analytics/investments/{sample_stock_holding.id}/performance/'
        perf_res = client.get(perf_url)
        assert perf_res.status_code == 200
        data = perf_res.json()

        assert Decimal(data['current_quantity']) == Decimal('6.0000')
        assert Decimal(data['current_cost_basis']) == Decimal('6000.0000')
        assert Decimal(data['realized_pnl']) == Decimal('2350.0000')
        assert Decimal(data['current_market_value']) == Decimal('9000.0000')
        assert Decimal(data['unrealized_pnl']) == Decimal('3000.0000')
        assert Decimal(data['total_pnl']) == Decimal('5350.0000')

    def test_overselling_holding_is_rejected(self, auth_client, sample_stock_holding):
        client, _user = auth_client
        tx_url = f'/api/v1/investments/{sample_stock_holding.id}/transactions/'
        tx_payload = {
            'transaction_type': 'SELL',
            'transaction_date': '2026-06-01',
            'units': '15.0000',  # Only 10 available
            'price_per_unit': '1500.0000',
        }
        tx_res = client.post(tx_url, tx_payload)
        assert tx_res.status_code == 400
        assert 'units' in tx_res.json()

    def test_future_dated_transaction_is_rejected(self, auth_client, sample_stock_holding):
        client, _user = auth_client
        tomorrow = date.today() + timedelta(days=1)
        tx_url = f'/api/v1/investments/{sample_stock_holding.id}/transactions/'
        tx_payload = {
            'transaction_type': 'BUY',
            'transaction_date': tomorrow.isoformat(),
            'units': '5.0000',
            'price_per_unit': '1500.0000',
        }
        tx_res = client.post(tx_url, tx_payload)
        assert tx_res.status_code == 400
        assert 'transaction_date' in tx_res.json()

    def test_invalid_date_range_is_rejected(self, auth_client, sample_portfolio):
        client, _user = auth_client
        perf_url = f'/api/v1/analytics/portfolios/{sample_portfolio.id}/performance/?start_date=2026-12-01&end_date=2026-01-01'
        res = client.get(perf_url)
        assert res.status_code == 400
        assert 'start_date' in res.json()

    def test_portfolio_performance_and_allocation(self, auth_client, sample_portfolio, sample_stock_holding):
        client, _user = auth_client
        perf_url = f'/api/v1/analytics/portfolios/{sample_portfolio.id}/performance/'
        res = client.get(perf_url)
        assert res.status_code == 200
        p_data = res.json()
        assert p_data['portfolio_id'] == str(sample_portfolio.id)
        assert Decimal(p_data['current_value']) == Decimal('15000.00')

        alloc_url = f'/api/v1/analytics/portfolios/{sample_portfolio.id}/allocation/'
        alloc_res = client.get(alloc_url)
        assert alloc_res.status_code == 200
        alloc_data = alloc_res.json()
        assert len(alloc_data['by_asset_category']) == 1
        assert alloc_data['by_asset_category'][0]['key'] == 'equity'
        assert Decimal(alloc_data['by_asset_category'][0]['percentage']) == Decimal('100.00')

    def test_transaction_reversal_workflow_and_lot_restoration(self, auth_client, sample_stock_holding):
        client, _user = auth_client
        tx_url = f'/api/v1/investments/{sample_stock_holding.id}/transactions/'

        # Record a sale of 4 units
        sell_payload = {
            'transaction_type': 'SELL',
            'transaction_date': '2026-06-01',
            'units': '4.0000',
            'price_per_unit': '1600.0000',
        }
        sell_res = client.post(tx_url, sell_payload)
        assert sell_res.status_code == 201
        sell_tx_id = sell_res.json()['id']

        # Verify performance shows 6 remaining units
        perf_url = f'/api/v1/analytics/investments/{sample_stock_holding.id}/performance/'
        p1 = client.get(perf_url).json()
        assert Decimal(p1['current_quantity']) == Decimal('6.0000')

        # Reverse the sell transaction
        rev_url = f'/api/v1/investments/{sample_stock_holding.id}/transactions/{sell_tx_id}/reverse/'
        rev_res = client.post(rev_url, {'reason': 'Order canceled by broker'})
        assert rev_res.status_code == 201
        rev_data = rev_res.json()
        assert rev_data['transaction_type'] == 'REVERSAL'
        assert rev_data['reversal_of'] == sell_tx_id
        assert rev_data['reversal_reason'] == 'Order canceled by broker'

        # Attempt to reverse again (prohibited)
        rev_repeat_res = client.post(rev_url, {'reason': 'Duplicate'})
        assert rev_repeat_res.status_code == 400
        assert 'already been reversed' in rev_repeat_res.json()['detail']

        # Attempt to reverse the reversal (prohibited)
        rev_of_rev_url = f'/api/v1/investments/{sample_stock_holding.id}/transactions/{rev_data["id"]}/reverse/'
        rev_of_rev_res = client.post(rev_of_rev_url, {'reason': 'Invalid'})
        assert rev_of_rev_res.status_code == 400

        # Verify performance shows restored 10 units!
        p2 = client.get(perf_url).json()
        assert Decimal(p2['current_quantity']) == Decimal('10.0000')

    def test_fx_conversion_and_multi_currency_portfolio(self, auth_client, sample_portfolio):
        from apps.analytics.models.fx import FXRate
        client, user = auth_client
        today = date.today()

        # Seed FX rate: 1 USD = 84.000000 INR
        FXRate.objects.create(
            base_currency='USD',
            quote_currency='INR',
            effective_date=today,
            rate=Decimal('84.000000'),
            source='RBI_REFERENCE',
            is_published=True,
        )

        # Create USD holding in sample INR portfolio
        usd_inv = Investment.objects.create(
            portfolio=sample_portfolio,
            user=user,
            category=AssetCategory.CRYPTO,
            asset_type='CRYPTO',
            display_name='Bitcoin Treasury',
            currency='USD',
            initial_value=Decimal('100.00'),
            current_value=Decimal('200.00'),  # 200 USD
        )
        InvestmentTransaction.objects.create(
            investment=usd_inv,
            portfolio=sample_portfolio,
            user=user,
            transaction_type='INITIAL_PURCHASE',
            transaction_date=today,
            units=Decimal('0.0020'),
            price_per_unit=Decimal('50000.00'),
            amount=Decimal('100.00'),
            gross_amount=Decimal('100.00'),
            currency='USD',
        )

        perf_url = f'/api/v1/analytics/portfolios/{sample_portfolio.id}/performance/'
        p_res = client.get(perf_url)
        assert p_res.status_code == 200
        p_data = p_res.json()

        # Converted value: 200 USD * 84 INR/USD = 16800.00 INR
        assert Decimal(p_data['current_value']) == Decimal('16800.00')
        assert p_data['currency'] == 'INR'
        assert p_data['data_completeness']['is_complete'] is True
