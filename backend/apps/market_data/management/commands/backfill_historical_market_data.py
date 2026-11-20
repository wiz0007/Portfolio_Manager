from django.core.management.base import BaseCommand

from apps.market_data.models.instrument import Instrument, InstrumentStatus
from apps.market_data.services.backfill_service import HistoricalBackfillService


class Command(BaseCommand):
    help = 'Executes bounded, idempotent historical market data backfill for canonical instruments.'

    def add_arguments(self, parser):
        parser.add_argument('--symbols', type=str, help='Comma-separated list of symbols to backfill')
        parser.add_argument('--asset-class', type=str, help='Filter by asset class (EQUITY, INDEX, MUTUAL_FUND, COMMODITY, etc.)')
        parser.add_argument('--limit', type=int, default=0, help='Maximum number of instruments to process (0 = all)')
        parser.add_argument('--target-days', type=int, default=365, help='Target days of history (default: 365)')

    def handle(self, *args, **options):
        self.stdout.write("=" * 65)
        self.stdout.write("Starting Canonical Historical Market Data Backfill Pipeline")
        self.stdout.write("=" * 65)

        service = HistoricalBackfillService()
        qs = Instrument.objects.filter(status=InstrumentStatus.ACTIVE)

        if options.get('symbols'):
            syms = [s.strip().upper() for s in options['symbols'].split(',') if s.strip()]
            qs = qs.filter(symbol__in=syms)

        if options.get('asset_class'):
            qs = qs.filter(asset_class=options['asset_class'].upper())

        total = qs.count()
        limit = options.get('limit', 0)
        if limit > 0:
            qs = qs[:limit]
            self.stdout.write(f"Processing limited batch of {limit} instruments (out of {total} total)...")
        else:
            self.stdout.write(f"Processing all {total} eligible instruments...")

        target_days = options.get('target_days', 365)
        success_count = 0
        skipped_count = 0
        failed_count = 0
        total_points = 0

        for idx, inst in enumerate(qs, start=1):
            res = service.backfill_instrument(inst, target_days=target_days)
            status_str = res['status']
            if status_str == 'SUCCESS':
                success_count += 1
                total_points += res['points_added']
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[{idx}/{total}] {inst.symbol} ({inst.asset_class}): +{res['points_added']} points ({res['start_date']} to {res['end_date']})"
                    )
                )
            elif status_str == 'SKIPPED':
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"[{idx}/{total}] {inst.symbol}: Already covered ({res['reason']})"
                    )
                )
            else:
                failed_count += 1
                self.stdout.write(
                    self.style.NOTICE(
                        f"[{idx}/{total}] {inst.symbol}: {status_str} ({res.get('reason', '')})"
                    )
                )

        self.stdout.write("=" * 65)
        self.stdout.write(
            self.style.SUCCESS(
                f"BACKFILL COMPLETE: {success_count} backfilled (+{total_points} observations), {skipped_count} skipped, {failed_count} no-data/failed."
            )
        )
        self.stdout.write("=" * 65)
