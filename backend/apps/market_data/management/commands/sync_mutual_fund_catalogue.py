"""Management command to synchronize Indian mutual fund scheme catalogue from MFAPI."""
from django.core.management.base import BaseCommand

from apps.market_data.services.mutual_fund_service import MutualFundMarketDataService


class Command(BaseCommand):
    help = 'Synchronizes curated Indian mutual fund schemes into canonical instruments and mappings.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Synchronizing Indian mutual fund catalogue..."))
        result = MutualFundMarketDataService.sync_catalogue()
        self.stdout.write(self.style.SUCCESS(
            f"Mutual fund catalogue synchronized: {result['total_synced']} schemes "
            f"({result['created']} created, {result['updated']} updated)."
        ))
