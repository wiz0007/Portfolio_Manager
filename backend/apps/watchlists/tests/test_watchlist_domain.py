from datetime import datetime
from datetime import timezone as dt_timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models import Investment
from apps.assets.models.details import EquityDetail
from apps.market_data.models.instrument import AssetClass, Instrument, InstrumentStatus
from apps.portfolios.models import Portfolio
from apps.watchlists.models import WatchlistItem
from apps.watchlists.services.watchlist_service import WatchlistService

User = get_user_model()


@pytest.fixture
def test_users(db):
    now = datetime.now(dt_timezone.utc)
    user_a = User.objects.create_user(
        email='user_a@example.com',
        password='ValidPassword123!',
        full_name='User A',
        email_verified_at=now,
    )
    user_b = User.objects.create_user(
        email='user_b@example.com',
        password='ValidPassword123!',
        full_name='User B',
        email_verified_at=now,
    )
    return user_a, user_b


@pytest.fixture
def sample_instruments(db):
    inst1 = Instrument.objects.create(
        symbol='INFY',
        name='Infosys Limited',
        asset_class=AssetClass.EQUITY,
        exchange='NSE',
        currency='INR',
        isin='INE009A01021',
        is_active=True,
    )
    inst2 = Instrument.objects.create(
        symbol='HDFCBANK',
        name='HDFC Bank Limited',
        asset_class=AssetClass.EQUITY,
        exchange='NSE',
        currency='INR',
        isin='INE040A01034',
        is_active=True,
    )
    inactive_inst = Instrument.objects.create(
        symbol='DELISTED_CO',
        name='Delisted Corp',
        asset_class=AssetClass.EQUITY,
        exchange='NSE',
        currency='INR',
        status=InstrumentStatus.DELISTED,
        is_active=False,
    )
    return inst1, inst2, inactive_inst


@pytest.mark.django_db
class TestWatchlistModelAndConstraints:
    """Verifies model constraints, cascade safety, and investment independence."""

    def test_create_watchlist_item_success(self, test_users, sample_instruments):
        user_a, _ = test_users
        inst1, _, _ = sample_instruments

        item = WatchlistItem.objects.create(
            user=user_a,
            instrument=inst1,
            notes='Monitoring for Q3 breakout',
            target_price=Decimal('1550.0000'),
        )
        assert item.id is not None
        assert item.user == user_a
        assert item.instrument == inst1
        assert item.notes == 'Monitoring for Q3 breakout'
        assert item.target_price == Decimal('1550.0000')

    def test_duplicate_user_instrument_constraint_rejected(self, test_users, sample_instruments):
        user_a, _ = test_users
        inst1, _, _ = sample_instruments

        WatchlistItem.objects.create(user=user_a, instrument=inst1)
        with pytest.raises((IntegrityError, ValidationError)):
            WatchlistItem.objects.create(user=user_a, instrument=inst1)

    def test_different_users_can_watch_same_instrument(self, test_users, sample_instruments):
        user_a, user_b = test_users
        inst1, _, _ = sample_instruments

        item_a = WatchlistItem.objects.create(user=user_a, instrument=inst1)
        item_b = WatchlistItem.objects.create(user=user_b, instrument=inst1)

        assert item_a.id != item_b.id
        assert WatchlistItem.objects.filter(instrument=inst1).count() == 2

    def test_target_price_must_be_strictly_positive(self, test_users, sample_instruments):
        user_a, _ = test_users
        inst1, _, _ = sample_instruments

        item = WatchlistItem(user=user_a, instrument=inst1, target_price=Decimal('-10.00'))
        with pytest.raises(ValidationError):
            item.clean()

    def test_remove_item_preserves_canonical_instrument(self, test_users, sample_instruments):
        user_a, _ = test_users
        inst1, _, _ = sample_instruments

        item = WatchlistItem.objects.create(user=user_a, instrument=inst1)
        item_id = item.id

        # Delete watchlist item
        item.delete()

        assert not WatchlistItem.objects.filter(id=item_id).exists()
        # Canonical instrument remains intact
        assert Instrument.objects.filter(id=inst1.id).exists()

    def test_remove_item_preserves_user_investments_and_transactions(self, test_users, sample_instruments):
        user_a, _ = test_users
        inst1, _, _ = sample_instruments

        portfolio = Portfolio.objects.create(user=user_a, name='Main Portfolio')
        investment = Investment.objects.create(
            portfolio=portfolio,
            user=user_a,
            instrument=inst1,
            category='equity',
            asset_type='listed_stocks',
            display_name='My INFY Holding',
            initial_value=Decimal('50000.00'),
            current_value=Decimal('55000.00'),
        )
        EquityDetail.objects.create(
            investment=investment,
            company_name='Infosys Limited',
            symbol='INFY',
            exchange='NSE',
            quantity=Decimal('35.0000'),
            average_buy_price=Decimal('1428.5714'),
            purchase_date=datetime.now(dt_timezone.utc).date(),
        )

        item = WatchlistItem.objects.create(user=user_a, instrument=inst1)

        # Deleting watchlist item must not impact investment
        item.delete()

        assert Investment.objects.filter(id=investment.id).exists()
        reloaded_inv = Investment.objects.get(id=investment.id)
        assert reloaded_inv.initial_value == Decimal('50000.00')
        assert reloaded_inv.current_value == Decimal('55000.00')

    def test_inactive_instrument_rejected_by_service(self, test_users, sample_instruments):
        user_a, _ = test_users
        _, _, inactive_inst = sample_instruments

        with pytest.raises(ValidationError):
            WatchlistService.add_item(user=user_a, instrument_id=inactive_inst.id)


@pytest.mark.django_db
class TestWatchlistAPILifecycle:
    """Verifies API contracts, authentication, authorization, and error responses."""

    def test_unauthenticated_requests_rejected(self, sample_instruments):
        inst1, _, _ = sample_instruments
        client = APIClient()

        res_list = client.get('/api/v1/watchlist/')
        assert res_list.status_code == status.HTTP_401_UNAUTHORIZED

        res_post = client.post('/api/v1/watchlist/', {'instrument_id': str(inst1.id)})
        assert res_post.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_to_watchlist_lifecycle(self, test_users, sample_instruments):
        user_a, _ = test_users
        inst1, _, _ = sample_instruments

        client = APIClient()
        client.force_authenticate(user=user_a)

        # 1. Add item
        payload = {
            'instrument_id': str(inst1.id),
            'notes': 'Accumulate below 1500',
            'target_price': '1450.0000',
        }
        res_add = client.post('/api/v1/watchlist/', payload)
        assert res_add.status_code == status.HTTP_201_CREATED
        data = res_add.data
        item_id = data['id']
        assert data['instrument']['symbol'] == 'INFY'
        assert data['notes'] == 'Accumulate below 1500'
        assert data['target_price'] == '1450.0000'
        assert 'market_data' in data

        # 2. List items
        res_list = client.get('/api/v1/watchlist/')
        assert res_list.status_code == status.HTTP_200_OK
        assert len(res_list.data) == 1
        assert res_list.data[0]['id'] == item_id

        # 3. Retrieve single item
        res_get = client.get(f'/api/v1/watchlist/{item_id}/')
        assert res_get.status_code == status.HTTP_200_OK
        assert res_get.data['id'] == item_id

        # 4. Duplicate creation rejected
        res_dup = client.post('/api/v1/watchlist/', payload)
        assert res_dup.status_code == status.HTTP_400_BAD_REQUEST

        # 5. Delete item
        res_del = client.delete(f'/api/v1/watchlist/{item_id}/')
        assert res_del.status_code == status.HTTP_204_NO_CONTENT

        # 6. Verify item is gone
        res_after = client.get(f'/api/v1/watchlist/{item_id}/')
        assert res_after.status_code == status.HTTP_404_NOT_FOUND

    def test_cross_user_isolation_returns_404(self, test_users, sample_instruments):
        user_a, user_b = test_users
        inst1, _, _ = sample_instruments

        # User A creates item
        item_a = WatchlistItem.objects.create(user=user_a, instrument=inst1)

        # User B tries to access or delete User A's item
        client_b = APIClient()
        client_b.force_authenticate(user=user_b)

        res_get = client_b.get(f'/api/v1/watchlist/{item_a.id}/')
        assert res_get.status_code == status.HTTP_404_NOT_FOUND

        res_del = client_b.delete(f'/api/v1/watchlist/{item_a.id}/')
        assert res_del.status_code == status.HTTP_404_NOT_FOUND

        # User A's item remains intact
        assert WatchlistItem.objects.filter(id=item_a.id).exists()
