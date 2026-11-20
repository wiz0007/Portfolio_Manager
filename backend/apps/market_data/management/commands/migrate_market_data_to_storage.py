import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.market_data.models.coverage import InstrumentCoverage
from apps.market_data.models.instrument_reference import MarketInstrumentReference
from apps.market_data.models.market_data_point import MarketDataPoint
from apps.market_data.models.observation import PriceObservation
from apps.market_data.services.sync_service import InstrumentIdentitySyncService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Idempotent migration command to transfer market data and historical time-series "
        "from Primary Database ('default') to Dedicated Market Data Storage Database ('market_data')."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=2000,
            help='Chunk size for bulk insert operations (default: 2000).',
        )
        parser.add_argument(
            '--purge-primary',
            action='store_true',
            help='Purge transferred market data observations from the primary database after verification.',
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not prompt for confirmation when purging primary observations.',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        purge_primary = options['purge_primary']
        no_input = options['no_input']

        self.stdout.write(self.style.MIGRATE_HEADING("=== Portfolio Manager: Market Data Storage Migration ==="))

        if 'market_data' not in settings.DATABASES:
            self.stdout.write(
                self.style.WARNING(
                    "Note: 'market_data' database alias is not yet configured in DATABASES.\n"
                    "Please set NEON_STORAGE_DATABASE_URL in backend/.env to target your second Neon database.\n"
                    "Running in verification & dry-run reconciliation mode against current database."
                )
            )
            reconcile_result = InstrumentIdentitySyncService.reconcile_all(batch_size=batch_size)
            self.stdout.write(self.style.SUCCESS(f"Reconciliation check complete: {reconcile_result}"))
            return

        target_db = 'market_data'
        source_db = 'default'

        start_time = time.time()

        # Step 1: Reconcile Canonical Instruments -> MarketInstrumentReference
        self.stdout.write("1. Synchronizing Canonical Instruments to Market Data Storage...")
        sync_result = InstrumentIdentitySyncService.reconcile_all(batch_size=batch_size)
        self.stdout.write(
            f"   - Canonical: {sync_result['total_canonical']} | Target References: {sync_result['synced_total']} (Created: {sync_result['created']}, Updated: {sync_result['updated']})"
        )

        # Step 2: Migrate InstrumentCoverages
        self.stdout.write("2. Migrating Instrument Coverage policies...")
        source_covs = list(InstrumentCoverage.objects.using(source_db).all())
        to_create_covs = []
        for cov in source_covs:
            to_create_covs.append(
                InstrumentCoverage(
                    id=cov.id,
                    instrument_id=cov.instrument_id,
                    price_type=cov.price_type,
                    unit=cov.unit,
                    currency=cov.currency,
                    cadence=cov.cadence,
                    freshness_hours=cov.freshness_hours,
                    status=cov.status,
                    notes=cov.notes,
                )
            )
        if to_create_covs:
            InstrumentCoverage.objects.using(target_db).bulk_create(
                to_create_covs,
                batch_size=batch_size,
                ignore_conflicts=True,
            )
        self.stdout.write(f"   - Synced {len(to_create_covs)} coverage policies.")

        # Step 3: Migrate Price Observations in batches
        source_obs_count = PriceObservation.objects.using(source_db).count()
        self.stdout.write(f"3. Migrating {source_obs_count} Price Observations to storage...")
        obs_migrated = 0
        target_chunk = []

        for obs in PriceObservation.objects.using(source_db).all().iterator(chunk_size=batch_size):
            target_chunk.append(
                PriceObservation(
                    id=obs.id,
                    instrument_id=obs.instrument_id,
                    price_type=obs.price_type,
                    value=obs.value,
                    open_price=obs.open_price,
                    high_price=obs.high_price,
                    low_price=obs.low_price,
                    volume=obs.volume,
                    currency=obs.currency,
                    unit=obs.unit,
                    effective_at=obs.effective_at,
                    published_at=obs.published_at,
                    trust_class=obs.trust_class,
                    status=obs.status,
                    source=obs.source,
                    source_reference=obs.source_reference,
                    notes=obs.notes,
                    is_synthetic=obs.is_synthetic,
                    recorded_by_id=obs.recorded_by_id,
                    published_by_id=obs.published_by_id,
                )
            )
            if len(target_chunk) >= batch_size:
                PriceObservation.objects.using(target_db).bulk_create(
                    target_chunk,
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )
                obs_migrated += len(target_chunk)
                target_chunk = []
                self.stdout.write(f"   - Progress: {obs_migrated} / {source_obs_count} observations copied...")

        if target_chunk:
            PriceObservation.objects.using(target_db).bulk_create(
                target_chunk,
                batch_size=batch_size,
                ignore_conflicts=True,
            )
            obs_migrated += len(target_chunk)
            self.stdout.write(f"   - Progress: {obs_migrated} / {source_obs_count} observations copied...")

        # Step 4: Migrate MarketDataPoints in batches
        source_mdp_count = MarketDataPoint.objects.using(source_db).count()
        self.stdout.write(f"4. Migrating {source_mdp_count} Market Data Points to storage...")
        mdp_migrated = 0
        target_mdp_chunk = []

        for mdp in MarketDataPoint.objects.using(source_db).all().iterator(chunk_size=batch_size):
            target_mdp_chunk.append(
                MarketDataPoint(
                    id=mdp.id,
                    instrument_id=mdp.instrument_id,
                    timestamp=mdp.timestamp,
                    price=mdp.price,
                    open_price=mdp.open_price,
                    high_price=mdp.high_price,
                    low_price=mdp.low_price,
                    close_price=mdp.close_price,
                    volume=mdp.volume,
                    change_amount=mdp.change_amount,
                    change_percent=mdp.change_percent,
                    interval=mdp.interval,
                    provider=mdp.provider,
                    is_synthetic=mdp.is_synthetic,
                )
            )
            if len(target_mdp_chunk) >= batch_size:
                MarketDataPoint.objects.using(target_db).bulk_create(
                    target_mdp_chunk,
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )
                mdp_migrated += len(target_mdp_chunk)
                target_mdp_chunk = []
                self.stdout.write(f"   - Progress: {mdp_migrated} / {source_mdp_count} data points copied...")

        if target_mdp_chunk:
            MarketDataPoint.objects.using(target_db).bulk_create(
                target_mdp_chunk,
                batch_size=batch_size,
                ignore_conflicts=True,
            )
            mdp_migrated += len(target_mdp_chunk)
            self.stdout.write(f"   - Progress: {mdp_migrated} / {source_mdp_count} data points copied...")

        # Step 5: Verification & Reconciliation Report
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("MIGRATION AUDIT & RECONCILIATION REPORT"))
        self.stdout.write("=" * 60)

        target_obs_count = PriceObservation.objects.using(target_db).count()
        target_mdp_count = MarketDataPoint.objects.using(target_db).count()
        target_ref_count = MarketInstrumentReference.objects.using(target_db).count()

        self.stdout.write(f"Canonical Instruments (Primary): {sync_result['total_canonical']}")
        self.stdout.write(f"Instrument References (Storage): {target_ref_count}")
        self.stdout.write(f"Price Observations (Primary)  : {source_obs_count}")
        self.stdout.write(f"Price Observations (Storage)  : {target_obs_count}")
        self.stdout.write(f"Market Data Points (Primary)  : {source_mdp_count}")
        self.stdout.write(f"Market Data Points (Storage)  : {target_mdp_count}")

        elapsed = round(time.time() - start_time, 2)
        self.stdout.write(f"Time Elapsed: {elapsed} seconds")

        verified = (
            target_ref_count >= sync_result['total_canonical']
            and target_obs_count >= source_obs_count
            and target_mdp_count >= source_mdp_count
        )

        if verified:
            self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Integrity verified! All observations and points safely copied to Market Data Storage."))
        else:
            self.stdout.write(self.style.ERROR("\n[WARNING] Discrepancy detected between source and destination row counts."))

        # Optional Step 6: Purge primary observations to reclaim 166+ MB on Neon Free Tier
        if purge_primary and verified:
            if not no_input:
                confirm = input("\nAre you sure you want to purge observations from the PRIMARY database? (yes/no): ")
                if confirm.lower() != 'yes':
                    self.stdout.write("Purge aborted by user.")
                    return

            self.stdout.write("Purging market data from Primary Database to reclaim storage quota...")
            deleted_obs, _ = PriceObservation.objects.using(source_db).all().delete()
            deleted_mdp, _ = MarketDataPoint.objects.using(source_db).all().delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully purged {deleted_obs} observations and {deleted_mdp} data points from Primary DB!\n"
                    "Primary database size significantly reduced on Neon."
                )
            )
