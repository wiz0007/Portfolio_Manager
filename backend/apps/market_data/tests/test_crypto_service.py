"""Unit tests for CryptoMarketDataService and crypto management commands."""
from decimal import Decimal
from unittest.mock import MagicMock

from django.test import TestCase

from apps.market_data.models.coverage import InstrumentCoverage, PriceType
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
from apps.market_data.models.series import MarketDataSeries
from apps.market_data.services.crypto_service import CryptoMarketDataService


class CryptoMarketDataServiceTests(TestCase):
    databases = {'default', 'market_data'}

    def test_sync_catalogue_creates_instruments_and_series(self):
        sample_coins = [
            {'id': 'bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin'},
            {'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum'},
        ]
        result = CryptoMarketDataService.sync_catalogue(sample_coins)
        self.assertEqual(result['total_synced'], 2)
        self.assertEqual(result['created'], 2)

        # Verify Canonical Instrument in default database
        btc_inst = Instrument.objects.using('default').get(symbol='BTC', asset_class=AssetClass.CRYPTO)
        self.assertEqual(btc_inst.name, 'Bitcoin')

        # Verify Provider Mapping in market_data database
        mapping = ProviderInstrumentMapping.objects.using('market_data').get(
            instrument_id=btc_inst.id,
            provider_name='COINGECKO',
        )
        self.assertEqual(mapping.provider_symbol, 'bitcoin')

        # Verify Coverage policy
        cov = InstrumentCoverage.objects.using('market_data').get(instrument_id=btc_inst.id)
        self.assertEqual(cov.price_type, PriceType.LTP)
        self.assertEqual(cov.currency, 'INR')

        # Verify Series
        series = MarketDataSeries.objects.using('market_data').get(
            instrument_id=btc_inst.id,
            source='COINGECKO',
        )
        self.assertEqual(series.price_type, PriceType.LTP)

    def test_sync_prices_ingests_and_publishes_observations(self):
        sample_coins = [{'id': 'bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin'}]
        CryptoMarketDataService.sync_catalogue(sample_coins)

        mock_client = MagicMock()
        mock_client.get_markets.return_value = [
            {
                'id': 'bitcoin',
                'symbol': 'btc',
                'name': 'Bitcoin',
                'current_price': 8500000.0,
                'market_cap': 170000000000000,
                'total_volume': 3000000000,
                'high_24h': 8600000.0,
                'low_24h': 8400000.0,
                'price_change_24h': 100000.0,
                'price_change_percentage_24h': 1.19,
                'last_updated': '2026-11-26T12:00:00.000Z',
            }
        ]

        res = CryptoMarketDataService.sync_prices(coin_ids=['bitcoin'], client=mock_client)
        self.assertEqual(res['synced'], 1)

        btc_inst = Instrument.objects.using('default').get(symbol='BTC')
        obs = PriceObservation.objects.using('market_data').filter(
            instrument_id=btc_inst.id,
            source='COINGECKO',
            status=ObservationStatus.PUBLISHED,
        ).first()

        self.assertIsNotNone(obs)
        self.assertEqual(obs.value, Decimal('8500000.0'))
        self.assertEqual(obs.high_price, Decimal('8600000.0'))
        self.assertEqual(obs.low_price, Decimal('8400000.0'))
        self.assertFalse(obs.is_synthetic)

    def test_backfill_history(self):
        sample_coins = [{'id': 'solana', 'symbol': 'SOL', 'name': 'Solana'}]
        CryptoMarketDataService.sync_catalogue(sample_coins)

        mock_client = MagicMock()
        mock_client.get_market_chart.return_value = {
            'prices': [
                [1764115200000, 18500.0],
                [1764201600000, 19200.0],
            ],
            'total_volumes': [
                [1764115200000, 50000000],
                [1764201600000, 60000000],
            ],
            'market_caps': [
                [1764115200000, 8500000000],
                [1764201600000, 8800000000],
            ],
        }

        count = CryptoMarketDataService.backfill_history('solana', days=2, client=mock_client)
        self.assertEqual(count, 2)

        sol_inst = Instrument.objects.using('default').get(symbol='SOL')
        observations = PriceObservation.objects.using('market_data').filter(
            instrument_id=sol_inst.id,
            source='COINGECKO',
        ).order_by('effective_at')

        self.assertEqual(observations.count(), 2)
        self.assertEqual(observations[0].value, Decimal('18500.0'))
        self.assertEqual(observations[1].value, Decimal('19200.0'))
