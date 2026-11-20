from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models.investment import Investment
from apps.assets.models.valuations import InvestmentValuation
from apps.market_data.models.coverage import (
    CollectionCadence,
    InstrumentCoverage,
    PriceType,
    QuotationUnit,
)
from apps.market_data.models.instrument import AssetClass, Instrument, InstrumentStatus
from apps.market_data.models.instrument_request import (
    InstrumentRequest,
    InstrumentRequestStatus,
)
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.models.worklist import DueReason, WorklistItemStatus
from apps.market_data.services.import_service import PriceImportService
from apps.market_data.services.price_resolver import PriceResolver, ResolutionStatus
from apps.market_data.services.worklist_service import MarketDataWorklistService
from apps.portfolios.models.portfolio import Portfolio
from apps.users.models.user import User


@pytest.fixture
def standard_user(db):
    return User.objects.create_user(
        email="standard_user@example.com",
        password="SecurePassword123!",
        full_name="Standard User",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="other_user@example.com",
        password="SecurePassword123!",
        full_name="Other User",
    )


@pytest.fixture
def staff_operator(db):
    return User.objects.create_user(
        email="operator@example.com",
        password="SecurePassword123!",
        full_name="Market Operator",
        is_staff=True,
    )


@pytest.fixture
def canonical_instrument(db):
    inst = Instrument.objects.create(
        symbol="INFY",
        name="Infosys Limited",
        asset_class=AssetClass.EQUITY,
        exchange="NSE",
        currency="INR",
        isin="INE009A01021",
        status=InstrumentStatus.ACTIVE,
    )
    InstrumentCoverage.objects.create(
        instrument=inst,
        price_type=PriceType.LTP,
        currency="INR",
        unit=QuotationUnit.SHARES,
        cadence=CollectionCadence.EVERY_TRADING_DAY,
        freshness_hours=24,
        preferred_source="MANUAL_VERIFIED",
    )
    return inst


@pytest.mark.django_db
class TestInstrumentRequestsAndCatalogue:
    """
    Tests unknown-instrument request submission, deduplication, and operator review actions.
    """

    def test_user_can_submit_instrument_request(self, standard_user):
        client = APIClient()
        client.force_authenticate(user=standard_user)

        payload = {
            "raw_name": "Tata Technologies Ltd",
            "asset_class": "EQUITY",
            "symbol": "TATATECH",
            "exchange": "NSE",
            "isin": "INE142M01025",
            "notes": "Recently listed equity",
        }
        res = client.post('/api/v1/market-data/requests/', payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['status'] == 'PENDING'
        assert res.data['symbol'] == 'TATATECH'

    def test_duplicate_pending_request_rejected(self, standard_user):
        client = APIClient()
        client.force_authenticate(user=standard_user)

        payload = {
            "raw_name": "Tata Technologies Ltd",
            "asset_class": "EQUITY",
            "symbol": "TATATECH",
            "exchange": "NSE",
        }
        res1 = client.post('/api/v1/market-data/requests/', payload, format='json')
        assert res1.status_code == status.HTTP_201_CREATED

        # Duplicate pending submission
        res2 = client.post('/api/v1/market-data/requests/', payload, format='json')
        assert res2.status_code == status.HTTP_400_BAD_REQUEST

    def test_cross_user_request_isolation(self, standard_user, other_user):
        client_a = APIClient()
        client_a.force_authenticate(user=standard_user)
        res_a = client_a.post('/api/v1/market-data/requests/', {'raw_name': 'HDFC Life', 'asset_class': 'EQUITY', 'symbol': 'HDFCLIFE'}, format='json')
        req_id = res_a.data['id']

        client_b = APIClient()
        client_b.force_authenticate(user=other_user)
        # Attempt to retrieve User A's request
        res_b = client_b.get(f'/api/v1/market-data/requests/{req_id}/')
        assert res_b.status_code == status.HTTP_404_NOT_FOUND

    def test_staff_approval_creates_canonical_instrument_and_coverage_atomically(self, standard_user, staff_operator):
        req = InstrumentRequest.objects.create(
            user=standard_user,
            raw_name="LTIMindtree",
            asset_class=AssetClass.EQUITY,
            symbol="LTIM",
            exchange="NSE",
        )

        client = APIClient()
        client.force_authenticate(user=staff_operator)

        approve_payload = {
            "symbol": "LTIM",
            "name": "LTIMindtree Limited",
            "asset_class": "EQUITY",
            "exchange": "NSE",
            "currency": "INR",
            "isin": "INE214T01019",
            "cadence": "EVERY_TRADING_DAY",
            "price_type": "LTP",
            "unit": "SHARES",
            "freshness_hours": 24,
        }
        res = client.post(f'/api/v1/market-data/requests/{req.id}/approve/', approve_payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED

        req.refresh_from_db()
        assert req.status == InstrumentRequestStatus.APPROVED
        assert req.matched_instrument is not None
        assert req.matched_instrument.symbol == 'LTIM'
        assert hasattr(req.matched_instrument, 'coverage')
        assert req.matched_instrument.coverage.cadence == CollectionCadence.EVERY_TRADING_DAY

    def test_staff_rejection_records_reason(self, standard_user, staff_operator):
        req = InstrumentRequest.objects.create(
            user=standard_user,
            raw_name="Fake Scam Coin",
            asset_class=AssetClass.CRYPTO,
            symbol="SCAM",
        )
        client = APIClient()
        client.force_authenticate(user=staff_operator)

        res = client.post(f'/api/v1/market-data/requests/{req.id}/reject/', {'reason': 'Invalid unregulated asset.'}, format='json')
        assert res.status_code == status.HTTP_200_OK

        req.refresh_from_db()
        assert req.status == InstrumentRequestStatus.REJECTED
        assert req.rejection_reason == 'Invalid unregulated asset.'


@pytest.mark.django_db
class TestWorklistGenerationAndExport:
    """
    Tests deterministic daily worklist generation, schedule filtering, and export.
    """

    def test_worklist_identifies_first_price_and_due_today(self, canonical_instrument):
        today = date(2026, 11, 17)  # Tuesday (Trading Day)
        worklist = MarketDataWorklistService.generate_worklist(today)

        assert worklist.total_items >= 1
        item = worklist.items.filter(instrument=canonical_instrument).first()
        assert item is not None
        assert item.due_reason == DueReason.FIRST_PRICE
        assert item.status == WorklistItemStatus.PENDING

    def test_worklist_generation_is_idempotent(self, canonical_instrument):
        today = date(2026, 11, 18)
        wl1 = MarketDataWorklistService.generate_worklist(today)
        count1 = wl1.items.count()

        wl2 = MarketDataWorklistService.generate_worklist(today)
        count2 = wl2.items.count()
        assert count1 == count2
        assert wl1.id == wl2.id

    def test_worklist_markdown_and_csv_export(self, canonical_instrument):
        today = date(2026, 11, 19)
        worklist = MarketDataWorklistService.generate_worklist(today)

        md = MarketDataWorklistService.export_to_markdown(worklist)
        assert "# Market Data Collection Worklist" in md
        assert "INFY" in md

        csv_str = MarketDataWorklistService.export_to_csv(worklist)
        assert "schema_version,worklist_item_id,instrument_id" in csv_str
        assert "INFY" in csv_str


@pytest.mark.django_db
class TestObservationLifecycleAndImport:
    """
    Tests manual price observation drafting, review, immutable publishing, correction chaining, and CSV import.
    """

    def test_operator_can_create_draft_observation(self, canonical_instrument, staff_operator):
        client = APIClient()
        client.force_authenticate(user=staff_operator)

        eff_dt = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
        payload = {
            "instrument": str(canonical_instrument.id),
            "price_type": "LTP",
            "value": "1850.5000",
            "currency": "INR",
            "unit": "SHARES",
            "effective_at": eff_dt.isoformat(),
            "source": "NSE_WEBSITE",
            "source_reference": "https://www.nseindia.com/get-quotes/equity?symbol=INFY",
        }
        res = client.post('/api/v1/market-data/observations/', payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['status'] == 'DRAFT'
        assert Decimal(res.data['value']) == Decimal('1850.5000')

    def test_observation_publication_and_correction_workflow(self, canonical_instrument, staff_operator):
        eff_dt = datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc)
        obs = PriceObservation.objects.create(
            instrument=canonical_instrument,
            price_type=PriceType.LTP,
            value=Decimal("1850.5000"),
            currency="INR",
            unit=QuotationUnit.SHARES,
            effective_at=eff_dt,
            source="NSE_WEBSITE",
            status=ObservationStatus.DRAFT,
            recorded_by=staff_operator,
        )

        client = APIClient()
        client.force_authenticate(user=staff_operator)

        # 0. Submit observation for review (Draft -> Pending Review)
        res_sub = client.post(f'/api/v1/market-data/observations/{obs.id}/submit-for-review/')
        assert res_sub.status_code == status.HTTP_200_OK

        # 1. Publish observation
        res_pub = client.post(f'/api/v1/market-data/observations/{obs.id}/publish/')
        assert res_pub.status_code == status.HTTP_200_OK
        obs.refresh_from_db()
        assert obs.status == ObservationStatus.PUBLISHED
        assert obs.published_by == staff_operator

        # 2. Immutable: cannot reject once published
        res_rej = client.post(f'/api/v1/market-data/observations/{obs.id}/reject/', {'reason': 'Oops'})
        assert res_rej.status_code == status.HTTP_400_BAD_REQUEST

        # 3. Correction creates chained observation
        res_corr = client.post(
            f'/api/v1/market-data/observations/{obs.id}/correct/',
            {
                'value': '1855.0000',
                'correction_reason': 'Closing auction adjustment after manual audit',
            },
            format='json',
        )
        assert res_corr.status_code == status.HTTP_201_CREATED
        corr_data = res_corr.data['correction']
        assert Decimal(corr_data['value']) == Decimal('1855.0000')
        assert str(corr_data['correction_of']) == str(obs.id)

    def test_csv_import_preview_and_commit(self, canonical_instrument, staff_operator):
        csv_content = (
            "schema_version,worklist_item_id,instrument_id,symbol,price_type,value,currency,unit,effective_at,source_id,source_reference,notes\n"
            f"1.0,,{canonical_instrument.id},INFY,LTP,1860.00,INR,SHARES,2026-11-17T10:00:00Z,MANUAL_VERIFIED,NSE,=cmd|' /C calc'!A0\n"
        )
        preview = PriceImportService.preview_csv(staff_operator, csv_content, filename='quotes.csv')
        assert preview['total_rows'] == 1
        assert preview['valid_count'] == 1
        assert preview['error_count'] == 0

        # Formula injection stripped
        valid_row = preview['valid_rows'][0]
        assert not valid_row['notes'].startswith('=')

        batch = PriceImportService.commit_import(staff_operator, preview)
        assert batch.valid_rows == 1
        draft = PriceObservation.objects.filter(instrument=canonical_instrument, status=ObservationStatus.DRAFT).first()
        assert draft is not None
        assert draft.value == Decimal('1860.0000')


@pytest.mark.django_db
class TestPriceResolverAndSharedValuationRefresh:
    """
    Tests that published observations update valuations across all user holdings
    without mutating historical transaction records or cost basis.
    """

    def test_resolver_respects_as_of_bounds_and_draft_exclusion(self, canonical_instrument, staff_operator):
        t1 = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)

        # Published observation at t1
        PriceObservation.objects.create(
            instrument=canonical_instrument,
            price_type=PriceType.LTP,
            value=Decimal("1700.0000"),
            currency="INR",
            unit=QuotationUnit.SHARES,
            effective_at=t1,
            status=ObservationStatus.PUBLISHED,
            recorded_by=staff_operator,
            published_by=staff_operator,
            published_at=t1,
        )

        # Draft observation at t2 (must NOT be used)
        PriceObservation.objects.create(
            instrument=canonical_instrument,
            price_type=PriceType.LTP,
            value=Decimal("1900.0000"),
            currency="INR",
            unit=QuotationUnit.SHARES,
            effective_at=t2,
            status=ObservationStatus.DRAFT,
            recorded_by=staff_operator,
        )

        # Resolve as of t1 + 1 day
        resolved = PriceResolver.resolve_price(canonical_instrument, as_of=t1 + timedelta(days=1))
        assert resolved.status in (ResolutionStatus.AVAILABLE, ResolutionStatus.STALE)
        assert resolved.price == Decimal("1700.0000")

        # Resolve before t1: missing price
        resolved_past = PriceResolver.resolve_price(canonical_instrument, as_of=t1 - timedelta(days=1))
        assert resolved_past.status == ResolutionStatus.MISSING
        assert resolved_past.price is None

    def test_published_observation_refreshes_multi_user_holdings(
        self, canonical_instrument, standard_user, other_user, staff_operator
    ):
        from apps.assets.models import EquityDetail

        # Create holding for User A
        port_a = Portfolio.objects.create(user=standard_user, name="Port A", base_currency="INR")
        inv_a = Investment.objects.create(
            portfolio=port_a,
            user=standard_user,
            instrument=canonical_instrument,
            category="equity",
            asset_type="listed_stock",
            display_name="Infosys Holding A",
            currency="INR",
            invested_amount=Decimal("15000.00"),
            current_value=Decimal("15000.00"),
        )
        EquityDetail.objects.create(
            investment=inv_a,
            company_name="Infosys Limited",
            symbol="INFY",
            exchange="NSE",
            quantity=Decimal("10.0000"),
            average_buy_price=Decimal("1500.00"),
            purchase_date=date(2026, 1, 1),
        )

        # Create holding for User B (same instrument)
        port_b = Portfolio.objects.create(user=other_user, name="Port B", base_currency="INR")
        inv_b = Investment.objects.create(
            portfolio=port_b,
            user=other_user,
            instrument=canonical_instrument,
            category="equity",
            asset_type="listed_stock",
            display_name="Infosys Holding B",
            currency="INR",
            invested_amount=Decimal("8000.00"),
            current_value=Decimal("8000.00"),
        )
        EquityDetail.objects.create(
            investment=inv_b,
            company_name="Infosys Limited",
            symbol="INFY",
            exchange="NSE",
            quantity=Decimal("5.0000"),
            average_buy_price=Decimal("1600.00"),
            purchase_date=date(2026, 2, 1),
        )

        # Draft observation at 1800.00
        eff_dt = datetime.now(timezone.utc)
        obs = PriceObservation.objects.create(
            instrument=canonical_instrument,
            price_type=PriceType.LTP,
            value=Decimal("1800.0000"),
            currency="INR",
            unit=QuotationUnit.SHARES,
            effective_at=eff_dt,
            source="NSE_MANUAL",
            status=ObservationStatus.DRAFT,
            recorded_by=staff_operator,
        )

        client = APIClient()
        client.force_authenticate(user=staff_operator)

        # Submit observation for review (Draft -> Pending Review)
        res_sub = client.post(f'/api/v1/market-data/observations/{obs.id}/submit-for-review/')
        assert res_sub.status_code == status.HTTP_200_OK

        # Publish observation
        res = client.post(f'/api/v1/market-data/observations/{obs.id}/publish/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['valuation_refresh']['refreshed_count'] == 2

        # Verify holdings recalculation
        inv_a.refresh_from_db()
        inv_b.refresh_from_db()

        # 10 shares * 1800 = 18,000
        assert inv_a.current_value == Decimal("18000.00")
        assert inv_a.invested_amount == Decimal("15000.00")  # Cost must NOT be mutated!

        # 5 shares * 1800 = 9,000
        assert inv_b.current_value == Decimal("9000.00")
        assert inv_b.invested_amount == Decimal("8000.00")  # Cost must NOT be mutated!

        # Snapshots created
        snap_a = InvestmentValuation.objects.filter(investment=inv_a).order_by('-created_at').first()
        assert snap_a is not None
        assert snap_a.amount == Decimal("18000.00")
