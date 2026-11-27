"""Management command to synchronize cryptocurrency catalogue from CoinGecko."""
from django.core.management.base import BaseCommand

from apps.market_data.services.crypto_service import CryptoMarketDataService


class Command(BaseCommand):
    help = 'Synchronizes supported cryptocurrency catalogue into canonical instruments and mappings.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Synchronizing cryptocurrency catalogue..."))
        result = CryptoMarketDataService.sync_catalogue()
        self.stdout.write(self.style.SUCCESS(
            f"Crypto catalogue synchronized: {result['total_synced']} instruments "
            f"({result['created']} created, {result['updated']} updated)."
        ))
