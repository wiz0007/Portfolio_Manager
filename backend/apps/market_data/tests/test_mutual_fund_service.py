"""Unit tests for MutualFundMarketDataService and management commands."""
from decimal import Decimal
from unittest.mock import MagicMock

from django.test import TestCase

from apps.market_data.models.coverage import InstrumentCoverage, PriceType
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
from apps.market_data.models.series import MarketDataSeries
from apps.market_data.services.mutual_fund_service import MutualFundMarketDataService


class MutualFundMarketDataServiceTests(TestCase):
    databases = {'default', 'market_data'}

    def test_sync_catalogue_creates_instruments_and_series(self):
        sample_schemes = [
            {
                'scheme_code': '122639',
                'scheme_name': 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth',
                'fund_house': 'PPFAS Mutual Fund',
                'isin': 'INF879O01027',
                'plan_type': 'DIRECT',
                'option_type': 'GROWTH',
            }
        ]
        res = MutualFundMarketDataService.sync_catalogue(sample_schemes)
        self.assertEqual(res['total_synced'], 1)
        self.assertEqual(res['created'], 1)

        # Verify Canonical Instrument
        inst = Instrument.objects.using('default').get(scheme_code='122639', asset_class=AssetClass.MUTUAL_FUND)
        self.assertEqual(inst.symbol, '122639')
        self.assertEqual(inst.isin, 'INF879O01027')

        # Verify Mappings
        mfapi_map = ProviderInstrumentMapping.objects.using('market_data').get(
            instrument_id=inst.id,
            provider_name='MFAPI',
        )
        self.assertEqual(mfapi_map.provider_symbol, '122639')
        self.assertTrue(mfapi_map.is_primary)

        # Verify Coverage
        cov = InstrumentCoverage.objects.using('market_data').get(instrument_id=inst.id)
        self.assertEqual(cov.price_type, PriceType.NAV)
        self.assertEqual(cov.currency, 'INR')

        # Verify Series
        series = MarketDataSeries.objects.using('market_data').get(
            instrument_id=inst.id,
            source='MFAPI',
            price_type=PriceType.NAV,
        )
        self.assertIsNotNone(series)

    def test_sync_nav_creates_published_observation(self):
        sample_schemes = [
            {
                'scheme_code': '122639',
                'scheme_name': 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth',
                'fund_house': 'PPFAS Mutual Fund',
            }
        ]
        MutualFundMarketDataService.sync_catalogue(sample_schemes)

        mock_client = MagicMock()
        mock_client.get_scheme.return_value = {
            'meta': {
                'fund_house': 'PPFAS Mutual Fund',
                'scheme_name': 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth',
                'scheme_code': 122639,
            },
            'data': [
                {'date': '25-11-2026', 'nav': '93.5000'},
                {'date': '26-11-2026', 'nav': '94.2590'},
            ],
            'status': 'SUCCESS',
        }

        res = MutualFundMarketDataService.sync_nav(scheme_codes=['122639'], client=mock_client)
        self.assertEqual(res['synced'], 1)

        inst = Instrument.objects.using('default').get(scheme_code='122639')
        obs = PriceObservation.objects.using('market_data').filter(
            instrument_id=inst.id,
            source='MFAPI',
            status=ObservationStatus.PUBLISHED,
        ).first()

        self.assertIsNotNone(obs)
        self.assertEqual(obs.value, Decimal('94.2590'))
        self.assertEqual(obs.price_type, PriceType.NAV)
        self.assertFalse(obs.is_synthetic)

    def test_backfill_history(self):
        sample_schemes = [
            {
                'scheme_code': '118834',
                'scheme_name': 'Mirae Asset Large Cap Fund - Direct Plan - Growth Option',
                'fund_house': 'Mirae Asset Mutual Fund',
            }
        ]
        MutualFundMarketDataService.sync_catalogue(sample_schemes)

        mock_client = MagicMock()
        mock_client.get_scheme.return_value = {
            'meta': {'scheme_name': 'Mirae Asset Large Cap'},
            'data': [
                {'date': '24-11-2026', 'nav': '123.0000'},
                {'date': '25-11-2026', 'nav': '123.8000'},
                {'date': '26-11-2026', 'nav': '124.5000'},
            ],
        }

        count = MutualFundMarketDataService.backfill_history('118834', days=2, client=mock_client)
        self.assertEqual(count, 2)

        inst = Instrument.objects.using('default').get(scheme_code='118834')
        observations = PriceObservation.objects.using('market_data').filter(
            instrument_id=inst.id,
            source='MFAPI',
        ).order_by('effective_at')

        self.assertEqual(observations.count(), 2)
        self.assertEqual(observations[0].value, Decimal('123.8000'))
        self.assertEqual(observations[1].value, Decimal('124.5000'))
