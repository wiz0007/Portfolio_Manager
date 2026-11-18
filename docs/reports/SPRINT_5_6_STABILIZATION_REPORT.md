# Sprint 5 & 6 Stabilization, Financial Data Integrity and Performance Optimization Report

**Project:** Multi-Asset Portfolio Management Platform  
**Scope:** Sprint 5 (Watchlist & Manual Market-Data Integration) & Sprint 6 (Portfolio Dashboard Integration)  
**Branch:** `sprint-5-6-stabilization`  
**Execution Date:** November 18, 2026  
**Status:** Complete & Fully Verified  

---

## 1. Executive Summary

During this stabilization and hardening phase, we completed a comprehensive audit and resolution pass covering manual market pricing, watchlist monitoring, portfolio dashboard aggregation, data integrity, and performance bottlenecks across Sprint 5 and Sprint 6. 

Key architectural achievements:
1. **Canonical Market-Price Data Contract**: Upgraded `PriceResolver` to expose authoritative timestamps (`published_at`), explicit price types (`price_type`), relative age (`age_seconds`), coverage-aware defaults, and proper `AWAITING_VERIFICATION` classification. Superseded observations (those corrected via published corrections) are strictly excluded from resolution.
2. **Observation Security & Append-Only Governance**: Enforced append-only observation lifecycle by rejecting direct mutations (`PUT`/`PATCH` return `405 Method Not Allowed`) and prohibiting deletion of published observations (`DELETE` returns `400 Bad Request`). Included `MarketDataPublisher` permissions in query scopes. Atomic publishing with post-commit failure-isolated valuation refreshes was established.
3. **CSV Import Sanitization & Server-Side Batches**: Eliminated cell stripping of negative numbers in `clean_cell()` and implemented server-persisted preview batches (`PriceImportBatch`) in `commit_batch()`, preventing client manipulation of parsed rows.
4. **Historical Price Service Integrity**: Removed arbitrary 5-year bounds on `ALL` periods, resolving dynamically to earliest eligible observations, filtering superseded corrections, and enforcing ISO date query validation.
5. **Watchlist Concurrency & Integrity**: Eliminated race-condition crashes on duplicate watchlist addition via atomic `get_or_create` and `IntegrityError` handling, added positive target-price enforcement, and integrated canonical market-data freshness.
6. **Dashboard Financial Correctness & N+1 Elimination**: Replaced row-by-row price lookups and valuation existence checks with `PriceResolver.resolve_prices_bulk()` and prefetched valuations. Implemented database-side pagination on `/api/v1/dashboard/holdings/` and fixed missing valuation snapshots to return `valuation_date=None` rather than falling back to `Investment.updated_at`.
7. **Frontend Presentation & Cache Management**: Upgraded watchlist tables and preview cards to display `Session Movement` and relative freshness age (`Updated 2 hours ago`), removed hardcoded `₹` defaults for multi-currency compatibility, and added consolidated cache invalidation for TanStack Query.

---

## 2. Requirement-to-Code Correction Matrix

| Category | Defect / Gap Identified | Architectural Correction | Code Location | Status |
|---|---|---|---|---|
| **Price Resolver** | Missing `published_at`, `price_type`, `age_seconds`; superseded observations returned | Expose authoritative fields, calculate age, exclude `.exclude(corrections__status=ObservationStatus.PUBLISHED)` | `backend/apps/market_data/services/price_resolver.py` | Verified |
| **Price Resolver** | Missing price returned current UTC time as effective date | Return `effective_at=None` and `published_at=None` when no observation exists | `backend/apps/market_data/services/price_resolver.py` | Verified |
| **Observation API** | `PriceObservationViewSet` allowed `PUT`/`PATCH`/`DELETE` on published records | Override `update`/`partial_update` with `405 Method Not Allowed`, disallow `destroy` on published | `backend/apps/market_data/api/v1/views/operations.py` | Verified |
| **Observation API** | `get_queryset()` excluded `MarketDataPublisher` group from viewing pending drafts | Added `MarketDataPublisher` to authorized query group checks | `backend/apps/market_data/api/v1/views/operations.py` | Verified |
| **Observation API** | Valuation refresh error could roll back published observation transaction | Atomic publication with `select_for_update()`, post-commit failure-isolated valuation refresh | `backend/apps/market_data/api/v1/views/operations.py` | Verified |
| **CSV Import** | `clean_cell()` stripped leading `-`, corrupting negative numbers | Only strip formula injection prefixes (`=`, `@`, `\t`, `\r`); never strip `-` or `+` | `backend/apps/market_data/services/import_service.py` | Verified |
| **CSV Import** | `commit_import` accepted untrusted client-parsed rows | Stored parsed rows in `PriceImportBatch.metadata` on preview; `commit_batch` verifies ownership | `backend/apps/market_data/services/import_service.py` | Verified |
| **History Service** | `ALL` period hardcoded to 5 years (365 * 5 days) | Dynamically queries earliest eligible observation; excludes superseded corrections | `backend/apps/market_data/services/history_service.py` | Verified |
| **History API** | Invalid date format in `?from=` caused unhandled 500 | Wrapped query date parsing in `try...except ValueError` returning `400 Bad Request` | `backend/apps/market_data/api/v1/views/__init__.py` | Verified |
| **Movement Service** | Movement calculation picked superseded erroneous observations | Added `.exclude(corrections__status=ObservationStatus.PUBLISHED)` | `backend/apps/market_data/services/movement_service.py` | Verified |
| **Watchlists** | Concurrent addition caused unhandled 500 IntegrityError | Atomic transaction and clean `ValidationError("Instrument is already in your watchlist.")` | `backend/apps/watchlists/services/watchlist_service.py` | Verified |
| **Watchlists** | Single-row price resolution in `list_items` caused N+1 queries | Bulk price resolution via `PriceResolver.resolve_prices_bulk()` | `backend/apps/watchlists/services/watchlist_service.py` | Verified |
| **Dashboard** | Missing valuation snapshot substituted `inv.updated_at` | Return `valuation_date=None`, `valuation_source=None`, `valuation_status='MISSING'` | `backend/apps/dashboard/services/dashboard_service.py` | Verified |
| **Dashboard** | N+1 queries in overview, holdings, and data quality | Batch price resolution via `resolve_prices_bulk()`; prefetched valuation snapshots | `backend/apps/dashboard/services/dashboard_service.py` | Verified |
| **Dashboard** | Holdings overview loaded all holdings before in-memory slicing | Implemented database-side ordering and pagination (`order_by(...)[offset:offset+limit]`) | `backend/apps/dashboard/services/dashboard_service.py` | Verified |
| **Dashboard** | Active holdings consistency: inactive holdings mixed with active holdings | Defaulted `is_active=True` filter with optional query parameter override | `backend/apps/dashboard/services/dashboard_service.py` | Verified |
| **Frontend UI** | Misleading `24h Movement` column header for daily manual pricing | Updated table header to `Session Movement` | `frontend/src/features/watchlists/components/WatchlistTable.tsx` | Verified |
| **Frontend UI** | Hardcoded `₹` currency symbol in watchlist and target alert | Dynamic currency symbol resolution based on instrument currency | `frontend/src/features/watchlists/components/WatchlistTable.tsx` | Verified |
| **Frontend UI** | Cache invalidation did not invalidate all dashboard slices and watchlists | Consolidated `useInvalidateDashboard` invalidating overview, base keys, and watchlists | `frontend/src/features/dashboard/hooks/useDashboard.ts` | Verified |

---

## 3. Data Integrity & Financial Correctness Validation

1. **Zero vs Null Preservation**:
   - `PriceResolver`: Non-existent market prices return `price=None`, `effective_at=None`, and `published_at=None`.
   - `DashboardService`: Holdings without valuation records return `valuation_date=None` and `valuation_status='MISSING'`. True zero valuations (`current_value = Decimal('0.00')`) are distinguished from unvalued investments.
2. **Denominators in Asset Allocation**:
   - Unvalued assets (`current_value <= Decimal('0.00')` without snapshot) are excluded from percentage allocation denominators, preventing silent portfolio dilution.
3. **Currency Isolation**:
   - Multi-currency portfolios compute and report totals by currency partition (`totals_by_currency`), preventing artificial FX additions without market FX rates.
4. **Append-Only Audit Trail**:
   - Observations can only move through `draft -> pending_review -> published`. Once published, they are immutable; corrections must link through `correction_of` with documented reasons.

---

## 4. Performance Optimization Metrics

- **N+1 Query Elimination**:
  - `DashboardService.get_user_dashboard_overview`: Price resolution queries reduced from $O(N)$ to $O(1)$ batch query. Valuation checks utilize cached prefetched instances (`bool(inv.valuations.all())`).
  - `DashboardService.get_holdings_overview`: Pre-slicing pagination limits price resolution to the requested page items ($K \le 20$), eliminating unnecessary resolutions for off-page holdings.
  - `DashboardService.get_data_quality`: Price resolution queries reduced from $O(N)$ to $1$ bulk query for all active holdings.
  - `WatchlistService.list_items`: Converted to single batch query using `resolve_prices_bulk()`.
- **Database Pagination**:
  - Direct database ordering applied on `current_value`, `initial_value` (`invested_capital`), and `display_name` via SQL `ORDER BY ... LIMIT ... OFFSET`.

---

## 5. Test Execution Summary

### Backend Pytest Suite
- **Total Tests Passed:** 210 passed (0 failed, 0 errors)
- **Execution Time:** ~9.31s
- **Coverage Highlights:**
  - `apps/market_data/tests/test_sprint_5_6_stabilization.py`: 16 dedicated stabilization tests.
  - `apps/market_data/tests/test_manual_market_operations.py`: 13 tests.
  - `apps/market_data/tests/test_market_history_service.py`: 5 tests.
  - `apps/market_data/tests/test_price_movement_service.py`: 5 tests.
  - `apps/dashboard/tests/test_dashboard_api.py`: 15 tests.
  - `apps/watchlists/tests/test_watchlist_domain.py`: 10 tests.
  - Core valuation, assets, portfolios, and auth suites: 146 tests.

### Frontend Vitest Suite
- **Total Tests Passed:** 142 passed (0 failed)
- **Test Files:** 41 passed across all feature modules
- **Linting & Code Quality:**
  - `ruff check backend`: Clean (`All checks passed!`)
  - TypeScript types: Validated with no missing fields

---

## 6. Security & Permission Enforcement

| Endpoint | Operator | Publisher | Ordinary User | Anonymous |
|---|---|---|---|---|
| `POST /api/v1/market-data/observations/` | Allowed (Draft) | Allowed (Draft) | Denied (403) | Denied (401) |
| `PUT /api/v1/market-data/observations/{id}/` | Denied (405) | Denied (405) | Denied (405) | Denied (401) |
| `PATCH /api/v1/market-data/observations/{id}/` | Denied (405) | Denied (405) | Denied (405) | Denied (401) |
| `DELETE /api/v1/market-data/observations/{id}/` (Published) | Denied (400) | Denied (400) | Denied (400) | Denied (401) |
| `POST /api/v1/market-data/observations/{id}/publish/` | Denied (403) | Allowed (200) | Denied (403) | Denied (401) |
| `POST /api/v1/market-data/import/commit/` | Allowed (201) | Allowed (201) | Denied (403) | Denied (401) |
| `GET /api/v1/watchlist/` | Own items only | Own items only | Own items only | Denied (401) |
| `GET /api/v1/dashboard/overview/` | Own portfolios | Own portfolios | Own portfolios | Denied (401) |
