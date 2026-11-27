"""Management command to fetch and publish current Indian mutual fund NAVs from MFAPI."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.market_data.services.mutual_fund_service import MutualFundMarketDataService


class Command(BaseCommand):
    help = 'Fetches latest NAVs for Indian mutual fund schemes from MFAPI and stores published observations.'

    def add_arguments(self, parser):
        parser.add_argument('--schemes', type=str, help='Comma-separated list of scheme codes (e.g. 122639,118834)')

    def handle(self, *args, **options):
        schemes_arg = options.get('schemes')
        scheme_codes = [s.strip() for s in schemes_arg.split(',') if s.strip()] if schemes_arg else None

        self.stdout.write(self.style.NOTICE("Ingesting mutual fund NAVs from MFAPI..."))
        publisher = get_user_model().objects.filter(is_superuser=True, is_active=True).first()
        result = MutualFundMarketDataService.sync_nav(scheme_codes=scheme_codes, publisher=publisher)

        if result.get('errors'):
            for err in result['errors']:
                self.stdout.write(self.style.WARNING(f"Warning: {err}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully published {result['synced']} mutual fund NAV observations."))
