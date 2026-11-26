from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models.investment import Investment
from apps.assets.models.transactions import InvestmentTransaction
from apps.assets.models.valuations import InvestmentValuation
from apps.market_data.models.coverage import InstrumentCoverage
from apps.market_data.models.instrument import Instrument, InstrumentStatus
from apps.market_data.models.observation import ObservationStatus, PriceObservation, TrustClass
from apps.market_data.models.series import MarketDataSeries
from apps.portfolios.models import Portfolio
from apps.watchlists.models import WatchlistItem

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a():
    return User.objects.create_user(
        email='user_a@example.com',
        password='Password123!',
        full_name='Alpha User',
    )


@pytest.fixture
def user_b():
    return User.objects.create_user(
        email='user_b@example.com',
        password='Password123!',
        full_name='Beta User',
    )


@pytest.mark.django_db
class TestDashboardOverviewAPI:
    def test_unauthenticated_overview_rejected(self, api_client):
        url = reverse('dashboard_api_v1:dashboard-overview')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_receives_valid_overview(self, api_client, user_a):
        url = reverse('dashboard_api_v1:dashboard-overview')
        api_client.force_authenticate(user=user_a)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert 'user' in data
        assert data['user']['id'] == str(user_a.id)
        assert data['user']['full_name'] == 'Alpha User'
        assert data['user']['email'] == 'user_a@example.com'
        assert data['portfolio_count'] == 0
        assert data['recent_portfolios'] == []

    def test_dashboard_user_isolation(self, api_client, user_a, user_b):
        url = reverse('dashboard_api_v1:dashboard-overview')

        api_client.force_authenticate(user=user_a)
        res_a = api_client.get(url)
        assert res_a.status_code == status.HTTP_200_OK
        assert res_a.data['user']['email'] == user_a.email

        api_client.force_authenticate(user=user_b)
        res_b = api_client.get(url)
        assert res_b.status_code == status.HTTP_200_OK
        assert res_b.data['user']['email'] == user_b.email
        assert res_b.data['user']['email'] != res_a.data['user']['email']

    def test_dashboard_reflects_actual_portfolios(self, api_client, user_a, user_b):
        from apps.portfolios.models import Portfolio
        url = reverse('dashboard_api_v1:dashboard-overview')

        # Create portfolios for user_a
        Portfolio.objects.create(user=user_a, name="Alpha Growth", base_currency="INR")
        Portfolio.objects.create(user=user_a, name="Global Tech", base_currency="USD")

        # user_a should see count=2 and both portfolios
        api_client.force_authenticate(user=user_a)
        res_a = api_client.get(url)
        assert res_a.status_code == status.HTTP_200_OK
        assert res_a.data['portfolio_count'] == 2
        assert len(res_a.data['recent_portfolios']) == 2
        names = [p['name'] for p in res_a.data['recent_portfolios']]
        assert "Alpha Growth" in names
        assert "Global Tech" in names

        # user_b has no portfolios, should still see count=0 and empty list
        api_client.force_authenticate(user=user_b)
        res_b = api_client.get(url)
        assert res_b.status_code == status.HTTP_200_OK
        assert res_b.data['portfolio_count'] == 0
        assert res_b.data['recent_portfolios'] == []
        assert 'base_currency' not in res_b.data

    def test_dashboard_updates_after_portfolio_crud(self, api_client, user_a):
        from apps.portfolios.models import Portfolio
        url = reverse('dashboard_api_v1:dashboard-overview')
        api_client.force_authenticate(user=user_a)

        # 1. Initial state: 0 portfolios
        res = api_client.get(url)
        assert res.data['portfolio_count'] == 0
        assert 'base_currency' not in res.data

        # 2. Create portfolio
        p1 = Portfolio.objects.create(user=user_a, name="Crypto Stash", base_currency="USD")
        res = api_client.get(url)
        assert res.data['portfolio_count'] == 1
        assert res.data['recent_portfolios'][0]['name'] == 'Crypto Stash'
        assert res.data['recent_portfolios'][0]['base_currency'] == 'USD'
        assert 'updated_at' in res.data['recent_portfolios'][0]
        assert 'base_currency' not in res.data

        # 3. Update portfolio
        p1.name = "Web3 Assets"
        p1.save()
        res = api_client.get(url)
        assert res.data['recent_portfolios'][0]['name'] == 'Web3 Assets'

        # 4. Delete portfolio
        p1.delete()
        res = api_client.get(url)
        assert res.data['portfolio_count'] == 0
        assert res.data['recent_portfolios'] == []


@pytest.fixture
def portfolio_a(user_a):
    return Portfolio.objects.create(user=user_a, name="Alpha Portfolio", base_currency="INR")


@pytest.fixture
def portfolio_b(user_b):
    return Portfolio.objects.create(user=user_b, name="Beta Portfolio", base_currency="INR")


@pytest.mark.django_db
class TestDashboardOverviewMetrics:
    def test_overview_with_valid_metrics(self, api_client, user_a, portfolio_a):
        url = reverse('dashboard_api_v1:dashboard-overview')
        api_client.force_authenticate(user=user_a)

        # Create 2 investments: 1 equity, 1 cash
        inv1 = Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            category='equity',
            asset_type='listed_stocks',
            display_name='Infosys Limited',
            currency='INR',
            initial_value=Decimal('10000.00'),
            current_value=Decimal('12500.00'),
        )
        InvestmentValuation.objects.create(
            investment=inv1,
            valuation_date=date.today(),
            amount=Decimal('12500.00'),
            currency='INR',
            valuation_method='MARKET_PRICE',
            source='TEST',
        )

        Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            category='cash',
            asset_type='savings_account',
            display_name='HDFC Savings',
            currency='INR',
            initial_value=Decimal('5000.00'),
            current_value=Decimal('5000.00'),
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.data

        assert data['portfolio_count'] == 1
        assert data['active_investment_count'] == 2
        assert data['is_combined'] is True

        summary = data['summary']
        assert summary['currency'] == 'INR'
        assert Decimal(summary['total_invested_capital']) == Decimal('15000.00')
        assert Decimal(summary['total_current_value']) == Decimal('17500.00')
        assert Decimal(summary['absolute_gain_loss']) == Decimal('2500.00')
        assert round(float(summary['gain_loss_percentage']), 2) == 16.67
        assert summary['valued_investment_count'] == 2
        assert summary['unvalued_investment_count'] == 0

    def test_overview_with_negative_return(self, api_client, user_a, portfolio_a):
        url = reverse('dashboard_api_v1:dashboard-overview')
        api_client.force_authenticate(user=user_a)

        Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            category='crypto',
            asset_type='cryptocurrency',
            display_name='Solana Holding',
            currency='INR',
            initial_value=Decimal('10000.00'),
            current_value=Decimal('7000.00'),
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        summary = res.data['summary']
        assert Decimal(summary['absolute_gain_loss']) == Decimal('-3000.00')
        assert Decimal(summary['gain_loss_percentage']) == Decimal('-30.00')

    def test_overview_with_zero_invested_capital(self, api_client, user_a, portfolio_a):
        url = reverse('dashboard_api_v1:dashboard-overview')
        api_client.force_authenticate(user=user_a)

        Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            category='cash',
            asset_type='savings_account',
            display_name='Bonus Grant',
            currency='INR',
            initial_value=Decimal('0.00'),
            current_value=Decimal('500.00'),
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        summary = res.data['summary']
        assert Decimal(summary['total_invested_capital']) == Decimal('0.00')
        assert Decimal(summary['total_current_value']) == Decimal('500.00')
        assert summary['gain_loss_percentage'] is None

    def test_overview_portfolio_scoping_and_cross_user_isolation(self, api_client, user_a, user_b, portfolio_a, portfolio_b):
        url = reverse('dashboard_api_v1:dashboard-overview')
        api_client.force_authenticate(user=user_a)

        # Scoping to own portfolio works
        res = api_client.get(f"{url}?portfolio_id={portfolio_a.id}")
        assert res.status_code == status.HTTP_200_OK
        assert res.data['is_combined'] is False
        assert res.data['selected_portfolio']['id'] == str(portfolio_a.id)

        # Scoping to another user's portfolio returns 404
        res_cross = api_client.get(f"{url}?portfolio_id={portfolio_b.id}")
        assert res_cross.status_code == status.HTTP_404_NOT_FOUND

        # Invalid UUID returns 404
        res_invalid = api_client.get(f"{url}?portfolio_id=not-a-valid-uuid")
        assert res_invalid.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestDashboardAllocationAPI:
    def test_allocation_by_asset_class_and_portfolio(self, api_client, user_a, portfolio_a):
        url = reverse('dashboard_api_v1:dashboard-allocation')
        api_client.force_authenticate(user=user_a)

        p2 = Portfolio.objects.create(user=user_a, name="Retirement Fund", base_currency="INR")

        Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            category='equity',
            asset_type='listed_stocks',
            display_name='TCS',
            currency='INR',
            initial_value=Decimal('6000.00'),
            current_value=Decimal('6000.00'),
        )
        Investment.objects.create(
            user=user_a,
            portfolio=p2,
            category='mutual_funds',
            asset_type='mutual_fund',
            display_name='Nifty Index Fund',
            currency='INR',
            initial_value=Decimal('4000.00'),
            current_value=Decimal('4000.00'),
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.data

        assert Decimal(data['denominator_value']) == Decimal('10000.00')
        assert data['valued_count'] == 2
        assert data['unvalued_count'] == 0
        assert data['has_unvalued_assets'] is False

        # Asset class allocation: 60% equity, 40% mutual_funds
        cat_alloc = data['asset_class_allocation']
        assert len(cat_alloc) == 2
        assert cat_alloc[0]['category'] == 'equity'
        assert Decimal(cat_alloc[0]['percentage']) == Decimal('60.00')
        assert cat_alloc[1]['category'] == 'mutual_funds'
        assert Decimal(cat_alloc[1]['percentage']) == Decimal('40.00')

        # Portfolio allocation: 60% portfolio_a, 40% p2
        port_alloc = data['portfolio_allocation']
        assert len(port_alloc) == 2

    def test_allocation_excludes_unvalued_holdings_from_denominator(self, api_client, user_a, portfolio_a):
        url = reverse('dashboard_api_v1:dashboard-allocation')
        api_client.force_authenticate(user=user_a)

        # 1 valued investment of 5000, 1 unvalued investment of 0 current_value
        Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            category='equity',
            asset_type='listed_stocks',
            display_name='Valued Stock',
            currency='INR',
            initial_value=Decimal('5000.00'),
            current_value=Decimal('5000.00'),
        )
        Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            category='gold',
            asset_type='physical_gold',
            display_name='Unvalued Gold',
            currency='INR',
            initial_value=Decimal('2000.00'),
            current_value=Decimal('0.00'),
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.data

        assert Decimal(data['denominator_value']) == Decimal('5000.00')
        assert data['valued_count'] == 1
        assert data['unvalued_count'] == 1
        assert data['has_unvalued_assets'] is True
        assert len(data['asset_class_allocation']) == 1
        assert Decimal(data['asset_class_allocation'][0]['percentage']) == Decimal('100.00')


@pytest.mark.django_db
class TestDashboardHoldingsAPI:
    def test_holdings_overview_sorting_and_filtering(self, api_client, user_a, portfolio_a):
        url = reverse('dashboard_api_v1:dashboard-holdings')
        api_client.force_authenticate(user=user_a)

        Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            category='equity',
            asset_type='listed_stocks',
            display_name='Alpha Stock',
            currency='INR',
            initial_value=Decimal('1000.00'),
            current_value=Decimal('1500.00'),
        )
        Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            category='fixed_income',
            asset_type='fixed_deposit',
            display_name='Beta FD',
            currency='INR',
            initial_value=Decimal('10000.00'),
            current_value=Decimal('10500.00'),
        )

        # Sort by current_value desc (Beta FD first)
        res_desc = api_client.get(f"{url}?sort_by=current_value&order=desc")
        assert res_desc.status_code == status.HTTP_200_OK
        assert res_desc.data['count'] == 2
        assert res_desc.data['results'][0]['display_name'] == 'Beta FD'
        assert res_desc.data['results'][1]['display_name'] == 'Alpha Stock'

        # Filter by category equity
        res_eq = api_client.get(f"{url}?category=equity")
        assert res_eq.status_code == status.HTTP_200_OK
        assert res_eq.data['count'] == 1
        assert res_eq.data['results'][0]['display_name'] == 'Alpha Stock'


@pytest.mark.django_db
class TestDashboardRecentActivityAPI:
    def test_recent_activity_deterministic_order(self, api_client, user_a, portfolio_a):
        url = reverse('dashboard_api_v1:dashboard-recent-activity')
        api_client.force_authenticate(user=user_a)

        inv = Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            category='equity',
            asset_type='listed_stocks',
            display_name='Reliance',
            currency='INR',
            initial_value=Decimal('2000.00'),
            current_value=Decimal('2000.00'),
        )

        tx1 = InvestmentTransaction.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            investment=inv,
            transaction_type='BUY',
            transaction_date=date(2026, 11, 10),
            units=Decimal('1'),
            price_per_unit=Decimal('2000.00'),
            amount=Decimal('2000.00'),
            gross_amount=Decimal('2000.00'),
            fees=Decimal('10.00'),
            taxes=Decimal('5.00'),
            net_cash_flow=Decimal('2015.00'),
            currency='INR',
        )

        tx2 = InvestmentTransaction.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            investment=inv,
            transaction_type='BUY',
            transaction_date=date(2026, 11, 15),
            units=Decimal('2'),
            price_per_unit=Decimal('2100.00'),
            amount=Decimal('4200.00'),
            gross_amount=Decimal('4200.00'),
            fees=Decimal('20.00'),
            taxes=Decimal('10.00'),
            net_cash_flow=Decimal('4230.00'),
            currency='INR',
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        results = res.data
        assert len(results) == 2
        # Newer transaction date (Nov 15) must appear first
        assert results[0]['id'] == str(tx2.id)
        assert results[0]['transaction_date'] == '2026-11-15'
        assert Decimal(results[0]['net_cash_flow']) == Decimal('4230.00')
        assert results[1]['id'] == str(tx1.id)


@pytest.mark.django_db
class TestDashboardDataQualityAPI:
    def test_data_quality_detects_stale_and_missing(self, api_client, user_a, portfolio_a):
        url = reverse('dashboard_api_v1:dashboard-data-quality')
        api_client.force_authenticate(user=user_a)

        # Instrument 1: published price is stale
        inst1 = Instrument.objects.create(
            symbol="STALE_CORP",
            name="Stale Corporation",
            asset_class="EQUITY",
            currency="INR",
            status=InstrumentStatus.ACTIVE,
        )
        InstrumentCoverage.objects.create(
            instrument=inst1,
            freshness_hours=24,
            price_type="CLOSE",
            currency="INR",
            unit="UNITS",
        )
        series1 = MarketDataSeries.objects.create(
            instrument_id=inst1.id,
            price_type="CLOSE",
            currency="INR",
            unit="UNITS",
            source="NSE",
            exchange="NSE",
            is_active=True,
        )
        PriceObservation.objects.create(
            instrument=inst1,
            series=series1,
            price_type="CLOSE",
            value=Decimal('100.00'),
            currency="INR",
            unit="UNITS",
            source="NSE",
            effective_at=datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc),
            status=ObservationStatus.PUBLISHED,
            trust_class=TrustClass.VERIFIED_OFFICIAL,
            recorded_by=user_a,
        )

        Investment.objects.create(
            user=user_a,
            portfolio=portfolio_a,
            instrument=inst1,
            category='equity',
            asset_type='listed_stocks',
            display_name='Stale Corp Holding',
            currency='INR',
            initial_value=Decimal('1000.00'),
            current_value=Decimal('1000.00'),
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.data

        assert data['total_active_holdings'] == 1
        assert data['overall_status'] in ('WARNING', 'INCOMPLETE')
        assert data['categories']['stale']['count'] == 1


@pytest.mark.django_db
class TestDashboardWatchlistPreviewAPI:
    def test_watchlist_preview_returns_annotated_items(self, api_client, user_a):
        url = reverse('dashboard_api_v1:dashboard-watchlist-preview')
        api_client.force_authenticate(user=user_a)

        inst = Instrument.objects.create(
            symbol="INFY",
            name="Infosys Limited",
            asset_class="EQUITY",
            currency="INR",
            status=InstrumentStatus.ACTIVE,
        )
        InstrumentCoverage.objects.create(
            instrument=inst,
            price_type="CLOSE",
            currency="INR",
            unit="UNITS",
        )
        series = MarketDataSeries.objects.create(
            instrument_id=inst.id,
            price_type="CLOSE",
            currency="INR",
            unit="UNITS",
            source="NSE",
            exchange="NSE",
            is_active=True,
        )
        PriceObservation.objects.create(
            instrument=inst,
            series=series,
            price_type="CLOSE",
            value=Decimal('1850.50'),
            currency="INR",
            unit="UNITS",
            source="NSE",
            effective_at=datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc),
            status=ObservationStatus.PUBLISHED,
            trust_class=TrustClass.VERIFIED_OFFICIAL,
            recorded_by=user_a,
        )

        WatchlistItem.objects.create(
            user=user_a,
            instrument=inst,
            notes="Tech sector monitor",
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        results = res.data
        assert len(results) == 1
        assert results[0]['instrument']['symbol'] == 'INFY'
        assert Decimal(results[0]['market_data']['price']) == Decimal('1850.50')
