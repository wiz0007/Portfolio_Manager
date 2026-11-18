# Sprint 6 — Portfolio Dashboard Integration Implementation Report

**Project:** Multi-Asset Portfolio Management Platform  
**Sprint:** 6 — Portfolio Dashboard Integration  
**Date:** November 18, 2026  
**Status:** Complete & Verified  

---

## 1. Executive Summary

Sprint 6 implements a complete, data-driven portfolio dashboard that provides users with a comprehensive, mathematically sound, and reliable overview of their investments and overall financial position.

The dashboard integrates directly with the existing PostgreSQL models, transaction ledgers, valuation orchestrator, manual market-pricing infrastructure, and Sprint 5 watchlists without introducing redundant data layers or fabricated figures.

### Core Objectives Delivered:
1. **Financial Overview (Section A)**: Authoritative calculations of Total Current Value, Total Invested Capital (cost basis), Absolute Gain/Loss, and Gain/Loss Percentage.
2. **Portfolio Scoping (Section B)**: Combined multi-portfolio overview with seamless filtering by individual authorized portfolio. Rejects unauthorized or invalid portfolio IDs with HTTP 404.
3. **Asset Allocation (Section C)**: Real valuation breakdown by asset class (`category`) and portfolio. Uses strictly eligible current valuations with explicit denominator reporting, excluding unvalued holdings from the percentage denominator while clearly declaring unvalued asset counts.
4. **Holdings Overview (Section D)**: Sortable and filterable holdings list reporting display name, category, product type, units/quantity, cost basis, current value, return, valuation date, and market-price freshness badge.
5. **Recent Investment Activity (Section E)**: Chronological persisted transactions (`BUY`, `SELL`, `DIVIDEND`, etc.) displaying canonical gross considerations, fees, taxes, and net cash flows with deterministic ordering.
6. **Data Quality & Diagnostics (Section F)**: Transparency diagnostics distinguishing successfully valued, stale, missing price, awaiting verification, and unsupported/appraisal holdings with human-readable explanations.
7. **Watchlist Integration (Section G)**: Integrated preview of user's monitored instruments with latest published price, 24h movement, and currency/unit, directly reusing Sprint 5's `WatchlistService`.

---

## 2. Requirement-to-Code Correction Matrix

| Section / Capability | Requirement | Implementation | Authoritative Source |
|---|---|---|---|
| **Section A — Overview** | Backend-calculated totals, currency separation, zero capital safety, negative returns | `DashboardService.get_user_dashboard_overview`, `DashboardOverviewView` | `apps.assets.models.Investment`, `InvestmentValuation` |
| **Section B — Portfolio Selector** | Combined vs scoped views, 404 on unauthorized access | `DashboardService.resolve_portfolio_scope`, `PortfolioSelector.tsx` | `apps.portfolios.models.Portfolio` |
| **Section C — Asset Allocation** | Allocation from current eligible valuation denominator | `DashboardService.get_asset_allocation`, `AssetAllocationView`, `AssetAllocationChart.tsx` | `Investment.current_value` |
| **Section D — Holdings Overview** | Concise holdings, pagination, sorting, price freshness | `DashboardService.get_holdings_overview`, `HoldingsOverviewView`, `HoldingsOverview.tsx` | `apps.assets.models.Investment`, `PriceResolver` |
| **Section E — Recent Activity** | Deterministic transaction ledger with gross, fees, taxes | `DashboardService.get_recent_activity`, `RecentActivityView`, `RecentActivity.tsx` | `apps.assets.models.InvestmentTransaction` |
| **Section F — Data Quality** | Reliability counts (valued, stale, missing, unverified) | `DashboardService.get_data_quality`, `DataQualityView`, `ValuationDataQuality.tsx` | `PriceResolver`, `InstrumentCoverage` |
| **Section G — Watchlist Preview** | Top 5 items with prices, movements, and freshness | `DashboardService.get_watchlist_preview`, `WatchlistPreviewView`, `WatchlistPreview.tsx` | `apps.watchlists.services.WatchlistService` |

---

## 3. Financial Metric Definitions & Rules

1. **Current Valuation**:
   - `total_current_value = sum(investment.current_value)` for active holdings in a given currency.
   - Preserves zero when value is zero; never falls back to purchase price silently.
2. **Invested Capital**:
   - `total_invested_capital = sum(investment.initial_value)` for active holdings in a given currency.
3. **Gain / Loss**:
   - `absolute_gain_loss = total_current_value - total_invested_capital`.
   - `gain_loss_percentage = ((total_current_value - total_invested_capital) / total_invested_capital) * 100` when `total_invested_capital > 0`.
   - If `total_invested_capital == 0`, percentage return is explicitly `null` (reported as `N/A`).
4. **Currency Handling (Option B)**:
   - Values are strictly aggregated per currency code (`INR`, `USD`, etc.).
   - Multi-currency portfolios surface currency-specific totals and display an explicit multi-currency notification rather than applying unverified FX conversion rates.
5. **Allocation Denominator**:
   - Denominator represents the sum of current values for holdings where `current_value > 0`.
   - Holdings with missing or unvalued prices are excluded from the denominator to avoid arithmetic distortion, and their count is explicitly reported in footnote diagnostics.

---

## 4. API Endpoints Registered

Registered in `docs/testing/API_TEST_REGISTRY.md`:

| API ID | Method | Path | Status |
|---|---|---|---|
| `DASH-001` | `GET` | `/api/v1/dashboard/overview/` | Verified |
| `DASH-002` | `GET` | `/api/v1/dashboard/allocation/` | Verified |
| `DASH-003` | `GET` | `/api/v1/dashboard/holdings/` | Verified |
| `DASH-004` | `GET` | `/api/v1/dashboard/recent-activity/` | Verified |
| `DASH-005` | `GET` | `/api/v1/dashboard/data-quality/` | Verified |
| `DASH-006` | `GET` | `/api/v1/dashboard/watchlist-preview/` | Verified |

---

## 5. Verification & Test Execution Results

- **Backend Linting**: `ruff check backend` &rarr; **0 errors (All checks passed)**.
- **Django System Check**: `python manage.py check` &rarr; **0 issues identified**.
- **Database Migrations Check**: `python manage.py makemigrations --check --dry-run` &rarr; **No changes detected**.
- **Pytest Suite**: **194 passed in 5.93s** (15 dashboard tests + 179 regression tests across auth, investments, market data, valuation, portfolios, and watchlists).
- **Vitest Suite**: **142 passed across 41 test files in 55.75s** (16 dashboard lifecycle and component tests + 126 regression tests).
- **Frontend Production Build**: `tsc -b && vite build` &rarr; **Built successfully in 11.42s**.
