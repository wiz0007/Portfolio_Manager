"""Management command to synchronize cryptocurrency catalogue from CoinGecko."""
import sys

from django.core.management.base import BaseCommand

from apps.market_data.services.crypto_service import CryptoMarketDataService


class Command(BaseCommand):
    help = 'Synchronizes supported cryptocurrency catalogue into canonical instruments and mappings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-provider',
            action='store_true',
            help='Fetch fresh catalogue directly from CoinGecko API instead of default curated list.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of coins processed from the catalogue.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate catalogue fetch without persisting instruments to the database.',
        )

    def handle(self, *args, **options):
        from_provider = options.get('from_provider', False)
        limit = options.get('limit')
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: Simulating cryptocurrency catalogue sync..."))
            coins = CryptoMarketDataService.fetch_provider_catalogue()
            if limit:
                coins = coins[:limit]
            self.stdout.write(self.style.SUCCESS(f"Dry run complete: Found {len(coins)} coins from CoinGecko."))
            return

        self.stdout.write(self.style.NOTICE("Synchronizing cryptocurrency catalogue..."))
        try:
            result = CryptoMarketDataService.sync_catalogue(from_provider=from_provider)
            self.stdout.write(self.style.SUCCESS(
                f"Crypto catalogue synchronized: {result.get('total_synced', 0)} instruments "
                f"({result.get('created', 0)} created, {result.get('updated', 0)} updated)."
            ))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Catalogue synchronization failed: {exc}"))
            sys.exit(1)
