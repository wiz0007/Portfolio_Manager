"""Management command to fetch and publish current cryptocurrency prices from CoinGecko."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.market_data.services.crypto_service import CryptoMarketDataService


class Command(BaseCommand):
    help = 'Fetches current cryptocurrency quotes from CoinGecko and stores published observations.'

    def add_arguments(self, parser):
        parser.add_argument('--coins', type=str, help='Comma-separated list of CoinGecko coin IDs (e.g. bitcoin,ethereum)')

    def handle(self, *args, **options):
        coins_arg = options.get('coins')
        coin_ids = [c.strip().lower() for c in coins_arg.split(',') if c.strip()] if coins_arg else None

        self.stdout.write(self.style.NOTICE("Ingesting cryptocurrency quotes from CoinGecko..."))
        publisher = get_user_model().objects.filter(is_superuser=True, is_active=True).first()
        result = CryptoMarketDataService.sync_prices(coin_ids=coin_ids, publisher=publisher)

        if result.get('errors'):
            for err in result['errors']:
                self.stdout.write(self.style.WARNING(f"Warning: {err}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully published {result['synced']} cryptocurrency observations."))
