from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Retired legacy migration command. The old count-only copy/purge routine is unsafe '
        'for the series-aware, two-database schema.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=2000)
        parser.add_argument('--purge-primary', action='store_true')
        parser.add_argument('--no-input', action='store_true')

    def handle(self, *args, **options):
        if options.get('purge_primary'):
            raise CommandError(
                '--purge-primary is permanently disabled. Count-based verification is not sufficient '
                'to prove series, provenance, correction and outbox integrity.'
            )
        raise CommandError(
            'This legacy migration command is retired and performs no writes. '
            'Apply the database migrations separately to default and market_data, then run '
            'process_market_data_outboxes and the documented row-level reconciliation procedure. '
            'Do not delete primary records until a separately reviewed migration has verified every row.'
        )
