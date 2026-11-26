# End-to-End Workflow Audit and Implementation Record

Date: 2026-11-21  
Repository baseline: `Portfolio_manager(1).zip`  
Git HEAD at inspection: `897fd8e` (`update-market-catalogue`)  

## Scope and preservation

The complete repository archive was extracted with its Git metadata and existing working-tree changes intact. The working tree was already substantially modified before this implementation (340 modified tracked files and four untracked source/migration files at initial inspection). No reset, clean, checkout, or blanket patch overlay was performed. The candidate `Portfolio_manager_corrected_patch.zip` was inspected as a reference; it was not blindly applied.

The implementation retains the existing Django/DRF + PostgreSQL two-database architecture, React/TanStack Query frontend, model ownership registry, and existing naming conventions.

## Corrections implemented

### 1. Historical market-data look-ahead

**Root cause:** The single and bulk price resolvers bounded observations by `effective_at`, but did not bound them by `published_at`. A correction published after a historical `as_of` timestamp could therefore rewrite what the application reported as known at that earlier instant. The previous supersession exclusion also hid an original observation as soon as any published correction existed, regardless of when that correction became available.

**Correction:** Both resolver paths now require `published_at <= as_of` and only treat a correction as superseding its original when the correction itself was published by `as_of` and its effective time is within the requested effective-time boundary. This applies the same bitemporal cutoff to single and bulk resolution.

### 2. Explicit series selection

**Root cause:** An explicit `series_id` was still filtered by `InstrumentCoverage.price_type`, which is only the default selection policy. A caller selecting a valid non-default series could receive a false missing result.

**Correction:** An explicit series selection now overrides the coverage default price type. The resolver still scopes the series to the requested canonical instrument and active series; a caller-supplied `price_type` remains an explicit filter.

### 3. Concurrent publication and series-version integrity

**Root cause:** Publication incremented `MarketDataSeries.data_version` using a potentially stale in-memory series instance without locking the observation row. Concurrent publishers could race, duplicate work, or lose a version increment.

**Correction:** Publication now locks and re-reads the observation, validates its current lifecycle state under lock, locks the exact series row, increments its version from the locked database value, then writes the immutable published observation and durable publication event in the same secondary-database transaction. Repeated publication of an already-published row is idempotent. Inactive publishers are rejected.

`MarketDataSeries.save()` now rejects ordinary model-level changes to `data_version`; the publication lifecycle explicitly marks its version update as managed. The defensive direct-create publication path also uses the managed update guard.

### 4. Backfill-to-valuation amplification

**Root cause:** Every published historical observation emitted a durable event, and the worker refreshed every holding for every event. A five-year backfill could therefore trigger thousands of repeated recalculations for the same instrument.

**Correction:** The outbox worker now selects candidate instruments from a bounded event window, locks and processes up to 5,000 pending/failed events for each selected instrument as one group, refreshes that instrument's holdings once, and acknowledges the selected events together only after all holding refreshes succeed. The oldest event is used as a stable batch idempotency key, so a retry after partial primary-database success does not duplicate already-recorded valuation snapshots. Events beyond the per-instrument cap remain pending for a later run.

The holding refresh query now iterates in chunks of 100 rather than materializing every investment for an instrument into memory.

### 5. Backfill authorization, timestamps and duplicate detection

**Root cause:** The backfill service could fall back to the first user in the database as a publisher, even if that user was not authorized. Naive timestamps were interpreted using the host timezone, and duplicate detection issued one database existence query per provider observation. Mixed provider payloads could also be assigned to the first observation's series and fail partway through.

**Correction:** Backfill now selects only active superusers, staff or `MarketDataPublisher` group members and checks authorization before fetching or writing data. Financial values must be finite and positive. Naive provider timestamps are interpreted as Asia/Kolkata market-local timestamps. Observations are sorted chronologically. Mixed source/price-type/currency/unit payloads are rejected explicitly instead of being silently attached to an incompatible series. Existing published market dates are loaded in one bounded date-range query and tracked in memory, avoiding an existence query for every row and suppressing duplicates within the provider response.

The backfill management command now validates `--limit` and bounds `--target-days` to 1–36,500.

## Regression coverage added or corrected

- Historical `as_of` excludes a correction published later.
- Historical `as_of` excludes observations not yet published.
- Explicit series selection overrides the coverage default price type.
- Correction fixtures use the original observation's exact series identity, matching the production correction workflow.
- Publication is idempotent and advances the series data version exactly once.
- Direct model-level series version mutation is rejected.
- Multiple publication events for one instrument are coalesced into one holding refresh and acknowledged as a group.

## Verification results

| Check | Result | Details |
|---|---|---|
| Python syntax compilation | PASS | `python -m compileall -q backend` |
| Frontend TypeScript check | PASS | `cd frontend && npm run typecheck` |
| Targeted diff whitespace check | PASS | `git diff --check` on the eight implementation/test files |
| Backend pytest suite | BLOCKED | The archive contains a Windows virtual environment, not executable in this Linux runtime. Django is not installed in the available Linux interpreter. Dependency installation was attempted but package-index DNS/network access was unavailable. |
| Django system checks and migrations | BLOCKED | Require the unavailable Django runtime and configured databases. |
| Frontend Vitest suite | BLOCKED | Existing `node_modules` lacks the platform-specific optional dependency `@rollup/rollup-linux-x64-gnu`; the Vitest executable also lacks execute permission. Direct Node invocation confirms the missing module. |
| Frontend production build | BLOCKED | Vite cannot load Rollup because the same platform-specific optional dependency is missing. |

A passing syntax/type check is not represented as a passing runtime test. Backend integration, database locking, migrations and browser tests still require execution in the project's supported Windows/Linux CI environment with dependencies installed.

## Remaining verification and operational requirements

1. Run the complete backend pytest suite against both configured database aliases, preferably PostgreSQL for row-lock and trigger behavior.
2. Run `manage.py check`, `makemigrations --check --dry-run`, and forward migrations against both `default` and `market_data` in a disposable environment before production.
3. Run frontend `npm ci`, Vitest, and production build in a clean Linux CI runner so optional native dependencies are installed for the runner platform.
4. Exercise concurrent publication and outbox workers against PostgreSQL, not only SQLite or mocks.
5. Exercise a representative five-year backfill and confirm event coalescing, worker duration, provider limits, and valuation consistency using production-like data volumes.
6. Schedule `process_market_data_outboxes` at the intended cadence and monitor pending/failed event counts; failed events remain retryable and require operational alerting/reconciliation.

## Delivery notes

The final source archive excludes Git internals, local virtual environments, `node_modules`, build output, local SQLite databases, caches, and actual `.env` files. It retains `.env.example`, source, migrations, tests, documentation, package manifests and lockfiles. Existing user modifications are retained in the delivered source tree.
