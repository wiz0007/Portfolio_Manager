"""Management command to synchronize Indian mutual fund scheme catalogue from MFAPI."""
import sys

from django.core.management.base import BaseCommand

from apps.market_data.services.mutual_fund_service import MutualFundMarketDataService


class Command(BaseCommand):
    help = 'Synchronizes Indian mutual fund schemes into canonical instruments and mappings.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-provider',
            action='store_true',
            help='Synchronize full catalogue from MFAPI rather than the curated active set.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of schemes synchronized.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate scheme catalogue fetch without writing to the database.',
        )

    def handle(self, *args, **options):
        from_provider = options.get('from_provider', False)
        limit = options.get('limit')
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: Fetching mutual fund scheme catalogue..."))
            schemes = MutualFundMarketDataService.fetch_provider_catalogue()
            if limit:
                schemes = schemes[:limit]
            self.stdout.write(self.style.SUCCESS(f"Dry run complete: Found {len(schemes)} schemes from MFAPI."))
            return

        self.stdout.write(self.style.NOTICE("Synchronizing Indian mutual fund catalogue..."))
        try:
            result = MutualFundMarketDataService.sync_catalogue(from_provider=from_provider)
            self.stdout.write(self.style.SUCCESS(
                f"Mutual fund catalogue synchronized: {result.get('total_synced', 0)} schemes "
                f"({result.get('created', 0)} created, {result.get('updated', 0)} updated)."
            ))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Mutual fund catalogue synchronization failed: {exc}"))
            sys.exit(1)
