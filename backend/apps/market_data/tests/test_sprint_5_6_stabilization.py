import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import connection, connections, transaction
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
from apps.valuation.services.asset_valuation.base import ValuationStatus
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

    def test_draft_cannot_be_published_directly(self, api_client, canonical_instruments, users):
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
            status=ObservationStatus.DRAFT,
            recorded_by=op,
        )

        api_client.force_authenticate(user=pub)
        pub_resp = api_client.post(f'/api/v1/market-data/observations/{obs.id}/publish/')
        assert pub_resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'PENDING_REVIEW' in str(pub_resp.data)

        # Operator submits for review
        api_client.force_authenticate(user=op)
        sub_resp = api_client.post(f'/api/v1/market-data/observations/{obs.id}/submit-for-review/')
        assert sub_resp.status_code == status.HTTP_200_OK
        obs.refresh_from_db()
        assert obs.status == ObservationStatus.PENDING_REVIEW

        # Now publisher can publish
        api_client.force_authenticate(user=pub)
        pub_resp2 = api_client.post(f'/api/v1/market-data/observations/{obs.id}/publish/')
        assert pub_resp2.status_code == status.HTTP_200_OK
        obs.refresh_from_db()
        assert obs.status == ObservationStatus.PUBLISHED

    def test_correction_rules_enforced(self, api_client, canonical_instruments, users):
        inst = canonical_instruments['infy']
        op = users['operator']
        pub = users['publisher']
        now = datetime.now(timezone.utc)

        obs_draft = PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('1855.00'),
            currency='INR',
            effective_at=now,
            source='NSE',
            status=ObservationStatus.DRAFT,
            recorded_by=op,
        )

        api_client.force_authenticate(user=pub)
        # 1. Reject correction on non-published observation
        corr_resp = api_client.post(
            f'/api/v1/market-data/observations/{obs_draft.id}/correct/',
            {'value': '1860.00', 'correction_reason': 'Data entry error'},
        )
        assert corr_resp.status_code == status.HTTP_400_BAD_REQUEST

        # Transition to published
        obs_draft.status = ObservationStatus.PENDING_REVIEW
        obs_draft.save()
        obs_draft.publish(pub)

        # 2. First correction succeeds
        corr_resp1 = api_client.post(
            f'/api/v1/market-data/observations/{obs_draft.id}/correct/',
            {'value': '1860.00', 'correction_reason': 'Data entry error'},
        )
        assert corr_resp1.status_code == status.HTTP_201_CREATED

        # 3. Second correction on the same original observation is rejected
        corr_resp2 = api_client.post(
            f'/api/v1/market-data/observations/{obs_draft.id}/correct/',
            {'value': '1865.00', 'correction_reason': 'Another correction'},
        )
        assert corr_resp2.status_code == status.HTTP_400_BAD_REQUEST
        assert 'superseded' in str(corr_resp2.data)


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

    def test_csv_commit_without_batch_id_rejected(self, api_client, users):
        op = users['operator']
        api_client.force_authenticate(user=op)
        resp = api_client.post('/api/v1/market-data/import/commit/', {'preview_result': {'valid_rows': []}}, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'batch_id' in str(resp.data)


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


@pytest.mark.django_db(transaction=True)
class TestConcurrencyStabilization:
    def test_watchlist_multithreaded_concurrency(self, canonical_instruments, users):
        if connection.vendor == 'sqlite':
            pytest.skip("Multi-threaded row lock concurrency tests require PostgreSQL.")
        from apps.watchlists.models import WatchlistItem

        inst = canonical_instruments['infy']
        user = users['user']

        successes = []
        errors = []

        def attempt_add(i):
            for _ in range(10):
                try:
                    item = WatchlistService.add_item(user, inst.id)
                    successes.append(item)
                    break
                except ValidationError as e:
                    errors.append(e)
                    break
                except Exception:
                    time.sleep(0.05)
                finally:
                    connections['default'].close()

        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(attempt_add, range(5)))

        assert len(successes) == 1
        assert WatchlistItem.objects.filter(user=user, instrument=inst).count() == 1
        assert len(errors) == 4

    def test_observation_publication_multithreaded_concurrency(self, canonical_instruments, users):
        if connection.vendor == 'sqlite':
            pytest.skip("Multi-threaded row lock concurrency tests require PostgreSQL.")
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

        successes = []

        def attempt_publish(i):
            for _ in range(15):
                try:
                    with transaction.atomic(using='market_data'):
                        locked = PriceObservation.objects.select_for_update().get(id=obs.id)
                        locked.publish(pub)
                        successes.append(locked)
                    break
                except ValidationError:
                    break
                except Exception:
                    time.sleep(0.05)
                finally:
                    connections['market_data'].close()
                    connections['default'].close()

        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(attempt_publish, range(4)))

        obs.refresh_from_db()
        assert obs.status == ObservationStatus.PUBLISHED


@pytest.mark.django_db
class TestProductMappingStabilization:
    def test_government_bond_detail_creation(self, api_client, users):
        user = users['user']
        portfolio = Portfolio.objects.create(user=user, name='Fixed Income Portfolio', base_currency='INR')
        api_client.force_authenticate(user=user)

        payload = {
            'portfolio': str(portfolio.id),
            'category': 'fixed_income',
            'asset_type': 'government_bond',
            'display_name': '7.18% GS 2033',
            'initial_value': '10000.00',
            'currency': 'INR',
            'details': {
                'bond_name': '7.18% GS 2033',
                'issuer': 'Government of India',
                'bond_type': 'SOVEREIGN',
                'face_value': '100.00',
                'purchase_price': '100.00',
                'quantity': '100',
                'coupon_rate_pct': '7.18',
                'coupon_frequency': 'SEMI_ANNUALLY',
                'purchase_date': '2024-01-15',
                'maturity_date': '2033-08-14',
            },
        }
        resp = api_client.post('/api/v1/investments/', payload, format='json')
        assert resp.status_code == status.HTTP_201_CREATED
        inv = Investment.objects.get(id=resp.data['id'])
        assert hasattr(inv, 'bond_detail')
        assert inv.bond_detail.issuer_name == 'Government of India'

    def test_reit_detail_creation(self, api_client, users):
        user = users['user']
        portfolio = Portfolio.objects.create(user=user, name='Real Estate Portfolio', base_currency='INR')
        api_client.force_authenticate(user=user)

        payload = {
            'portfolio': str(portfolio.id),
            'category': 'real_estate',
            'asset_type': 'reit',
            'display_name': 'Embassy Office Parks REIT',
            'initial_value': '35000.00',
            'currency': 'INR',
            'details': {
                'property_nickname': 'Embassy REIT Units',
                'property_type': 'REIT',
                'purchase_price': '35000.00',
                'units': '100',
                'acquisition_date': '2024-02-01',
                'country': 'India',
                'state': 'Karnataka',
            },
        }
        resp = api_client.post('/api/v1/investments/', payload, format='json')
        assert resp.status_code == status.HTTP_201_CREATED
        inv = Investment.objects.get(id=resp.data['id'])
        assert inv.quantity == Decimal('100.0000')
        assert hasattr(inv, 'real_estate_detail')
        assert inv.real_estate_detail.property_type == 'REIT'


@pytest.mark.django_db
class TestValuationStrategyUnification:
    def test_equity_valuation_strategy_no_silent_success_fallback(self, canonical_instruments, users):
        from apps.assets.models import EquityDetail
        from apps.valuation.services.asset_valuation.equity import EquityValuationStrategy
        inst = canonical_instruments['infy']
        user = users['user']
        portfolio = Portfolio.objects.create(user=user, name='EQ Portfolio', base_currency='INR')

        # Investment with NO market observations published
        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            instrument=inst,
            category=AssetCategory.EQUITY,
            asset_type='stock',
            display_name='Infosys Holding',
            initial_value=Decimal('15000.00'),
            current_value=Decimal('15000.00'),
            currency='INR',
            is_active=True,
        )
        EquityDetail.objects.create(
            investment=inv,
            company_name='Infosys Limited',
            symbol='INFY',
            quantity=Decimal('10'),
            average_buy_price=Decimal('1500.00'),
            purchase_date=date.today(),
        )

        strategy = EquityValuationStrategy()
        val = strategy.evaluate(inv)

        # Must NOT silently return SUCCESS with purchase price!
        assert val.status == ValuationStatus.MARKET_DATA_UNAVAILABLE
        assert val.current_value is None

    def test_equity_valuation_strategy_resolves_published_price(self, canonical_instruments, users):
        from apps.assets.models import EquityDetail
        from apps.valuation.services.asset_valuation.equity import EquityValuationStrategy
        inst = canonical_instruments['infy']
        user = users['user']
        pub = users['publisher']
        portfolio = Portfolio.objects.create(user=user, name='EQ Portfolio', base_currency='INR')
        now = datetime.now(timezone.utc)

        PriceObservation.objects.create(
            instrument=inst,
            price_type='LTP',
            value=Decimal('1850.00'),
            currency='INR',
            effective_at=now,
            source='NSE_VERIFIED',
            status=ObservationStatus.PUBLISHED,
            recorded_by=pub,
            published_by=pub,
            published_at=now,
        )

        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            instrument=inst,
            category=AssetCategory.EQUITY,
            asset_type='stock',
            display_name='Infosys Holding',
            initial_value=Decimal('15000.00'),
            current_value=Decimal('15000.00'),
            currency='INR',
            is_active=True,
        )
        EquityDetail.objects.create(
            investment=inv,
            company_name='Infosys Limited',
            symbol='INFY',
            quantity=Decimal('10'),
            average_buy_price=Decimal('1500.00'),
            purchase_date=date.today(),
        )

        strategy = EquityValuationStrategy()
        val = strategy.evaluate(inv)

        assert val.status == ValuationStatus.SUCCESS
        assert val.current_value == Decimal('18500.00')
        assert val.source == 'NSE_VERIFIED'

    def test_equity_valuation_strategy_user_estimate(self, canonical_instruments, users):
        from apps.valuation.services.asset_valuation.equity import EquityValuationStrategy
        inst = canonical_instruments['infy']
        user = users['user']
        portfolio = Portfolio.objects.create(user=user, name='EQ Portfolio', base_currency='INR')

        inv = Investment.objects.create(
            user=user,
            portfolio=portfolio,
            instrument=inst,
            category=AssetCategory.EQUITY,
            asset_type='stock',
            display_name='Infosys Holding',
            initial_value=Decimal('15000.00'),
            current_value=Decimal('15000.00'),
            currency='INR',
            is_active=True,
        )
        inv.details = {'quantity': Decimal('10'), 'current_price': '1800.00'}

        strategy = EquityValuationStrategy()
        val = strategy.evaluate(inv)

        assert val.status == ValuationStatus.ESTIMATED
        assert val.current_value == Decimal('18000.00')
        assert val.source == 'USER_ESTIMATE'
        assert val.source == 'USER_ESTIMATE'

    def test_serializer_exposes_market_data_fields(self, canonical_instruments, users):
        from apps.watchlists.api.v1.serializers import MarketDataAnnotationSerializer
        inst = canonical_instruments['infy']
        pub = users['publisher']
        now = datetime.now(timezone.utc)

        obs = PriceObservation.objects.create(
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

        data = {
            'price': obs.value,
            'currency': obs.currency,
            'unit': obs.unit,
            'effective_at': obs.effective_at,
            'published_at': obs.published_at,
            'price_type': obs.price_type,
            'age_seconds': 120,
            'status': 'AVAILABLE',
            'source': obs.source,
            'source_reference': 'INFY',
            'is_synthetic': False,
            'notes': '',
            'movement': {
                'change_amount': None,
                'change_percent': None,
                'previous_price': None,
                'previous_effective_at': None,
                'status': 'NO_CHANGE',
                'notes': '',
            },
        }

        serializer = MarketDataAnnotationSerializer(data)
        out = serializer.data
        assert out['published_at'] is not None
        assert out['price_type'] == 'LTP'
        assert out['age_seconds'] == 120
