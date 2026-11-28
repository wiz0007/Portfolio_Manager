"""Management command to backfill historical cryptocurrency prices from CoinGecko."""
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.market_data.services.crypto_service import CryptoMarketDataService
from apps.market_data.services.system_publisher import SystemPublisher


class Command(BaseCommand):
    help = 'Backfills historical price observations for a cryptocurrency from CoinGecko.'

    def add_arguments(self, parser):
        parser.add_argument('coin_id', type=str, help='CoinGecko coin ID (e.g. bitcoin, ethereum)')
        parser.add_argument('--days', type=int, default=30, help='Number of days of history to backfill (default: 30, max: 365)')
        parser.add_argument('--dry-run', action='store_true', help='Fetch historical data without saving observations.')

    def handle(self, *args, **options):
        coin_id = options['coin_id'].strip().lower()
        days = options['days']
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING(f"DRY RUN: Fetching {days} days of history for {coin_id}..."))
            from apps.market_data.providers.coingecko.client import CoinGeckoClient
            history = CoinGeckoClient().get_market_chart(coin_id=coin_id, days=days)
            prices = history.get('prices', [])
            self.stdout.write(self.style.SUCCESS(f"Dry run complete: Retrieved {len(prices)} data points for {coin_id}."))
            return

        self.stdout.write(self.style.NOTICE(f"Backfilling {days} days of history for {coin_id}..."))
        publisher = get_user_model().objects.filter(is_superuser=True, is_active=True).first() or SystemPublisher

        try:
            count = CryptoMarketDataService.backfill_history(coin_id=coin_id, days=days, publisher=publisher)
            self.stdout.write(self.style.SUCCESS(f"Successfully backfilled {count} observations for {coin_id}."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Backfill failed: {e!s}"))
            sys.exit(1)
