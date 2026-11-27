"""
Tests for MarketDataSchedulerService, SystemPublisher authorization,
mutual fund NAV corrections, and API null semantics.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.market_data.models.coverage import InstrumentCoverage, PriceType, QuotationUnit
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
from apps.market_data.models.series import MarketDataSeries
from apps.market_data.providers.mfapi.client import MFAPIClient
from apps.market_data.services.market_data_service import MarketDataService
from apps.market_data.services.mutual_fund_service import MutualFundMarketDataService
from apps.market_data.services.scheduler_service import MarketDataSchedulerService
from apps.market_data.services.system_publisher import SystemPublisher


class SchedulerAndCorrectionsTests(TestCase):
    databases = {'default', 'market_data'}

    def setUp(self):
        self.instrument_id = uuid.uuid4()
        self.instrument = Instrument.objects.using('default').create(
            id=self.instrument_id,
            symbol='122639',
            name='Parag Parikh Flexi Cap Fund - Direct Plan - Growth',
            asset_class=AssetClass.MUTUAL_FUND,
            scheme_code='122639',
            currency='INR',
            exchange='AMFI',
            is_active=True,
        )
        self.series = MarketDataSeries.objects.using('market_data').create(
            instrument_id=self.instrument_id,
            exchange='AMFI',
            source='MFAPI',
            price_type=PriceType.NAV,
            currency='INR',
            unit=QuotationUnit.UNITS,
        )
        self.coverage = InstrumentCoverage.objects.using('market_data').create(
            instrument_id=self.instrument_id,
            price_type=PriceType.NAV,
            currency='INR',
            unit=QuotationUnit.UNITS,
            preferred_source='MFAPI',
        )
        self.mapping = ProviderInstrumentMapping.objects.using('market_data').create(
            instrument_id=self.instrument_id,
            provider_name='MFAPI',
            provider_symbol='122639',
            is_primary=True,
        )

    def test_system_publisher_authorizes_observation_publication(self):
        """Verify that SystemPublisher is authorized to publish draft observations."""
        now = datetime.now(timezone.utc)
        obs = PriceObservation.objects.using('market_data').create(
            instrument_id=self.instrument_id,
            series=self.series,
            effective_at=now,
            price_type=PriceType.NAV,
            value=Decimal('95.5000'),
            source='MFAPI',
            status=ObservationStatus.DRAFT,
        )
        obs.status = ObservationStatus.PENDING_REVIEW
        obs.save(using='market_data')

        # Publish using SystemPublisher
        obs.publish(publisher=SystemPublisher)
        self.assertEqual(obs.status, ObservationStatus.PUBLISHED)
        self.assertEqual(obs.published_by_id, SystemPublisher.id)

    def test_mutual_fund_nav_correction_workflow(self):
        """Verify that re-ingesting a modified NAV for the same date creates a chained correction."""
        effective_date = datetime(2026, 11, 25, 0, 0, tzinfo=timezone.utc)

        # 1. First ingestion of NAV
        initial_obs = PriceObservation.objects.using('market_data').create(
            instrument_id=self.instrument_id,
            series=self.series,
            effective_at=effective_date,
            price_type=PriceType.NAV,
            value=Decimal('90.0000'),
            source='MFAPI',
            status=ObservationStatus.PUBLISHED,
            published_by_id=SystemPublisher.id,
        )

        # 2. Provider later publishes a corrected NAV of 91.5000 for the same date
        mock_response = {
            'meta': {'fund_house': 'PPFAS', 'scheme_name': 'Parag Parikh Direct Growth'},
            'data': [
                {'date': '25-11-2026', 'nav': '91.5000'},
            ],
        }
        with patch.object(MFAPIClient, 'get_scheme', return_value=mock_response):
            res = MutualFundMarketDataService.sync_nav(scheme_codes=['122639'], publisher=SystemPublisher)

        self.assertEqual(res['corrected'], 1)

        # Verify the corrected observation is linked to the initial observation
        corrected_obs = PriceObservation.objects.using('market_data').filter(
            instrument_id=self.instrument_id,
            correction_of=initial_obs,
        ).first()
        self.assertIsNotNone(corrected_obs)
        self.assertEqual(corrected_obs.value, Decimal('91.5000'))
        self.assertEqual(corrected_obs.trust_class, 'CORRECTED')
        self.assertEqual(corrected_obs.status, ObservationStatus.PUBLISHED)

    @override_settings(MARKET_DATA_PROVIDER_MODE='PRODUCTION')
    def test_market_data_service_returns_null_semantics_for_missing_price(self):
        """Ensure missing quotes return None/null rather than 'N/A' or '0.0000' in production mode."""
        quote = MarketDataService.get_latest_quote(self.instrument)
        self.assertIsNone(quote.price)
        self.assertIsNone(quote.change_amount)
        self.assertIsNone(quote.change_percent)

    def test_scheduler_lock_and_due_state(self):
        """Verify scheduler respects locks, prevents overlap, and tracks job states."""
        state = MarketDataSchedulerService.get_job_state('crypto_prices')
        self.assertEqual(state['job_id'], 'crypto_prices')
        self.assertEqual(state['lock_status'], 'IDLE')

        # Test lock prevents concurrent dispatch
        with patch.object(MarketDataSchedulerService, 'is_provider_enabled', return_value=True):
            with patch('apps.market_data.services.scheduler_service.cache.add', return_value=False):
                res = MarketDataSchedulerService.run_job('crypto_prices')
                self.assertEqual(res['status'], 'LOCKED')
