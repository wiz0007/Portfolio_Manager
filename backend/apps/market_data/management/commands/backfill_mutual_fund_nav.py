"""Management command to backfill historical NAVs for an Indian mutual fund scheme from MFAPI."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.market_data.services.mutual_fund_service import MutualFundMarketDataService


class Command(BaseCommand):
    help = 'Backfills historical NAV observations for an Indian mutual fund scheme from MFAPI.'

    def add_arguments(self, parser):
        parser.add_argument('scheme_code', type=str, help='AMFI scheme code (e.g. 122639)')
        parser.add_argument('--days', type=int, default=90, help='Number of daily NAV records to backfill (default: 90)')

    def handle(self, *args, **options):
        scheme_code = options['scheme_code'].strip()
        days = options['days']

        self.stdout.write(self.style.NOTICE(f"Backfilling {days} days of NAV history for scheme {scheme_code}..."))
        publisher = get_user_model().objects.filter(is_superuser=True, is_active=True).first()

        try:
            count = MutualFundMarketDataService.backfill_history(scheme_code=scheme_code, days=days, publisher=publisher)
            self.stdout.write(self.style.SUCCESS(f"Successfully backfilled {count} NAV observations for scheme {scheme_code}."))
        except Exception as e:
            raise CommandError(f"NAV backfill failed: {e!s}") from e
