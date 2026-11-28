"""Management command to fetch and publish current Indian mutual fund NAVs from MFAPI."""
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.market_data.services.mutual_fund_service import MutualFundMarketDataService
from apps.market_data.services.system_publisher import SystemPublisher


class Command(BaseCommand):
    help = 'Fetches latest NAVs for Indian mutual fund schemes from MFAPI and stores published observations.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--schemes',
            type=str,
            help='Comma-separated list of scheme codes (e.g. 122639,118834)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of schemes to sync.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Fetch and parse NAVs without persisting to the database.',
        )

    def handle(self, *args, **options):
        schemes_arg = options.get('schemes')
        limit = options.get('limit')
        dry_run = options.get('dry_run', False)

        scheme_codes = [s.strip() for s in schemes_arg.split(',') if s.strip()] if schemes_arg else None
        if scheme_codes and limit:
            scheme_codes = scheme_codes[:limit]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: Fetching mutual fund NAVs without saving observations..."))
            from apps.market_data.providers.mfapi.client import MFAPIClient
            codes_to_test = scheme_codes or ['122639', '118834']
            count = 0
            client = MFAPIClient()
            for code in codes_to_test:
                nav_data = client.get_scheme(code)
                if nav_data:
                    count += 1
            self.stdout.write(self.style.SUCCESS(f"Dry run complete: Retrieved NAVs for {count} schemes."))
            return

        self.stdout.write(self.style.NOTICE("Ingesting mutual fund NAVs from MFAPI..."))
        publisher = get_user_model().objects.filter(is_superuser=True, is_active=True).first() or SystemPublisher
        try:
            result = MutualFundMarketDataService.sync_nav(scheme_codes=scheme_codes, publisher=publisher)

            if result.get('errors'):
                for err in result['errors']:
                    self.stdout.write(self.style.WARNING(f"Warning: {err}"))

            self.stdout.write(self.style.SUCCESS(f"Successfully published {result['synced']} mutual fund NAV observations."))
            if result['synced'] == 0 and result.get('errors'):
                sys.exit(1)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"NAV synchronization failed: {exc}"))
            sys.exit(1)
