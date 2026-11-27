"""Management command to backfill historical cryptocurrency prices from CoinGecko."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.market_data.services.crypto_service import CryptoMarketDataService


class Command(BaseCommand):
    help = 'Backfills historical price observations for a cryptocurrency from CoinGecko.'

    def add_arguments(self, parser):
        parser.add_argument('coin_id', type=str, help='CoinGecko coin ID (e.g. bitcoin, ethereum)')
        parser.add_argument('--days', type=int, default=30, help='Number of days of history to backfill (default: 30)')

    def handle(self, *args, **options):
        coin_id = options['coin_id'].strip().lower()
        days = options['days']

        self.stdout.write(self.style.NOTICE(f"Backfilling {days} days of history for {coin_id}..."))
        publisher = get_user_model().objects.filter(is_superuser=True, is_active=True).first()

        try:
            count = CryptoMarketDataService.backfill_history(coin_id=coin_id, days=days, publisher=publisher)
            self.stdout.write(self.style.SUCCESS(f"Successfully backfilled {count} observations for {coin_id}."))
        except Exception as e:
            raise CommandError(f"Backfill failed: {e!s}") from e
