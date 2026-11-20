import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.market_data.adapters import (
    CommodityAdapter,
    EquityIndexAdapter,
    MutualFundAdapter,
    NormalizedObservation,
)
from apps.market_data.models.instrument import AssetClass, Instrument, InstrumentStatus
from apps.market_data.models.market_data_point import MarketDataPoint
from apps.market_data.models.observation import (
    ObservationStatus,
    PriceObservation,
    PriceType,
    TrustClass,
)
from apps.market_data.services.backfill_service import HistoricalBackfillService
from apps.market_data.services.history_service import MarketHistoryService


@pytest.fixture
def auth_client(django_user_model):
    user = django_user_model.objects.create_user(
        email='operator@portfoliomanager.local',
        password='OperatorPass123!',
        is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def sample_equity(db):
    return Instrument.objects.create(
        id=uuid.uuid4(),
        symbol='TEST_INFY',
        name='Infosys Limited Test',
        asset_class=AssetClass.EQUITY,
        product_type='EQUITY',
        exchange='NSE',
        isin='INE009A01021',
        currency='INR',
        status=InstrumentStatus.ACTIVE,
    )


@pytest.fixture
def sample_index(db):
    return Instrument.objects.create(
        id=uuid.uuid4(),
        symbol='NIFTY 50',
        name='NIFTY 50 Index',
        asset_class=AssetClass.INDEX,
        product_type='INDEX',
        exchange='NSE',
        currency='INR',
        status=InstrumentStatus.ACTIVE,
    )


@pytest.fixture
def sample_mutual_fund(db):
    return Instrument.objects.create(
        id=uuid.uuid4(),
        symbol='MF_122639',
        name='Parag Parikh Flexi Cap Fund Test',
        asset_class=AssetClass.MUTUAL_FUND,
        product_type='MUTUAL_FUND',
        exchange='AMFI',
        scheme_code='122639',
        currency='INR',
        status=InstrumentStatus.ACTIVE,
    )


@pytest.mark.django_db
class TestHistoricalDataTrustAndIntegrity:
    """Tests guaranteeing that verified and synthetic data never mix and series are clean."""

    def test_trust_class_separation_no_synthetic_mixing(self, sample_equity, django_user_model):
        operator = django_user_model.objects.create_user(email='op1@pm.local', password='password123')
        today = date(2026, 11, 19)

        # 1. Create verified observations
        for i in range(5):
            dt = datetime.combine(today - timedelta(days=i), datetime.min.time().replace(hour=10), tzinfo=timezone.utc)
            PriceObservation.objects.create(
                instrument=sample_equity,
                effective_at=dt,
                price_type=PriceType.LTP,
                value=Decimal('1500.0000') + Decimal(i * 10),
                status=ObservationStatus.PUBLISHED,
                trust_class=TrustClass.VERIFIED_OFFICIAL,
                source='NSE_OFFICIAL',
                is_synthetic=False,
                recorded_by=operator,
                published_by=operator,
            )

        # 2. Create dirty synthetic MarketDataPoints (simulating demo provider pollution)
        for i in range(10):
            dt = datetime.combine(today - timedelta(days=i + 5), datetime.min.time(), tzinfo=timezone.utc)
            MarketDataPoint.objects.create(
                instrument=sample_equity,
                timestamp=dt,
                interval='1D',
                provider='DEMO',
                price=Decimal('150.0000'),  # Distorted synthetic price
                is_synthetic=True,
            )

        # 3. Retrieve history via MarketHistoryService
        res = MarketHistoryService.get_history(sample_equity, period='1M')

        # Assert: Exactly the 5 verified observations returned, 0 synthetic points
        assert res.supported is True
        assert len(res.points) == 5
        assert all(p.is_synthetic is False for p in res.points)
        assert all(p.trust_class == TrustClass.VERIFIED_OFFICIAL for p in res.points)
        assert all(p.price >= Decimal('1500.0000') for p in res.points)

    def test_historical_deduplication_one_point_per_date(self, sample_equity, django_user_model):
        operator = django_user_model.objects.create_user(email='op2@pm.local', password='password123')
        trading_day = date(2026, 11, 18)

        # Two observations on the same trading day (e.g. initial and revised close)
        dt1 = datetime.combine(trading_day, datetime.min.time().replace(hour=10), tzinfo=timezone.utc)
        dt2 = datetime.combine(trading_day, datetime.min.time().replace(hour=11), tzinfo=timezone.utc)

        PriceObservation.objects.create(
            instrument=sample_equity,
            effective_at=dt1,
            price_type=PriceType.LTP,
            value=Decimal('1510.0000'),
            status=ObservationStatus.PUBLISHED,
            trust_class=TrustClass.VERIFIED_OFFICIAL,
            source='NSE_OFFICIAL',
            recorded_by=operator,
            published_by=operator,
        )
        PriceObservation.objects.create(
            instrument=sample_equity,
            effective_at=dt2,
            price_type=PriceType.LTP,
            value=Decimal('1515.0000'),
            status=ObservationStatus.PUBLISHED,
            trust_class=TrustClass.VERIFIED_OFFICIAL,
            source='NSE_REVISED',
            recorded_by=operator,
            published_by=operator,
        )

        res = MarketHistoryService.get_history(sample_equity, period='1W')
        # Exactly 1 point for 2026-11-18, latest value wins
        dates = [p.date for p in res.points]
        assert dates.count('2026-11-18') == 1
        assert res.points[-1].price == Decimal('1515.0000')


@pytest.mark.django_db
class TestHistoricalAdapters:
    """Tests verifying adapter support and mapping logic."""

    def test_adapter_support_mapping(self, sample_equity, sample_index, sample_mutual_fund):
        eq_adapter = EquityIndexAdapter()
        mf_adapter = MutualFundAdapter()
        comm_adapter = CommodityAdapter()

        assert eq_adapter.supports(sample_equity) is True
        assert eq_adapter.supports(sample_index) is True
        assert eq_adapter.supports(sample_mutual_fund) is False

        assert mf_adapter.supports(sample_mutual_fund) is True
        assert mf_adapter.supports(sample_equity) is False

        gold_inst = Instrument(symbol='GOLD_24K_1G', asset_class=AssetClass.COMMODITY)
        assert comm_adapter.supports(gold_inst) is True

    def test_backfill_service_validation_rules(self, sample_equity):
        service = HistoricalBackfillService()
        valid_obs = NormalizedObservation(
            instrument_id=str(sample_equity.id),
            effective_at=datetime(2026, 11, 18, 10, 0, tzinfo=timezone.utc),
            price_type=PriceType.LTP,
            value=Decimal('100.50'),
            open_price=Decimal('100.00'),
            high_price=Decimal('102.00'),
            low_price=Decimal('99.50'),
        )
        assert service.validate_observation(valid_obs) is True

        # Invalid: High < Low
        invalid_ohlc = NormalizedObservation(
            instrument_id=str(sample_equity.id),
            effective_at=datetime(2026, 11, 18, 10, 0, tzinfo=timezone.utc),
            price_type=PriceType.LTP,
            value=Decimal('100.50'),
            high_price=Decimal('95.00'),
            low_price=Decimal('99.50'),
        )
        assert service.validate_observation(invalid_ohlc) is False

        # Invalid: Negative price
        negative_price = NormalizedObservation(
            instrument_id=str(sample_equity.id),
            effective_at=datetime(2026, 11, 18, 10, 0, tzinfo=timezone.utc),
            price_type=PriceType.LTP,
            value=Decimal('-50.00'),
        )
        assert service.validate_observation(negative_price) is False


@pytest.mark.django_db
class TestOperationsHistoricalCoverageAPI:
    """Tests verifying the operator-facing historical coverage views."""

    def test_historical_coverage_report_view(self, auth_client, sample_equity):
        client, _user = auth_client
        url = '/api/v1/market-data/operations/history-coverage/'
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'universe' in data
        assert 'coverage' in data
        assert 'storage' in data
        assert 'total_instruments' in data['universe']
        assert 'neon_plan_limit' in data['storage']

    def test_historical_backfill_trigger_view_not_found(self, auth_client):
        client, _user = auth_client
        url = '/api/v1/market-data/operations/history-backfill/'
        response = client.post(url, {'symbol': 'NON_EXISTENT_SYMBOL_999'})
        assert response.status_code == status.HTTP_404_NOT_FOUND
