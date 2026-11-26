from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models.investment import Investment
from apps.assets.models.valuations import InvestmentValuation
from apps.market_data.models.coverage import InstrumentCoverage
from apps.market_data.models.instrument import Instrument, InstrumentStatus
from apps.market_data.models.observation import ObservationStatus, PriceObservation, TrustClass
from apps.market_data.models.series import MarketDataSeries
from apps.portfolios.models import Portfolio

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user():
    return User.objects.create_user(
        email='gap_user@example.com',
        password='Password123!',
        full_name='Gap User',
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(
        email='other_user@example.com',
        password='Password123!',
        full_name='Other User',
    )


@pytest.fixture
def user_portfolio(test_user):
    return Portfolio.objects.create(
        user=test_user,
        name='Main Portfolio',
        base_currency='INR',
    )


@pytest.fixture
def second_portfolio(test_user):
    return Portfolio.objects.create(
        user=test_user,
        name='Second Portfolio',
        base_currency='INR',
    )


def create_instrument_with_series(symbol, name="Corp", status=InstrumentStatus.ACTIVE, price_type="CLOSE", source="NSE"):
    inst = Instrument.objects.create(
        symbol=symbol,
        name=name,
        asset_class="EQUITY",
        currency="INR",
        status=status,
    )
    cov = InstrumentCoverage.objects.create(
        instrument=inst,
        freshness_hours=24,
        price_type=price_type,
        currency="INR",
        unit="UNITS",
    )
    series = MarketDataSeries.objects.create(
        instrument_id=inst.id,
        price_type=price_type,
        currency="INR",
        unit="UNITS",
        source=source,
        exchange="NSE",
        is_active=True,
    )
    return inst, cov, series


@pytest.mark.django_db
class TestHoldingsMarketTimestamps:
    """Issue 2: Verify market price timestamps vs valuation snapshot dates."""

    def test_instrument_holding_returns_market_timestamps_and_age(self, api_client, test_user, user_portfolio):
        url = reverse('dashboard_api_v1:dashboard-holdings')
        api_client.force_authenticate(user=test_user)

        inst, _, series = create_instrument_with_series("TCS", source="NSE")
        eff_dt = datetime(2026, 11, 20, 15, 30, tzinfo=timezone.utc)
        pub_dt = datetime(2026, 11, 20, 16, 0, tzinfo=timezone.utc)

        PriceObservation.objects.create(
            instrument=inst,
            series=series,
            price_type="CLOSE",
            value=Decimal('3500.00'),
            currency="INR",
            unit="UNITS",
            source="NSE",
            effective_at=eff_dt,
            published_at=pub_dt,
            status=ObservationStatus.PUBLISHED,
            trust_class=TrustClass.VERIFIED_OFFICIAL,
            recorded_by=test_user,
        )

        inv = Investment.objects.create(
            user=test_user,
            portfolio=user_portfolio,
            instrument=inst,
            category='equity',
            asset_type='listed_stocks',
            display_name='TCS Ltd',
            currency='INR',
            initial_value=Decimal('3000.00'),
            current_value=Decimal('3500.00'),
        )

        # Historical valuation snapshot with a distinct date
        InvestmentValuation.objects.create(
            investment=inv,
            valuation_date=date(2026, 11, 15),
            amount=Decimal('3400.00'),
            currency='INR',
            source='SNAPSHOT',
            created_by=test_user,
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        items = res.data['results']
        assert len(items) == 1
        item = items[0]

        # Market timestamps come from the resolved observation
        assert item['price_effective_at'] == eff_dt.isoformat()
        assert item['price_published_at'] == pub_dt.isoformat()
        assert item['price_age_seconds'] is not None
        assert isinstance(item['price_age_seconds'], int)

        # Valuation snapshot date is distinct and preserved
        assert item['valuation_date'] == '2026-11-15'
        assert item['valuation_date'] != item['price_effective_at']

    def test_missing_observation_returns_null_market_timestamps(self, api_client, test_user, user_portfolio):
        url = reverse('dashboard_api_v1:dashboard-holdings')
        api_client.force_authenticate(user=test_user)

        inst, _, _ = create_instrument_with_series("NO_OBS")
        Investment.objects.create(
            user=test_user,
            portfolio=user_portfolio,
            instrument=inst,
            category='equity',
            asset_type='listed_stocks',
            display_name='No Price Holding',
            currency='INR',
            initial_value=Decimal('1000.00'),
            current_value=Decimal('0.00'),
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        items = res.data['results']
        assert len(items) == 1
        item = items[0]

        assert item['price_effective_at'] is None
        assert item['price_published_at'] is None
        assert item['price_age_seconds'] is None
        assert item['price_freshness'] == 'MISSING'

    def test_non_instrument_holding_returns_null_market_timestamps(self, api_client, test_user, user_portfolio):
        url = reverse('dashboard_api_v1:dashboard-holdings')
        api_client.force_authenticate(user=test_user)

        inv = Investment.objects.create(
            user=test_user,
            portfolio=user_portfolio,
            instrument=None,
            category='cash',
            asset_type='bank_deposits',
            display_name='Fixed Deposit SBI',
            currency='INR',
            initial_value=Decimal('50000.00'),
            current_value=Decimal('52500.00'),
        )

        InvestmentValuation.objects.create(
            investment=inv,
            valuation_date=date(2026, 11, 19),
            amount=Decimal('52500.00'),
            currency='INR',
            source='MANUAL',
            created_by=test_user,
        )

        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        items = res.data['results']
        assert len(items) == 1
        item = items[0]

        # Non-instrument holdings return MANUAL freshness and null market timestamps
        assert item['price_freshness'] == 'MANUAL'
        assert item['price_effective_at'] is None
        assert item['price_published_at'] is None
        assert item['price_age_seconds'] is None
        assert item['valuation_date'] == '2026-11-19'


@pytest.mark.django_db
class TestDashboardCompletenessAndQualityConsistency:
    """Issue 4: Shared classification consistency between overview and data-quality."""

    def test_awaiting_verification_appears_in_both_endpoints(self, api_client, test_user, user_portfolio):
        api_client.force_authenticate(user=test_user)

        inst, _, series = create_instrument_with_series("PENDING_STK", source="OPERATOR")
        PriceObservation.objects.create(
            instrument=inst,
            series=series,
            price_type="CLOSE",
            value=Decimal('150.00'),
            currency="INR",
            unit="UNITS",
            source="OPERATOR",
            effective_at=datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc),
            status=ObservationStatus.PENDING_REVIEW,
            trust_class=TrustClass.VERIFIED_OFFICIAL,
            recorded_by=test_user,
        )
        Investment.objects.create(
            user=test_user,
            portfolio=user_portfolio,
            instrument=inst,
            category='equity',
            asset_type='listed_stocks',
            display_name='Pending Stock Holding',
            currency='INR',
            initial_value=Decimal('500.00'),
            current_value=Decimal('0.00'),
        )

        # Overview response
        ov_res = api_client.get(reverse('dashboard_api_v1:dashboard-overview'))
        assert ov_res.status_code == status.HTTP_200_OK
        completeness = ov_res.data['data_completeness']
        assert completeness['total_active_holdings'] == 1
        assert completeness['awaiting_verification_holdings'] == 1
        assert completeness['missing_price_holdings'] == 0

        # Data-quality response
        dq_res = api_client.get(reverse('dashboard_api_v1:dashboard-data-quality'))
        assert dq_res.status_code == status.HTTP_200_OK
        dq_cats = dq_res.data['categories']
        assert dq_cats['awaiting_verification']['count'] == 1
        assert dq_cats['missing_price']['count'] == 0
        assert dq_res.data['overall_status'] == 'INCOMPLETE'

    def test_unverified_observation_classification(self, api_client, test_user, user_portfolio):
        api_client.force_authenticate(user=test_user)

        inst, _, series = create_instrument_with_series("UNVERIFIED_STK", source="COMMUNITY")
        PriceObservation.objects.create(
            instrument=inst,
            series=series,
            price_type="CLOSE",
            value=Decimal('250.00'),
            currency="INR",
            unit="UNITS",
            source="COMMUNITY",
            effective_at=datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc),
            status=ObservationStatus.PUBLISHED,
            trust_class=TrustClass.UNVERIFIED,  # Not trusted
            recorded_by=test_user,
        )

        Investment.objects.create(
            user=test_user,
            portfolio=user_portfolio,
            instrument=inst,
            category='equity',
            asset_type='listed_stocks',
            display_name='Unverified Holding',
            currency='INR',
            initial_value=Decimal('1000.00'),
            current_value=Decimal('0.00'),
        )

        ov_res = api_client.get(reverse('dashboard_api_v1:dashboard-overview'))
        completeness = ov_res.data['data_completeness']
        assert completeness['awaiting_verification_holdings'] == 1
        assert completeness['missing_price_holdings'] == 0

        dq_res = api_client.get(reverse('dashboard_api_v1:dashboard-data-quality'))
        assert dq_res.data['categories']['awaiting_verification']['count'] == 1

    def test_unsupported_and_synthetic_observations_increment_unsupported_count(
        self, api_client, test_user, user_portfolio
    ):
        api_client.force_authenticate(user=test_user)

        # Synthetic observation
        inst, _, series = create_instrument_with_series("SYNTH_STK", source="DEMO_FEED")
        PriceObservation.objects.create(
            instrument=inst,
            series=series,
            price_type="CLOSE",
            value=Decimal('120.00'),
            currency="INR",
            unit="UNITS",
            source="DEMO_FEED",
            effective_at=datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc),
            status=ObservationStatus.PUBLISHED,
            trust_class=TrustClass.SYNTHETIC,
            is_synthetic=True,
            recorded_by=test_user,
        )

        Investment.objects.create(
            user=test_user,
            portfolio=user_portfolio,
            instrument=inst,
            category='equity',
            asset_type='listed_stocks',
            display_name='Synthetic Stock Holding',
            currency='INR',
            initial_value=Decimal('1000.00'),
            current_value=Decimal('0.00'),
        )

        ov_res = api_client.get(reverse('dashboard_api_v1:dashboard-overview'))
        completeness = ov_res.data['data_completeness']
        assert completeness['unsupported_holdings'] == 1
        assert completeness['missing_price_holdings'] == 0

        dq_res = api_client.get(reverse('dashboard_api_v1:dashboard-data-quality'))
        assert dq_res.data['categories']['unsupported']['count'] == 1

    def test_stale_and_available_observations(self, api_client, test_user, user_portfolio):
        api_client.force_authenticate(user=test_user)

        # 1. Available/Verified
        inst_ok, _, series_ok = create_instrument_with_series("OK_CORP", source="NSE")
        PriceObservation.objects.create(
            instrument=inst_ok,
            series=series_ok,
            price_type="CLOSE",
            value=Decimal('500.00'),
            currency="INR",
            unit="UNITS",
            source="NSE",
            effective_at=datetime.now(timezone.utc),
            status=ObservationStatus.PUBLISHED,
            trust_class=TrustClass.VERIFIED_OFFICIAL,
            recorded_by=test_user,
        )
        Investment.objects.create(
            user=test_user,
            portfolio=user_portfolio,
            instrument=inst_ok,
            category='equity',
            asset_type='listed_stocks',
            display_name='OK Corp Holding',
            currency='INR',
            initial_value=Decimal('1000.00'),
            current_value=Decimal('1200.00'),
        )

        # 2. Stale
        inst_stale, _, series_stale = create_instrument_with_series("OLD_CORP", source="NSE")
        PriceObservation.objects.create(
            instrument=inst_stale,
            series=series_stale,
            price_type="CLOSE",
            value=Decimal('80.00'),
            currency="INR",
            unit="UNITS",
            source="NSE",
            effective_at=datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
            status=ObservationStatus.PUBLISHED,
            trust_class=TrustClass.VERIFIED_OFFICIAL,
            recorded_by=test_user,
        )
        Investment.objects.create(
            user=test_user,
            portfolio=user_portfolio,
            instrument=inst_stale,
            category='equity',
            asset_type='listed_stocks',
            display_name='Old Corp Holding',
            currency='INR',
            initial_value=Decimal('1000.00'),
            current_value=Decimal('800.00'),
        )

        ov_res = api_client.get(reverse('dashboard_api_v1:dashboard-overview'))
        completeness = ov_res.data['data_completeness']
        assert completeness['total_active_holdings'] == 2
        assert completeness['stale_holdings'] == 1

        dq_res = api_client.get(reverse('dashboard_api_v1:dashboard-data-quality'))
        assert dq_res.data['categories']['valued']['count'] == 1
        assert dq_res.data['categories']['stale']['count'] == 1

    def test_classification_invariants_mutual_exclusivity_and_scoping(
        self, api_client, test_user, other_user, user_portfolio, second_portfolio
    ):
        api_client.force_authenticate(user=test_user)

        # Active holding in portfolio 1
        inst1, _, _ = create_instrument_with_series("SCOPED_1")
        Investment.objects.create(
            user=test_user,
            portfolio=user_portfolio,
            instrument=inst1,
            category='equity',
            asset_type='listed_stocks',
            display_name='P1 Stock',
            currency='INR',
            initial_value=Decimal('100.00'),
            current_value=Decimal('0.00'),
        )

        # Active holding in portfolio 2
        inst2, _, _ = create_instrument_with_series("SCOPED_2")
        Investment.objects.create(
            user=test_user,
            portfolio=second_portfolio,
            instrument=inst2,
            category='equity',
            asset_type='listed_stocks',
            display_name='P2 Stock',
            currency='INR',
            initial_value=Decimal('200.00'),
            current_value=Decimal('0.00'),
        )

        # Inactive investment (must be excluded from counts)
        Investment.objects.create(
            user=test_user,
            portfolio=user_portfolio,
            instrument=None,
            category='cash',
            asset_type='bank_deposits',
            display_name='Closed Deposit',
            currency='INR',
            initial_value=Decimal('500.00'),
            current_value=Decimal('0.00'),
            is_active=False,
        )

        # Holding belonging to other user
        other_port = Portfolio.objects.create(user=other_user, name='Other Port')
        Investment.objects.create(
            user=other_user,
            portfolio=other_port,
            instrument=None,
            category='cash',
            asset_type='bank_deposits',
            display_name='Other User Holding',
            currency='INR',
            initial_value=Decimal('5000.00'),
            current_value=Decimal('5000.00'),
        )

        # 1. Combined overview
        res_combined = api_client.get(reverse('dashboard_api_v1:dashboard-overview'))
        comp_comb = res_combined.data['data_completeness']
        assert comp_comb['total_active_holdings'] == 2

        # Invariant: sum of mutually exclusive counts does not exceed total active
        sum_counts = (
            comp_comb['stale_holdings']
            + comp_comb['missing_price_holdings']
            + comp_comb['awaiting_verification_holdings']
            + comp_comb['unsupported_holdings']
        )
        assert sum_counts <= comp_comb['total_active_holdings']

        # 2. Portfolio-scoped overview
        res_scoped = api_client.get(f"{reverse('dashboard_api_v1:dashboard-overview')}?portfolio_id={user_portfolio.id}")
        comp_scoped = res_scoped.data['data_completeness']
        assert comp_scoped['total_active_holdings'] == 1
        assert comp_scoped['missing_price_holdings'] == 1

        # 3. Data quality scoped
        res_dq_scoped = api_client.get(f"{reverse('dashboard_api_v1:dashboard-data-quality')}?portfolio_id={user_portfolio.id}")
        assert res_dq_scoped.data['total_active_holdings'] == 1
        assert res_dq_scoped.data['categories']['missing_price']['count'] == 1
