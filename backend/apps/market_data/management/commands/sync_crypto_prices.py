"""Management command to fetch and publish current cryptocurrency prices from CoinGecko."""
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.market_data.services.crypto_service import CryptoMarketDataService
from apps.market_data.services.system_publisher import SystemPublisher


class Command(BaseCommand):
    help = 'Fetches current cryptocurrency quotes from CoinGecko and stores published observations.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--coins',
            type=str,
            help='Comma-separated list of CoinGecko coin IDs (e.g. bitcoin,ethereum)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of coins to ingest.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Fetch and parse price data without creating observations.',
        )

    def handle(self, *args, **options):
        coins_arg = options.get('coins')
        limit = options.get('limit')
        dry_run = options.get('dry_run', False)
        coin_ids = [c.strip().lower() for c in coins_arg.split(',') if c.strip()] if coins_arg else None
        if coin_ids and limit:
            coin_ids = coin_ids[:limit]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: Fetching cryptocurrency quotes without persisting..."))
            from apps.market_data.providers.coingecko.client import CoinGeckoClient
            quotes = CoinGeckoClient().get_markets(coin_ids=coin_ids)
            self.stdout.write(self.style.SUCCESS(f"Dry run complete: Received quotes for {len(quotes)} coins."))
            return

        self.stdout.write(self.style.NOTICE("Ingesting cryptocurrency quotes from CoinGecko..."))
        publisher = get_user_model().objects.filter(is_superuser=True, is_active=True).first() or SystemPublisher
        try:
            result = CryptoMarketDataService.sync_prices(coin_ids=coin_ids, publisher=publisher)

            if result.get('errors'):
                for err in result['errors']:
                    self.stdout.write(self.style.WARNING(f"Warning: {err}"))

            self.stdout.write(self.style.SUCCESS(f"Successfully published {result['synced']} cryptocurrency observations."))
            if result['synced'] == 0 and result.get('errors'):
                sys.exit(1)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Price sync failed: {exc}"))
            sys.exit(1)
