"""
Management command to execute the Market Data Scheduler.
Supports continuous execution loop or a single run-through of due tasks.
"""
import sys
import time

from django.core.management.base import BaseCommand

from apps.market_data.services.scheduler_service import MarketDataSchedulerService


class Command(BaseCommand):
    help = 'Runs the market data scheduler for CoinGecko crypto and MFAPI mutual fund ingestion.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run all currently due jobs once and exit immediately.',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Poll interval in seconds when running in daemon loop (default: 60).',
        )
        parser.add_argument(
            '--job',
            type=str,
            help='Execute only a specific job name (e.g., crypto_prices, crypto_catalogue, mf_nav, mf_catalogue, health_check).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Execute job fetch/parse logic without committing changes to the database.',
        )

    def handle(self, *args, **options):
        once = options.get('once', False)
        poll_interval = options.get('interval', 60)
        specific_job = options.get('job')
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE: No persistent changes will be saved."))

        if specific_job:
            if specific_job not in MarketDataSchedulerService.JOBS:
                self.stderr.write(self.style.ERROR(
                    f"Invalid job '{specific_job}'. Available: {list(MarketDataSchedulerService.JOBS.keys())}"
                ))
                sys.exit(1)

            self.stdout.write(self.style.NOTICE(f"Executing single job '{specific_job}'..."))
            result = MarketDataSchedulerService.run_job(specific_job, dry_run=dry_run)
            if result.get('status') == 'FAILED':
                self.stderr.write(self.style.ERROR(f"Job failed: {result.get('error')}"))
                sys.exit(1)
            self.stdout.write(self.style.SUCCESS(f"Job completed: {result}"))
            return

        if once:
            self.stdout.write(self.style.NOTICE("Running all due market data jobs once..."))
            results = MarketDataSchedulerService.run_all_due_jobs(dry_run=dry_run)
            has_failures = any(res.get('status') == 'FAILED' for res in results.values())
            self.stdout.write(self.style.SUCCESS(f"Scheduler run finished: {results}"))
            if has_failures:
                sys.exit(1)
            return

        self.stdout.write(self.style.NOTICE(
            f"Starting Market Data Scheduler daemon (polling every {poll_interval}s)... Press Ctrl+C to stop."
        ))

        try:
            while True:
                results = MarketDataSchedulerService.run_all_due_jobs(dry_run=dry_run)
                for job_name, res in results.items():
                    if res.get('status') not in ('SKIPPED', 'LOCKED'):
                        self.stdout.write(f"[{job_name}] Result: {res}")
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nScheduler stopped by operator."))
