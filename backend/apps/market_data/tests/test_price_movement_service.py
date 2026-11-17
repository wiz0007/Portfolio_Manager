from datetime import datetime, timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.market_data.models.coverage import PriceType, QuotationUnit
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.services.movement_service import MovementStatus, PriceMovementService

User = get_user_model()


@pytest.fixture
def operator_user(db):
    return User.objects.create_user(
        email='operator@example.com',
        password='ValidPassword123!',
        full_name='Price Operator',
        email_verified_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def movement_instrument(db):
    return Instrument.objects.create(
        symbol='TCS',
        name='Tata Consultancy Services',
        asset_class=AssetClass.EQUITY,
        exchange='NSE',
        currency='INR',
        isin='INE467B01029',
        is_active=True,
    )


@pytest.mark.django_db
class TestPriceMovementService:
    """Verifies decimal-safe arithmetic, baseline checks, and unit/currency safety."""

    def test_positive_price_movement_calculation(self, operator_user, movement_instrument):
        t1 = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 11, 16, 10, 0, tzinfo=timezone.utc)

        # Prior day observation: 3500.00
        PriceObservation.objects.create(
            instrument=movement_instrument,
            value=Decimal('3500.0000'),
            currency='INR',
            unit=QuotationUnit.UNITS,
            price_type=PriceType.LTP,
            effective_at=t1,
            status=ObservationStatus.PUBLISHED,
            recorded_by=operator_user,
        )

        # Current price: 3850.00 (+350.00, +10.0000%)
        movement = PriceMovementService.calculate_movement(
            instrument=movement_instrument,
            current_price=Decimal('3850.0000'),
            current_dt=t2,
            currency='INR',
            unit=QuotationUnit.UNITS,
        )

        assert movement.status == MovementStatus.CALCULATED
        assert movement.change_amount == Decimal('350.0000')
        assert movement.change_percent == Decimal('10.0000')
        assert movement.previous_price == Decimal('3500.0000')
        assert movement.previous_effective_at == t1

    def test_negative_price_movement_calculation(self, operator_user, movement_instrument):
        t1 = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 11, 16, 10, 0, tzinfo=timezone.utc)

        PriceObservation.objects.create(
            instrument=movement_instrument,
            value=Decimal('4000.0000'),
            currency='INR',
            unit=QuotationUnit.UNITS,
            price_type=PriceType.LTP,
            effective_at=t1,
            status=ObservationStatus.PUBLISHED,
            recorded_by=operator_user,
        )

        # Current price: 3800.00 (-200.00, -5.0000%)
        movement = PriceMovementService.calculate_movement(
            instrument=movement_instrument,
            current_price=Decimal('3800.0000'),
            current_dt=t2,
            currency='INR',
            unit=QuotationUnit.UNITS,
        )

        assert movement.status == MovementStatus.CALCULATED
        assert movement.change_amount == Decimal('-200.0000')
        assert movement.change_percent == Decimal('-5.0000')
        assert movement.previous_price == Decimal('4000.0000')

    def test_zero_base_price_handled_safely(self, operator_user, movement_instrument):
        t1 = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 11, 16, 10, 0, tzinfo=timezone.utc)

        PriceObservation.objects.create(
            instrument=movement_instrument,
            value=Decimal('0.0000'),
            currency='INR',
            unit=QuotationUnit.UNITS,
            price_type=PriceType.LTP,
            effective_at=t1,
            status=ObservationStatus.PUBLISHED,
            recorded_by=operator_user,
        )

        movement = PriceMovementService.calculate_movement(
            instrument=movement_instrument,
            current_price=Decimal('100.0000'),
            current_dt=t2,
        )

        assert movement.status == MovementStatus.ZERO_BASE
        assert movement.change_amount is None
        assert movement.change_percent is None

    def test_currency_mismatch_rejected(self, operator_user, movement_instrument):
        t1 = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 11, 16, 10, 0, tzinfo=timezone.utc)

        PriceObservation.objects.create(
            instrument=movement_instrument,
            value=Decimal('100.0000'),
            currency='USD',
            unit=QuotationUnit.UNITS,
            price_type=PriceType.LTP,
            effective_at=t1,
            status=ObservationStatus.PUBLISHED,
            recorded_by=operator_user,
        )

        movement = PriceMovementService.calculate_movement(
            instrument=movement_instrument,
            current_price=Decimal('110.0000'),
            current_dt=t2,
            currency='INR',
        )

        assert movement.status == MovementStatus.INCOMPATIBLE
        assert movement.change_amount is None
        assert movement.change_percent is None

    def test_missing_previous_observation_returns_unavailable(self, movement_instrument):
        t2 = datetime(2026, 11, 16, 10, 0, tzinfo=timezone.utc)

        movement = PriceMovementService.calculate_movement(
            instrument=movement_instrument,
            current_price=Decimal('1000.0000'),
            current_dt=t2,
        )

        assert movement.status == MovementStatus.UNAVAILABLE
        assert movement.change_amount is None
        assert movement.change_percent is None
