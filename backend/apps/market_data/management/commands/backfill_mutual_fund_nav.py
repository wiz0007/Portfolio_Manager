"""Management command to backfill historical NAVs for an Indian mutual fund scheme from MFAPI."""
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.market_data.services.mutual_fund_service import MutualFundMarketDataService
from apps.market_data.services.system_publisher import SystemPublisher


class Command(BaseCommand):
    help = 'Backfills historical NAV observations for an Indian mutual fund scheme from MFAPI.'

    def add_arguments(self, parser):
        parser.add_argument('scheme_code', type=str, help='AMFI scheme code (e.g. 122639)')
        parser.add_argument('--days', type=int, default=90, help='Number of daily NAV records to backfill (default: 90, max: 3650)')
        parser.add_argument('--dry-run', action='store_true', help='Fetch historical NAVs without persisting.')

    def handle(self, *args, **options):
        scheme_code = options['scheme_code'].strip()
        days = options['days']
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING(f"DRY RUN: Fetching historical NAVs for scheme {scheme_code}..."))
            from apps.market_data.providers.mfapi.client import MFAPIClient
            _meta, data = MFAPIClient.get_scheme_history(scheme_code)
            self.stdout.write(self.style.SUCCESS(f"Dry run complete: Retrieved {len(data)} historical points for {scheme_code}."))
            return

        self.stdout.write(self.style.NOTICE(f"Backfilling {days} days of NAV history for scheme {scheme_code}..."))
        publisher = get_user_model().objects.filter(is_superuser=True, is_active=True).first() or SystemPublisher

        try:
            count = MutualFundMarketDataService.backfill_history(scheme_code=scheme_code, days=days, publisher=publisher)
            self.stdout.write(self.style.SUCCESS(f"Successfully backfilled {count} NAV observations for scheme {scheme_code}."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"NAV backfill failed: {e!s}"))
            sys.exit(1)
