# Sprint 6 — Portfolio Dashboard Integration: Audit & Correction Matrix

**Sprint:** 6 — Portfolio Dashboard Integration  
**Date:** November 18, 2026  
**Document:** Audit & Correction Matrix  
**Status:** In Progress (Phase 0 Complete)

---

## 1. Architectural Audit & Baseline Analysis

### 1.1 Backend State
- **Portfolios (`apps.portfolios`)**: Scoped strictly to `user`. Holds `base_currency` (default `INR`, validated against supported currencies). Full CRUD and isolation in place.
- **Investments & Details (`apps.assets`)**: `Investment` model holds `initial_value` (invested capital / cost basis) and `current_value`. Details linked 1:1 (`CashAccountDetail`, `EquityDetail`, `MutualFundDetail`, etc.).
- **Transactions (`apps.assets.models.transactions.InvestmentTransaction`)**: Immutable ledger recording `transaction_type`, `transaction_date`, `units`, `price_per_unit`, `amount`, `gross_amount`, `fees`, `taxes`, `net_cash_flow`, `currency`. Deterministic ordering `['-transaction_date', '-created_at']`.
- **Valuations (`apps.assets.models.valuations.InvestmentValuation`)**: Historical snapshot ledger holding `amount`, `currency`, `valuation_method`, `source`, `source_reference`, `observed_at`, `metadata`.
- **Valuation Engine (`apps.valuation`)**: `ValuationOrchestrator` deterministically evaluates asset strategies (`get_valuation_strategy`), persists snapshots, and updates `current_value` without letting older historical records overwrite newer ones.
- **Market Data & Manual Prices (`apps.market_data`)**: `PriceResolver` resolves latest eligible published `PriceObservation`, provides freshness status (`AVAILABLE`, `STALE`, `MISSING`, `SYNTHETIC`, `AWAITING_VERIFICATION`, `CONFLICTED`, `UNSUPPORTED`).
- **Watchlist (`apps.watchlists`)**: `WatchlistService.list_items(user)` returns dynamically annotated user watchlist items with resolved price, movement, and freshness.
- **Existing Dashboard (`apps.dashboard`)**: Minimal stub (`DashboardService.get_user_dashboard_overview`) returning `portfolio_count` and 5 `recent_portfolios`. Lacks financial metrics, allocation, holdings overview, recent activity, data quality, and watchlist preview.

### 1.2 Frontend State
- **Dashboard Feature (`frontend/src/features/dashboard`)**: Minimal page showing welcome card, portfolio count, and recent portfolios list.
- **Design System & Theme Tokens**: CSS variables and theme tokens (`--theme-primary`, `--theme-surface`, `--theme-border`, `--theme-text`, etc.) supporting light and dark themes. Accessible Cards, Badges, Tables, Buttons, Dialogs, Charts.
- **Query Architecture**: TanStack Query (`@tanstack/react-query`) used across portfolios, investments, market data, and watchlists.

---

## 2. Requirement-to-Code Correction Matrix

| Section / Requirement | Specification | Existing State | Gap / Target Implementation | Target File(s) |
|---|---|---|---|---|
| **Section A: Overview** | Total current value, invested capital, absolute gain/loss, percentage return, active investment count, portfolio count. | Only `portfolio_count` and 5 `recent_portfolios`. | Add comprehensive aggregation in `PortfolioDashboardService`, support currency-separated totals (Option B), handle zero capital, negative returns, and unvalued assets. | `backend/apps/dashboard/services/dashboard_service.py`, `serializers/dashboard.py`, `views/dashboard.py` |
| **Section B: Portfolio Selector** | Scope all metrics to either "All Portfolios" (combined) or a single authorized `portfolio_id`. Reject invalid/unauthorized IDs with 404. | No portfolio scoping on dashboard overview. | Add `portfolio_id` query parameter validation, cross-user ownership verification with 404, dynamic filter propagation across all dashboard queries. | `backend/apps/dashboard/api/v1/views/dashboard.py`, `frontend/src/features/dashboard/components/PortfolioSelector.tsx` |
| **Section C: Asset Allocation** | Breakdown by asset class (`category`) and portfolio. Calculate percentages from current eligible valuation denominator. Exclude unvalued assets from percentage denominator, report unvalued count. | Non-existent on dashboard. | Implement `GET /api/v1/dashboard/allocation/` with asset class and portfolio distributions, currency grouping, and explicit denominator metadata. | `backend/apps/dashboard/services/dashboard_service.py`, `backend/apps/dashboard/api/v1/views/allocation.py`, `frontend/src/features/dashboard/components/AssetAllocationChart.tsx` |
| **Section D: Investment Holdings** | Holdings table/cards with name, category, asset_type, portfolio, quantity/units, invested capital, current value, gain/loss, gain/loss %, valuation date, price freshness status. Sorting & pagination. | Only full investment CRUD pages exist (`apps/assets`). | Implement `GET /api/v1/dashboard/holdings/` with filtering, sorting (`current_value`, `invested_capital`, `gain_loss`), pagination, and links to holding detail. | `backend/apps/dashboard/api/v1/views/holdings.py`, `frontend/src/features/dashboard/components/HoldingsOverview.tsx` |
| **Section E: Recent Activity** | Chronological list of recent `InvestmentTransaction` records with canonical gross, fees, taxes, net cash flow, currency, and deterministic sorting. | Non-existent on dashboard. | Implement `GET /api/v1/dashboard/recent-activity/` pulling top N transactions for user/portfolio. | `backend/apps/dashboard/api/v1/views/activity.py`, `frontend/src/features/dashboard/components/RecentActivity.tsx` |
| **Section F: Data Quality** | Breakdown of successfully valued, stale, missing price, awaiting verification, and unsupported investments with human explanations. | Non-existent on dashboard. | Implement `GET /api/v1/dashboard/data-quality/` analyzing active investments against latest valuations and instrument coverage/price statuses. | `backend/apps/dashboard/api/v1/views/data_quality.py`, `frontend/src/features/dashboard/components/ValuationDataQuality.tsx` |
| **Section G: Watchlist Preview** | Preview top 5 items from user's watchlist with latest price, currency, unit, freshness, and 24h movement. | Implemented on dedicated `/watchlist` page, not on dashboard. | Implement `GET /api/v1/dashboard/watchlist-preview/` reusing `WatchlistService.list_items(user)[:5]`. | `backend/apps/dashboard/api/v1/views/watchlist_preview.py`, `frontend/src/features/dashboard/components/WatchlistPreview.tsx` |
| **Currency Handling** | Option B: Currency-separated summaries without fabricated FX conversions. Clear multi-currency warning if holdings span multiple currencies. | Portfolios store `base_currency`. | Aggregate totals grouped by currency. When single currency, render consolidated view; when multi-currency, surface currency tabs or breakdown cards. | `backend/apps/dashboard/services/dashboard_service.py`, `frontend/src/features/dashboard/components/PortfolioOverview.tsx` |
| **Cache Invalidation** | TanStack Query invalidation on investment, transaction, portfolio, watchlist, and valuation mutation. | Only basic `dashboard-overview` query key. | Establish query keys `['dashboard', 'overview', portfolioId]`, `['dashboard', 'allocation', portfolioId]`, `['dashboard', 'holdings', ...]` and invalidate on writes. | `frontend/src/features/dashboard/hooks/useDashboard.ts` |
