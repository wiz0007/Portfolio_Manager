from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models.investment import AssetCategory, Investment
from apps.dashboard.services.dashboard_service import DashboardService
from apps.market_data.models.coverage import InstrumentCoverage
from apps.market_data.models.import_batch import ImportBatchStatus, PriceImportBatch
from apps.market_data.models.instrument import Instrument, InstrumentStatus
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.services.history_service import MarketHistoryService
from apps.market_data.services.import_service import PriceImportService, clean_cell
from apps.market_data.services.price_resolver import PriceResolver, ResolutionStatus
from apps.portfolios.models import Portfolio
from apps.watchlists.services.watchlist_service import WatchlistService

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def users(db):
    user = User.objects.create_user(
        email='stabilization_user@example.com',
        password='StrongPassword123!',
        full_name='Stabilization User',
        is_active=True,
    )
    operator = User.objects.create_user(
        email='stabilization_operator@example.com',
        password='StrongPassword123!',
        full_name='Stabilization Operator',
        is_active=True,
    )
    publisher = User.objects.create_user(
        email='stabilization_publisher@example.com',
        password='StrongPassword123!',
        full_name='Stabilization Publisher',
        is_active=True,
    )
    op_group, _ = Group.objects.get_or_create(name='MarketDataOperator')
    pub_group, _ = Group.objects.get_or_create(name='MarketDataPublisher')
    operator.groups.add(op_group)
    publisher.groups.add(pub_group)

    return {'user': user, 'operator': operator, 'publisher': publisher}


@pytest.fixture
def canonical_instruments(db):
    inst1 = Instrument.objects.create(
        symbol='INFY',
        name='Infosys Limited',
        asset_class='EQUITY',
        exchange='NSE',
        currency='INR',
        isin='INE009A01021',
        status=InstrumentStatus.ACTIVE,
    )
    InstrumentCoverage.objects.create(
        instrument=inst1,
        price_type='LTP',
        currency='INR',
        cadence='EVERY_TRADING_DAY',
        freshness_hours=24,
    )

    inst2 = Instrument.objects.create(
        symbol='TCS',
        name='Tata Consultancy Services',
        asset_class='EQUITY',
        exchange='NSE',
        currency='INR',
        isin='INE467B01029',
        status=InstrumentStatus.ACTIVE,
    )
    InstrumentCoverage.objects.create(
        instrument=inst2,
        price_type='LTP',
        currency='INR',
        cadence='EVERY_TRADING_DAY',
        freshness_hours=24,
    )

    return {'infy': inst1, 'tcs': inst2}


@pytest.mark.django_db
class TestCanonicalPriceResolverContract:
    def test_resolver_data_contract_fields_and_age(self, canonical_instruments, users):
        inst = canonical_instruments['infy']
        pub = users['publisher']
        now = datetime.now(timezone.utc)
        effective_dt = now - timedelta(hours=2)

        PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('1850.50'),
            currency='INR',
            unit='UNITS',
            effective_at=effective_dt,
            source='NSE_CLOSING',
            status=ObservationStatus.PUBLISHED,
            recorded_by=pub,
            published_by=pub,
            published_at=effective_dt + timedelta(minutes=10),
        )

        resolved = PriceResolver.resolve_price(inst)
        assert resolved.status == ResolutionStatus.AVAILABLE
        assert resolved.price == Decimal('1850.50')
        assert resolved.price_type == 'LTP'
        assert resolved.published_at is not None
        assert resolved.age_seconds is not None
        assert resolved.age_seconds > 0

    def test_resolver_excludes_superseded_observations(self, canonical_instruments, users):
        inst = canonical_instruments['infy']
        pub = users['publisher']
        t1 = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 11, 11, 10, 0, tzinfo=timezone.utc)

        # Original erroneous observation
        original = PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('9999.00'),  # Wrong price
            currency='INR',
            effective_at=t2,
            source='MANUAL_ENTRY',
            status=ObservationStatus.PUBLISHED,
            recorded_by=pub,
            published_by=pub,
            published_at=t2,
        )

        # Correction superseding the original
        PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('1820.00'),  # Corrected price
            currency='INR',
            effective_at=t2,
            source='MANUAL_CORRECTION',
            status=ObservationStatus.PUBLISHED,
            recorded_by=pub,
            published_by=pub,
            published_at=t2 + timedelta(minutes=30),
            correction_of=original,
            correction_reason='Typo in original price',
        )

        # Older valid observation
        PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('1800.00'),
            currency='INR',
            effective_at=t1,
            source='NSE_CLOSING',
            status=ObservationStatus.PUBLISHED,
            recorded_by=pub,
            published_by=pub,
            published_at=t1,
        )

        # Resolver should return the correction, never the superseded original
        resolved = PriceResolver.resolve_price(inst, as_of=t2 + timedelta(hours=1))
        assert resolved.price == Decimal('1820.00')
        assert resolved.source == 'MANUAL_CORRECTION'

    def test_resolver_pending_review_returns_awaiting_verification(self, canonical_instruments, users):
        inst = canonical_instruments['tcs']
        op = users['operator']
        now = datetime.now(timezone.utc)

        PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('3500.00'),
            currency='INR',
            effective_at=now,
            source='OPERATOR_RESEARCH',
            status=ObservationStatus.PENDING_REVIEW,
            recorded_by=op,
        )

        resolved = PriceResolver.resolve_price(inst)
        assert resolved.status == ResolutionStatus.AWAITING_VERIFICATION
        assert resolved.price is None

    def test_resolver_missing_price_has_none_timestamps(self, canonical_instruments):
        inst = canonical_instruments['tcs']
        # No observations exist
        resolved = PriceResolver.resolve_price(inst)
        assert resolved.status == ResolutionStatus.MISSING
        assert resolved.price is None
        assert resolved.effective_at is None
        assert resolved.published_at is None
        assert resolved.age_seconds is None

    def test_resolver_resolve_prices_bulk(self, canonical_instruments, users):
        infy = canonical_instruments['infy']
        tcs = canonical_instruments['tcs']
        pub = users['publisher']
        now = datetime.now(timezone.utc)

        PriceObservation.objects.create(
            instrument=infy,
            price_type='LTP',
            value=Decimal('1850.00'),
            currency='INR',
            effective_at=now,
            source='NSE',
            status=ObservationStatus.PUBLISHED,
            recorded_by=pub,
            published_by=pub,
            published_at=now,
        )

        price_map = PriceResolver.resolve_prices_bulk([infy, tcs])
        assert len(price_map) == 2
        assert price_map[infy.id].status == ResolutionStatus.AVAILABLE
        assert price_map[infy.id].price == Decimal('1850.00')
        assert price_map[tcs.id].status == ResolutionStatus.MISSING


@pytest.mark.django_db
class TestPriceObservationSecurityAndLifecycle:
    def test_observation_put_patch_rejected_405(self, api_client, canonical_instruments, users):
        inst = canonical_instruments['infy']
        op = users['operator']
        now = datetime.now(timezone.utc)

        obs = PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('1800.00'),
            currency='INR',
            effective_at=now,
            source='TEST',
            status=ObservationStatus.DRAFT,
            recorded_by=op,
        )

        api_client.force_authenticate(user=op)
        put_resp = api_client.put(f'/api/v1/market-data/observations/{obs.id}/', {'value': '1900.00'})
        assert put_resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        patch_resp = api_client.patch(f'/api/v1/market-data/observations/{obs.id}/', {'value': '1900.00'})
        assert patch_resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_published_observation_delete_rejected_400(self, api_client, canonical_instruments, users):
        inst = canonical_instruments['infy']
        pub = users['publisher']
        now = datetime.now(timezone.utc)

        obs = PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('1800.00'),
            currency='INR',
            effective_at=now,
            source='TEST',
            status=ObservationStatus.PUBLISHED,
            recorded_by=pub,
            published_by=pub,
            published_at=now,
        )

        api_client.force_authenticate(user=pub)
        del_resp = api_client.delete(f'/api/v1/market-data/observations/{obs.id}/')
        assert del_resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_publisher_can_see_pending_and_publish(self, api_client, canonical_instruments, users):
        inst = canonical_instruments['infy']
        op = users['operator']
        pub = users['publisher']
        now = datetime.now(timezone.utc)

        obs = PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('1855.00'),
            currency='INR',
            effective_at=now,
            source='NSE',
            status=ObservationStatus.PENDING_REVIEW,
            recorded_by=op,
        )

        api_client.force_authenticate(user=pub)
        list_resp = api_client.get(f'/api/v1/market-data/observations/?instrument={inst.id}')
        assert list_resp.status_code == status.HTTP_200_OK
        obs_ids = (
            [o['id'] for o in list_resp.data]
            if isinstance(list_resp.data, list)
            else [o['id'] for o in list_resp.data.get('results', [])]
        )
        assert str(obs.id) in obs_ids

        publish_resp = api_client.post(f'/api/v1/market-data/observations/{obs.id}/publish/')
        assert publish_resp.status_code == status.HTTP_200_OK
        obs.refresh_from_db()
        assert obs.status == ObservationStatus.PUBLISHED
        assert obs.published_by == pub


@pytest.mark.django_db
class TestCSVImportIntegrity:
    def test_clean_cell_preserves_negative_numbers(self):
        assert clean_cell('-123.45') == '-123.45'
        assert clean_cell('+123.45') == '+123.45'
        assert clean_cell('=-123.45') == '-123.45'  # formula prefix stripped
        assert clean_cell('@SUM(A1)') == 'SUM(A1)'

    def test_server_side_import_batch_commit(self, canonical_instruments, users):
        inst = canonical_instruments['infy']
        op = users['operator']
        now_date = date.today().isoformat()

        csv_content = f"schema_version,instrument_id,value,currency,effective_at,source_id\n1.0,{inst.id},1890.50,INR,{now_date},MANUAL_CSV\n"
        preview = PriceImportService.preview_csv(op, csv_content, 'test.csv')

        assert preview['valid_count'] == 1
        assert 'batch_id' in preview
        batch_id = preview['batch_id']

        batch = PriceImportBatch.objects.get(id=batch_id)
        assert batch.status == ImportBatchStatus.PREVIEWED

        # Commit using server-side batch
        committed_batch = PriceImportService.commit_batch(op, batch_id)
        assert committed_batch.status == ImportBatchStatus.COMMITTED

        # Check PriceObservation was created
        obs = PriceObservation.objects.filter(instrument=inst, source='MANUAL_CSV').first()
        assert obs is not None
        assert obs.value == Decimal('1890.50')
        assert obs.status == ObservationStatus.DRAFT

        # Attempting to commit again must fail
        with pytest.raises(ValidationError):
            PriceImportService.commit_batch(op, batch_id)


@pytest.mark.django_db
class TestHistoricalPriceServiceStabilization:
    def test_history_all_period_resolves_earliest_date(self, canonical_instruments, users):
        inst = canonical_instruments['infy']
        pub = users['publisher']
        # Create an observation from 10 years ago (outside arbitrary 5-year window)
        earliest_dt = datetime.now(timezone.utc) - timedelta(days=365 * 10)
        recent_dt = datetime.now(timezone.utc) - timedelta(days=1)

        PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('500.00'),
            currency='INR',
            effective_at=earliest_dt,
            source='HISTORICAL',
            status=ObservationStatus.PUBLISHED,
            recorded_by=pub,
            published_by=pub,
            published_at=earliest_dt,
        )
        PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('1850.00'),
            currency='INR',
            effective_at=recent_dt,
            source='HISTORICAL',
            status=ObservationStatus.PUBLISHED,
            recorded_by=pub,
            published_by=pub,
            published_at=recent_dt,
        )

        res = MarketHistoryService.get_history(inst, period='ALL')
        assert res.supported is True
        assert len(res.points) == 2
        assert res.points[0].price == Decimal('500.00')
        assert res.start_date == earliest_dt.date().isoformat()
        assert res.points[0].price_type == 'LTP'
        assert res.points[0].published_at is not None

    def test_history_api_invalid_date_format_400(self, api_client, canonical_instruments, users):
        inst = canonical_instruments['infy']
        api_client.force_authenticate(user=users['user'])
        resp = api_client.get(f'/api/v1/instruments/{inst.id}/market-data/history/?from=invalid-date')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestWatchlistStabilization:
    def test_watchlist_concurrent_add_handled_gracefully(self, canonical_instruments, users):
        inst = canonical_instruments['infy']
        user = users['user']

        # First add succeeds
        item1 = WatchlistService.add_item(user, inst.id)
        assert item1 is not None

        # Second add raises clean ValidationError
        with pytest.raises(ValidationError):
            WatchlistService.add_item(user, inst.id)

    def test_watchlist_annotated_item_includes_published_at_and_age(self, canonical_instruments, users):
        inst = canonical_instruments['infy']
        user = users['user']
        pub = users['publisher']
        now = datetime.now(timezone.utc)

        PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('1850.00'),
            currency='INR',
            effective_at=now,
            source='NSE',
            status=ObservationStatus.PUBLISHED,
            recorded_by=pub,
            published_by=pub,
            published_at=now,
        )

        item = WatchlistService.add_item(user, inst.id, target_price=Decimal('2000.00'))
        data = WatchlistService.get_annotated_item_data(item)

        assert 'market_data' in data
        md = data['market_data']
        assert Decimal(md['price']) == Decimal('1850.00')
        assert md['price_type'] == 'LTP'
        assert md['published_at'] is not None
        assert md['age_seconds'] is not None


@pytest.mark.django_db
class TestDashboardFinancialCorrectness:
    def test_dashboard_holdings_unvalued_holding_has_null_valuation_date(self, users):
        user = users['user']
        portfolio = Portfolio.objects.create(user=user, name='Main Portfolio', base_currency='INR')

        # Investment with no valuation snapshots
        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            category=AssetCategory.EQUITY,
            display_name='Unvalued Holding',
            initial_value=Decimal('50000.00'),
            current_value=Decimal('50000.00'),
            currency='INR',
            is_active=True,
        )

        holdings_res = DashboardService.get_holdings_overview(user)
        assert holdings_res['count'] == 1
        item = holdings_res['results'][0]
        assert item['id'] == str(inv.id)
        assert item['valuation_date'] is None
        assert item['valuation_source'] is None
        assert item['valuation_status'] == 'MISSING'

    def test_dashboard_data_quality_classifies_awaiting_verification(self, canonical_instruments, users):
        user = users['user']
        op = users['operator']
        inst = canonical_instruments['tcs']
        now = datetime.now(timezone.utc)

        # Create pending review observation
        PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('3500.00'),
            currency='INR',
            effective_at=now,
            source='OPERATOR',
            status=ObservationStatus.PENDING_REVIEW,
            recorded_by=op,
        )

        portfolio = Portfolio.objects.create(user=user, name='Growth Portfolio', base_currency='INR')
        Investment.objects.create(
            user=user,
            portfolio=portfolio,
            instrument=inst,
            category=AssetCategory.EQUITY,
            display_name='TCS Holding',
            initial_value=Decimal('35000.00'),
            current_value=Decimal('35000.00'),
            currency='INR',
            is_active=True,
        )

        dq = DashboardService.get_data_quality(user)
        assert dq['categories']['awaiting_verification']['count'] == 1
        items = dq['categories']['awaiting_verification']['items']
        assert items[0]['display_name'] == 'TCS Holding'
