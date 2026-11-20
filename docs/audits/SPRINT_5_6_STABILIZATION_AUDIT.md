# Sprint 5 & 6 Stabilization, Financial Data Integrity and Performance Optimization Audit

**Project:** Portfolio Manager  
**Scope:** Sprint 5 (Watchlist and Market-Data Integration) & Sprint 6 (Portfolio Dashboard Integration)  
**Date:** November 18, 2026  
**Document:** Source-Level Audit & Correction Matrix  
**Status:** In Progress (Phase 0 Complete)  

---

## 1. Architectural Baseline & Audit Summary

An in-depth inspection of the current repository baseline across backend (`apps.market_data`, `apps.watchlists`, `apps.dashboard`, `apps.valuation`, `apps.assets`, `apps.portfolios`) and frontend (`features/watchlists`, `features/dashboard`, `features/investments`, `shared/services`) identified critical financial integrity, security, concurrency, and performance gaps.

### Summary of Key Findings:
1. **Security Vulnerability in Observation Management**: `PriceObservationViewSet` inherits `ModelViewSet` without disabling standard `update`, `partial_update`, or `destroy` actions, allowing published financial prices to be mutated or deleted via standard REST endpoints.
2. **Permission Queryset Discrepancy**: `PriceObservationViewSet.get_queryset()` filters `status=PUBLISHED` for any user not in `MarketDataOperator` or staff, blocking authorized `MarketDataPublisher` users from retrieving pending-review observations to publish or reject them.
3. **CSV Formula Injection / Negative Value Corruption**: `clean_cell()` strips leading `-` characters, causing valid negative financial values to silently convert to positive numbers.
4. **Client Preview Trust Vulnerability in CSV Import**: `commit_import` trusts client-supplied `preview_result` payloads containing unverified `valid_rows` instead of server-persisted batch state.
5. **Historical Timeseries 'ALL' Distortion & Correction Mixing**: The `ALL` period was hardcoded to `365 * 5` days instead of the earliest available observation date, and superseded historical observations were not filtered out when corrections occurred.
6. **Watchlist Concurrency Race Condition**: `WatchlistService.add_item` uses an existence-check-then-create pattern that can race under concurrent requests.
7. **N+1 Queries & Lack of Batch Resolution in Dashboard**:
   - `DashboardService.get_user_dashboard_overview` calls `inv.valuations.exists()` in a loop.
   - `PriceResolver.resolve_price` is called individually row by row for every investment in overview, holdings, and data quality.
   - `get_holdings_overview` queries `inv.valuations.order_by(...).first()` in a Python loop and loads all user holdings into memory before slicing.
8. **Fabricated Valuation Timestamps**: `DashboardService.get_holdings_overview` substitutes `inv.updated_at.date().isoformat()` when no valuation record exists.
9. **Active/Inactive Holdings Discrepancy**: Overview and Allocation filtered `is_active=True`, but `get_holdings_overview` omitted the active filter.
10. **ResolvedPrice Contract Lacking Publication Timestamp**: `ResolvedPrice` does not expose `published_at`, hindering the frontend from computing true publication age.
11. **Frontend Freshness & Movement Labels**: Frontend displays `24h Movement` despite once-daily manual market data collection, and lacks periodic relative-time updates (`Updated X hours ago`).

---

## 2. Requirement-to-Code Correction Matrix

| Finding ID | Domain / Module | Existing Behavior | Root Cause | Affected Files | Correction Plan |
|---|---|---|---|---|---|
| **SEC-OBS-001** | Observation Security | `PriceObservationViewSet` inherits `ModelViewSet`, allowing `PUT/PATCH/DELETE` on published observations. | Generic DRF ViewSet inheritance without restricting destructive HTTP verbs. | `backend/apps/market_data/api/v1/views/operations.py` | Inherit from `viewsets.ReadOnlyModelViewSet` with explicit custom actions (`create` draft, `publish`, `reject`, `correct`). Explicitly block `update`/`partial_update`/`destroy` on published records. |
| **SEC-OBS-002** | Publisher Permissions | Publishers cannot retrieve pending observations; `get_queryset` only checks `MarketDataOperator`. | `PriceObservationViewSet.get_queryset` checks `is_staff` or `MarketDataOperator`, omitting `MarketDataPublisher`. | `backend/apps/market_data/api/v1/views/operations.py` | Update `get_queryset` to include `request.user.groups.filter(name='MarketDataPublisher').exists()`. |
| **FIN-CSV-001** | CSV Sanitization | `clean_cell()` strips leading `-` from cells, converting negative numbers to positive. | Flawed spreadsheet formula injection protection stripping `-` from numeric cells. | `backend/apps/market_data/services/import_service.py` | Separate numeric parsing from text formula protection. Preserve legitimate negative decimals; reject negative market prices via domain validation. |
| **SEC-CSV-001** | CSV Import Trust | `commit_import` endpoint accepts parsed `preview_result` from client. | Client-side state passing instead of server-managed batch entity. | `backend/apps/market_data/services/import_service.py`, `backend/apps/market_data/api/v1/views/operations.py` | `preview_csv` persists a `PriceImportBatch` in `PREVIEWED` status with row data / hash in `metadata`. `commit_import` takes only `batch_id` and commits server-side validated rows. |
| **FIN-PRC-001** | Canonical Price Contract | `ResolvedPrice` omits `published_at`, `price_type`, and does not check coverage price type when unspecified. | Incomplete dataclass and missing coverage fallback logic in `PriceResolver`. | `backend/apps/market_data/services/price_resolver.py` | Add `published_at`, `price_type` to `ResolvedPrice`. Resolve instrument coverage default `price_type` when caller leaves it None. Include `AWAITING_VERIFICATION` check for pending review observations. |
| **FIN-PRC-002** | Correction & Supersession | Observations that have been superseded by corrections can still be returned as current or in history. | Missing supersession filter (`corrections.filter(status='PUBLISHED')`). | `backend/apps/market_data/services/price_resolver.py`, `backend/apps/market_data/services/history_service.py` | Exclude superseded observations from current resolution and active historical timeseries. |
| **FIN-HST-001** | Historical Timeseries ALL | `ALL` period hardcoded to `365 * 5` days. | Arbitrary period calculation in `PERIOD_DAYS_MAP`. | `backend/apps/market_data/services/history_service.py` | When period is `ALL`, dynamically query earliest eligible observation date as `resolved_start`. Add explicit `5Y` period. |
| **CONC-WCH-001** | Watchlist Concurrency | Existence-check-then-create in `WatchlistService.add_item` allows race conditions. | Non-atomic check and insert. | `backend/apps/watchlists/services/watchlist_service.py` | Use atomic creation and catch database `IntegrityError` to return clean duplicate validation error. |
| **PERF-DASH-001** | N+1 Queries & Batching | Dashboard loops over investments calling `inv.valuations.exists()`, `inv.valuations.first()`, and `PriceResolver.resolve_price`. | Per-holding iterative queries instead of subqueries / batch lookups. | `backend/apps/dashboard/services/dashboard_service.py` | Pre-fetch latest valuation snapshots in single bulk query or subquery. Implement batch price resolver for unique instruments. |
| **PERF-DASH-002** | Holdings Pagination | `get_holdings_overview` loads all holdings into memory before slicing with Python `[offset:offset+limit]`. | Memory-side pagination on unbound QuerySet. | `backend/apps/dashboard/services/dashboard_service.py` | Implement database-side filtering, sorting, and pagination. |
| **FIN-DASH-001** | Valuation Date Fallback | `get_holdings_overview` sets `valuation_date = inv.updated_at` when valuation record is missing. | Fallback to record update timestamp. | `backend/apps/dashboard/services/dashboard_service.py` | Set `valuation_date = None` when no valuation snapshot exists. |
| **FIN-DASH-002** | Active Holdings Consistency | `get_holdings_overview` does not filter `is_active=True`, whereas overview and allocation do. | Inconsistent QuerySet filtering. | `backend/apps/dashboard/services/dashboard_service.py` | Filter `is_active=True` by default in holdings overview. |
| **UI-WCH-001** | Freshness & Movement | UI displays misleading `24h Movement` and lacks publication relative age (`Updated 2 hours ago`). | Hardcoded labels and missing `published_at` consumer. | `frontend/src/features/watchlists/`, `frontend/src/features/dashboard/` | Replace `24h Movement` with `Movement (vs Prev Close)` and show `Last Updated` relative timestamp with tooltip. |
| **UI-DASH-001** | Multi-Currency Presentation | Multi-currency summary details are not fully explorable per currency. | UI only shows primary currency card. | `frontend/src/features/dashboard/components/PortfolioOverview.tsx` | Provide currency tabs/breakdown so users can inspect each currency's totals separately. |

---

## 3. Dependency Order for Implementation

1. **Phase 1: Canonical Market-Price Contract** (`apps/market_data/services/price_resolver.py`, `history_service.py`).
2. **Phase 2: Observation Security & Lifecycle** (`apps/market_data/api/v1/views/operations.py`, `models/observation.py`).
3. **Phase 3: CSV Import Integrity** (`apps/market_data/services/import_service.py`, `views/operations.py`).
4. **Phase 4: Historical & Watchlist Corrections** (`apps/watchlists/services/watchlist_service.py`).
5. **Phase 5: Dashboard Financial Correctness & Performance Optimization** (`apps/dashboard/services/dashboard_service.py`).
6. **Phase 6: Frontend Integration & Freshness UI** (`frontend/src/features/watchlists`, `frontend/src/features/dashboard`).
7. **Phase 7: Full Regression & Acceptance Testing** (Backend Pytest, Frontend Vitest, Build, Report).
