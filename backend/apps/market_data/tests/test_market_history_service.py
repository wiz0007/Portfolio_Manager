from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from apps.market_data.models.coverage import InstrumentCoverage, PriceType, QuotationUnit
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.services.history_service import MarketHistoryService

User = get_user_model()


@pytest.fixture
def history_user(db):
    return User.objects.create_user(
        email='history_user@example.com',
        password='ValidPassword123!',
        full_name='History User',
        email_verified_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def history_instrument(db):
    inst = Instrument.objects.create(
        symbol='WIPRO',
        name='Wipro Limited',
        asset_class=AssetClass.EQUITY,
        exchange='NSE',
        currency='INR',
        isin='INE075A01022',
        is_active=True,
    )
    InstrumentCoverage.objects.create(
        instrument=inst,
        freshness_hours=24,
        price_type=PriceType.LTP,
        unit=QuotationUnit.UNITS,
    )
    return inst


@pytest.mark.django_db
class TestMarketHistoryServiceAndEndpoints:
    """Verifies chronological timeseries, range bounds, and market-data sub-endpoints."""

    def test_chronological_ordering_and_filtering(self, history_user, history_instrument):
        base_dt = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)
        # Create observations out of order
        PriceObservation.objects.create(
            instrument=history_instrument,
            value=Decimal('450.0000'),
            effective_at=base_dt + timedelta(days=2),
            status=ObservationStatus.PUBLISHED,
            recorded_by=history_user,
        )
        PriceObservation.objects.create(
            instrument=history_instrument,
            value=Decimal('440.0000'),
            effective_at=base_dt,
            status=ObservationStatus.PUBLISHED,
            recorded_by=history_user,
        )
        PriceObservation.objects.create(
            instrument=history_instrument,
            value=Decimal('445.0000'),
            effective_at=base_dt + timedelta(days=1),
            status=ObservationStatus.PUBLISHED,
            recorded_by=history_user,
        )
        # Create a draft observation that should be EXCLUDED
        PriceObservation.objects.create(
            instrument=history_instrument,
            value=Decimal('999.0000'),
            effective_at=base_dt + timedelta(days=1),
            status=ObservationStatus.DRAFT,
            recorded_by=history_user,
        )

        res = MarketHistoryService.get_history(
            instrument=history_instrument,
            start_date=(base_dt).date(),
            end_date=(base_dt + timedelta(days=5)).date(),
        )

        assert res.supported is True
        assert len(res.points) == 3
        # Strict chronological order check
        assert res.points[0].price == Decimal('440.0000')
        assert res.points[1].price == Decimal('445.0000')
        assert res.points[2].price == Decimal('450.0000')
        # Draft observation excluded
        assert Decimal('999.0000') not in [p.price for p in res.points]

    def test_invalid_date_range_raises_validation_error(self, history_instrument):
        today = date.today()
        with pytest.raises(ValidationError):
            MarketHistoryService.get_history(
                instrument=history_instrument,
                start_date=today,
                end_date=today - timedelta(days=5),
            )

    def test_instrument_market_data_latest_endpoint(self, history_user, history_instrument):
        now = datetime.now(timezone.utc)
        PriceObservation.objects.create(
            instrument=history_instrument,
            value=Decimal('520.0000'),
            effective_at=now,
            status=ObservationStatus.PUBLISHED,
            source='MANUAL_VERIFIED',
            recorded_by=history_user,
        )

        client = APIClient()
        client.force_authenticate(user=history_user)

        res = client.get(f'/api/v1/instruments/{history_instrument.id}/market-data/latest/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['instrument_id'] == str(history_instrument.id)
        assert res.data['price'] == '520.0000'
        assert res.data['status'] == 'AVAILABLE'
        assert res.data['source'] == 'MANUAL_VERIFIED'

    def test_instrument_market_data_history_endpoint(self, history_user, history_instrument):
        base_dt = datetime.now(timezone.utc) - timedelta(days=5)
        PriceObservation.objects.create(
            instrument=history_instrument,
            value=Decimal('500.0000'),
            effective_at=base_dt,
            status=ObservationStatus.PUBLISHED,
            recorded_by=history_user,
        )

        client = APIClient()
        client.force_authenticate(user=history_user)

        res = client.get(f'/api/v1/instruments/{history_instrument.id}/market-data/history/?period=1W')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['supported'] is True
        assert len(res.data['points']) >= 1

    def test_instrument_market_data_status_endpoint(self, history_user, history_instrument):
        client = APIClient()
        client.force_authenticate(user=history_user)

        res = client.get(f'/api/v1/instruments/{history_instrument.id}/market-data/status/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['coverage_configured'] is True
        assert res.data['freshness_hours'] == 24
