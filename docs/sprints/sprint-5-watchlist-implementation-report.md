# Sprint 5 — Watchlist and Manual Market-Data Integration: Final Implementation Report

**Project:** Multi-Asset Portfolio Management Platform  
**Sprint:** 5 — Watchlist & Manual Market-Data Integration  
**Date:** 2026-11-17  
**Branch:** `sprint-5`  
**Status:** Complete & Fully Verified  

---

## 1. Executive Summary

Sprint 5 successfully introduces a dedicated **Personal Watchlist** feature enabling users to monitor canonical financial instruments independently of whether they hold them in a portfolio. 

Crucially, **no market prices are duplicated inside individual watchlist database records**. All watchlist items dynamically consume the centrally published, verified price observations through the shared `PriceResolver` service and calculate price movement via `PriceMovementService` using backend decimal-safe arithmetic.

All backend tests (184 passed), frontend tests (134 passed across 40 suites), Django database checks/migrations, and production bundle builds pass with zero errors.

---

## 2. Requirement-to-Code Correction Matrix

| Requirement | Specification | Implementation in Codebase | Test Verification |
|---|---|---|---|
| **3.1 Watchlist Model** | User-specific watchlist items linked to canonical instruments. | `WatchlistItem` model in `apps/watchlists/models.py`. | `TestWatchlistModelAndConstraints::test_create_watchlist_item_success` |
| **3.1 DB Uniqueness** | Prevent duplicate instrument per user at database level. | `UniqueConstraint(fields=['user', 'instrument'], name='unique_user_instrument_watchlist')`. | `TestWatchlistModelAndConstraints::test_duplicate_user_instrument_constraint_rejected` |
| **3.1 Isolation & Independence** | Removing watchlist item never mutates instruments or investments. | Clean CASCADE on user/instrument FK; no hooks or cascades into investments. | `TestWatchlistModelAndConstraints::test_remove_item_preserves_canonical_instrument`, `test_remove_item_preserves_user_investments_and_transactions` |
| **3.2 Catalogue Search** | Search canonical catalogue across name, symbol, ISIN, scheme code, exchange, sector, industry. | `InstrumentSearchService.search()` in `apps/market_data/services/search_service.py` filtering `status=ACTIVE, is_active=True`. | `TestInstrumentAPI::test_ins_002_fuzzy_search_instruments` |
| **3.3 Watchlist Overview** | Display symbol, name, latest resolved price, 24h change, freshness status, provenance. | `WatchlistService.list_items()` with `PriceResolver` and `PriceMovementService` annotations. | `TestWatchlistAPILifecycle::test_add_to_watchlist_lifecycle`, `WatchlistPage Lifecycle` |
| **3.4 Price Movement** | Decimal-safe arithmetic for price and percentage change; return explicit `UNAVAILABLE` when prior is missing or zero. | `PriceMovementService` in `apps/market_data/services/movement_service.py`. | `TestPriceMovementService::test_positive_price_movement_calculation`, `test_zero_base_price_handled_safely`, `test_currency_mismatch_rejected` |
| **3.5 Instrument Detail & History** | Detail page with interactive period chart (1D, 1W, 1M, 3M, 6M, 1Y, ALL) and policy info. | `InstrumentDetailPage.tsx`, `InstrumentPriceChart.tsx`, and `MarketHistoryService`. | `TestMarketHistoryServiceAndEndpoints::test_chronological_ordering_and_filtering`, `test_instrument_market_data_history_endpoint` |
| **4.1 Shared Price Resolver** | Watchlist and valuation share exact same market price resolver without duplicate pricing logic. | Direct call to `PriceResolver.resolve_price(item.instrument)` in `WatchlistService`. | `test_add_to_watchlist_lifecycle` |
| **4.2 Freshness & Provenance** | Distinguish AVAILABLE, STALE, MISSING, SYNTHETIC, AWAITING_VERIFICATION. | `PriceFreshnessBadge.tsx` and `market_data_status` endpoint. | `PriceFreshnessBadge::renders Verified badge...`, `test_instrument_market_data_status_endpoint` |
| **7.0 Cache Management** | Coordinated TanStack Query invalidation on add/remove. | `WATCHLIST_QUERY_KEYS` in `useWatchlist.ts` with invalidation of `['watchlist']`. | `WatchlistPage Lifecycle` |

---

## 3. Database Architecture & Migrations

### Model: `WatchlistItem` (`apps/watchlists/models.py`)
- `id`: UUID (Primary Key)
- `user`: ForeignKey to `AUTH_USER_MODEL` (`on_delete=models.CASCADE`, `related_name='watchlist_items'`)
- `instrument`: ForeignKey to `market_data.Instrument` (`on_delete=models.CASCADE`, `related_name='watched_by'`)
- `notes`: `models.TextField(blank=True, default='')`
- `target_price`: `models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)`
- `created_at`: `models.DateTimeField(auto_now_add=True, db_index=True)`
- `updated_at`: `models.DateTimeField(auto_now=True)`
- Database Constraints:
  - `models.UniqueConstraint(fields=['user', 'instrument'], name='unique_user_instrument_watchlist')`
- Indexes:
  - `watchlist_user_created_idx`: `['user', '-created_at']`
  - `watchlist_inst_idx`: `['instrument']`

### Migration:
- Generated: `backend/apps/watchlists/migrations/0001_initial.py`
- Consistency Verified: `python manage.py makemigrations --check --dry-run` reports **No changes detected**.

---

## 4. API Endpoints

### 4.1 Watchlists (`/api/v1/watchlist/`)
- `GET /api/v1/watchlist/`: Returns all watchlist items belonging to `request.user`, annotated with live `market_data` (price, currency, unit, freshness status, source, provenance, notes) and `movement` (change amount, change percent, prior price, prior timestamp).
- `POST /api/v1/watchlist/`: Adds canonical instrument to user watchlist (`instrument_id`, optional `notes`, optional `target_price`). Enforces instrument active status and uniqueness.
- `GET /api/v1/watchlist/{id}/`: Retrieves single item for `request.user`.
- `DELETE /api/v1/watchlist/{id}/`: Removes watchlist item.

### 4.2 Instrument Market-Data Sub-endpoints (`/api/v1/instruments/{id}/`)
- `GET /api/v1/instruments/{id}/market-data/latest/`: Returns authoritative resolved price and calculated 24h session movement.
- `GET /api/v1/instruments/{id}/market-data/history/`: Returns bounded, chronologically sorted historical market observations (`period=1D|1W|1M|3M|6M|1Y|ALL`), rejecting future bounds.
- `GET /api/v1/instruments/{id}/market-data/status/`: Returns coverage configuration, freshness threshold hours, last publication date, and staleness indicator.

---

## 5. Frontend Architecture

### Components (`frontend/src/features/watchlists/`)
- `components/WatchlistTable.tsx`: Tabular layout for desktop (`hidden md:block`) with symbol, market, latest price, 24h movement, freshness badge, target alert, and quick action buttons.
- `components/WatchlistCard.tsx`: Touch-friendly card view for mobile devices (`block md:hidden`).
- `components/AddToWatchlistModal.tsx`: Search and add modal embedding `InstrumentSearch`, note input, target price alert, and error handling.
- `components/PriceFreshnessBadge.tsx`: Visual and accessible indicator for `AVAILABLE`, `STALE`, `MISSING`, `SYNTHETIC`, `AWAITING_VERIFICATION`, `UNSUPPORTED`.
- `components/PriceMovement.tsx`: Positive/negative/neutral price movement formatted with currency symbols and accessible ARIA attributes.
- `components/InstrumentPriceChart.tsx`: SVG timeseries chart with 1D, 1W, 1M, 3M, 6M, 1Y, and ALL period selection, summary metrics bar (Open, High, Low, Net Change), and explicit handling of unsupported/empty history.
- `components/WatchlistEmptyState.tsx`: Empty state with guidance and direct "Add Instrument" action.

### Pages & Routes
- `pages/WatchlistPage.tsx`: Mounted at `/watchlist`. Includes header with live summary statistics (Watched Assets, 24h Gainers, 24h Decliners, Target Alerts), search filter, asset class chips, and table/card rendering.
- `pages/InstrumentDetailPage.tsx`: Mounted at `/instruments/:id` and `/watchlist/instruments/:id`. Displays canonical identifiers, coverage policy metadata, interactive historical chart, Watchlist add/remove toggle, and direct "Add to Portfolio" CTA.

---

## 6. Automated Test Execution Results

### 6.1 Backend Test Results (`pytest backend`)
- **Total Tests Passed:** 184 / 184 (100%)
- **Execution Time:** ~6.0s
- **Key Test Suites:**
  - `apps/watchlists/tests/test_watchlist_domain.py`: 10 tests covering model uniqueness, cascade safety, investment independence, target price validation, API lifecycle, unauthenticated rejection, and cross-user 404 isolation.
  - `apps/market_data/tests/test_price_movement_service.py`: 5 tests covering positive, negative, zero base, currency mismatch, and missing baseline calculations.
  - `apps/market_data/tests/test_market_history_service.py`: 5 tests covering chronological ordering, future date rejection, and `/market-data/` sub-endpoints.
  - `apps/market_data/tests/test_manual_market_operations.py`: 10 tests covering operator worklists, CSV preview/commit, and price observation review.
  - `apps/valuation/tests/`: 26 tests covering valuation strategies and projection schedules.
  - Sprints 1–4 regression suites: All 128 existing tests passing without regression.

### 6.2 Frontend Test Results (`vitest run`)
- **Total Test Files Passed:** 40 / 40 (100%)
- **Total Tests Passed:** 134 / 134 (100%)
- **New Test Files:**
  - `src/features/watchlists/tests/watchlistLifecycle.test.tsx`: 4 tests verifying summary cards, empty state, search filtering, and add modal opening.
  - `src/features/watchlists/tests/watchlistComponents.test.tsx`: 9 tests verifying freshness badges, decimal formatting, positive/negative signs, chart metrics, and unsupported history messaging.

### 6.3 Code Quality & Build Checks
- `ruff check backend`: 0 errors (All checks passed).
- `python manage.py check`: 0 issues identified.
- `python manage.py makemigrations --check --dry-run`: No changes detected.
- `npm run typecheck --prefix frontend` (`tsc --noEmit`): 0 errors.
- `npm run build --prefix frontend` (`tsc -b && vite build`): Succeeded in 11.22s.
