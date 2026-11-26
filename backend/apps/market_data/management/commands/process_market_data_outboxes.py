from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from apps.market_data.services.sync_service import InstrumentIdentitySyncService
from apps.valuation.services.refresh_service import ValuationRefreshService


class Command(BaseCommand):
    help = (
        'Process durable primary instrument-sync and secondary publication outboxes. '
        'Schedule this command periodically (for example, once per minute).'
    )

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)
        parser.add_argument('--skip-sync', action='store_true')
        parser.add_argument('--skip-valuations', action='store_true')

    def handle(self, *args, **options):
        limit = options['limit']
        if limit < 1 or limit > 1000:
            raise CommandError('--limit must be between 1 and 1000')

        for alias in ('default', 'market_data'):
            if alias not in connections:
                raise CommandError(f'Required database alias {alias!r} is not configured.')
            connections[alias].ensure_connection()

        sync = {'processed': 0, 'failed': 0}
        valuation = {'processed': 0, 'failed': 0}
        if not options['skip_sync']:
            sync = InstrumentIdentitySyncService.process_pending_sync_events(limit=limit)
        if not options['skip_valuations']:
            valuation = ValuationRefreshService.process_pending_publication_events(limit=limit)

        self.stdout.write(self.style.SUCCESS(
            f"Instrument sync: {sync['processed']} processed, {sync['failed']} failed | "
            f"Valuation publications: {valuation['processed']} processed, {valuation['failed']} failed"
        ))
        if sync['failed'] or valuation['failed']:
            self.stderr.write(self.style.WARNING('Some outbox events remain failed and will be retried.'))
