# Master Engineering Requirements & System-Wide Stabilization Audit

**Project:** Multi-Asset Portfolio Management Platform  
**Scope:** Complete Sprint 5–6 Correction, Financial Data Integrity, Security, Performance, and System-Wide Stabilization  
**Baseline Commit:** `1c97b47` (`sprint-5-6-stabilization`)  
**Parent Commit:** `8730d55` (`sprint-6`)  
**Date:** November 18, 2026  
**Status:** Audit Complete — Pre-Implementation Baseline Established  

---

## 1. Executive Audit Overview

An end-to-end execution path audit was performed across frontend components, API endpoints, permissions, serializers, domain services, valuation strategies, database models, and test suites. While previous stabilization corrected single-layer symptoms, this audit identified critical multi-layer gaps where invalid operations could bypass API restrictions through alternate paths or legacy fallbacks.

The findings have been cataloged below with stable identifiers, classified by severity (P0 Critical, P1 High, P2 Medium, P3 Low), execution paths, and required architectural corrections.

---

## 2. Requirement-to-Code Correction Matrix

| Finding ID | Classification | Severity | Domain | Existing Behavior | Required Architectural Behavior | Files Involved |
|---|---|---|---|---|---|---|
| **SEC-001** | Confirmed Defect | P0 | CSV Import Security | `PriceImportCommitView` & `commit_import()` still accept `preview_result` from client payload if `batch_id` omitted | Remove legacy client-trust branch; strictly require server-persisted `batch_id` verified against user ownership | `backend/apps/market_data/api/v1/views/operations.py`<br>`backend/apps/market_data/services/import_service.py`<br>`frontend/src/features/market-data/api/marketDataApi.ts` |
| **SEC-002** | Confirmed Defect | P0 | Cache Session Isolation | `useLogout()` only nullifies `AUTH_USER_QUERY_KEY`; query cache retains previous user's portfolios, holdings, and dashboard | Purge entire TanStack query cache via `queryClient.clear()` upon logout | `frontend/src/features/authentication/hooks/useAuth.ts` |
| **FIN-001** | Confirmed Defect | P0 | Observation Lifecycle | Observations can be published directly from `DRAFT`; no `submit_for_review` action exists on viewset; `publish()` does not enforce `PENDING_REVIEW` | Enforce strict state machine: `DRAFT -> submit_for_review -> PENDING_REVIEW -> publish -> PUBLISHED`. Direct draft publishing rejected. | `backend/apps/market_data/models/observation.py`<br>`backend/apps/market_data/api/v1/views/operations.py` |
| **FIN-002** | Confirmed Defect | P0 | Correction Chain Integrity | `correct()` does not verify if original observation is already superseded by an active correction, risking competing correction siblings | Verify `original_obs.status == PUBLISHED` and reject if `corrections.filter(status=PUBLISHED).exists()` | `backend/apps/market_data/api/v1/views/operations.py` |
| **VAL-001** | Confirmed Defect | P0 | Valuation Strategy Crash | `digital_gold.py`, `gold_etf.py`, and `reit.py` reference `ValuationStatus.UNAVAILABLE`, which is not defined in `ValuationStatus` enum | Define `UNAVAILABLE`, `ERROR`, `UNSUPPORTED`, `SYNTHETIC` on `ValuationStatus` | `backend/apps/valuation/services/asset_valuation/base.py` |
| **VAL-002** | Confirmed Defect | P1 | Price Resolver Unification | Market-linked strategies (`equity`, `mutual_fund`, `crypto`, `reit`, `gold_etf`, `digital_gold`) called `MarketDataService.get_latest_quote()` instead of `PriceResolver.resolve_price()` | Unify all market-linked strategies to consume canonical `PriceResolver.resolve_price(investment.instrument, as_of=obs_dt)` | `backend/apps/valuation/services/asset_valuation/*.py` |
| **VAL-003** | Confirmed Defect | P1 | Silent Purchase Price Fallback | `equity.py` and `mutual_fund.py` fell back to `purchase_price` when market data missing and returned `ValuationStatus.SUCCESS` | Never report purchase price as verified `SUCCESS`; return `ESTIMATED` with documented assumptions or `MARKET_DATA_UNAVAILABLE` | `backend/apps/valuation/services/asset_valuation/equity.py`<br>`backend/apps/valuation/services/asset_valuation/mutual_fund.py` |
| **VAL-004** | Confirmed Defect | P1 | Valuation Snapshot Persistence | `ValuationOrchestrator.calculate_and_record()` only persisted `SUCCESS`; legitimate `ESTIMATED` valuations were silently dropped | Persist `SUCCESS`, `ESTIMATED`, and `STALE_DATA` valuations with their status in metadata | `backend/apps/valuation/services/valuation_orchestrator.py` |
| **MAP-001** | Confirmed Defect | P1 | Product Mapping (`government_bond`) | `government_bond` was allowed in product mapping but omitted from `BondDetail` creation branch in `investment.py`, falling through to deposit detail | Add `'government_bond'` to bond-detail creation tuple in `investment.py` | `backend/apps/assets/api/v1/serializers/investment.py` |
| **MAP-002** | Confirmed Defect | P1 | Product Mapping (REIT) | REIT is mapped to unit-based market-price valuation but real-estate investment creation lacks unit/quantity structure | Set `investment.quantity = units` and allow `units` / `property_type='REIT'` in `RealEstateDetailCreateValidator` | `backend/apps/assets/api/v1/serializers/investment.py`<br>`backend/apps/assets/api/v1/serializers/detail_validators.py` |
| **API-001** | Confirmed Defect | P1 | Watchlist Serializer Contract | `MarketDataAnnotationSerializer` omitted `published_at`, `age_seconds`, and `price_type`, dropping fields from API response | Add missing fields to `MarketDataAnnotationSerializer` | `backend/apps/watchlists/api/v1/serializers.py` |
| **PERF-001** | Confirmed Defect | P1 | Dashboard Holdings Pagination | `get_holdings_overview` sorted `gain_loss` in Python memory across all holdings before slicing | Annotate `db_gain_loss = ExpressionWrapper(F('current_value') - F('initial_value'))` and sort directly in SQL with stable secondary key `-id` | `backend/apps/dashboard/services/dashboard_service.py` |
| **UI-001** | Confirmed Defect | P2 | Multi-Currency Dashboard Display | Frontend showed warning message but did not render actual breakdown by currency | Render dedicated multi-currency breakdown cards/section in `PortfolioOverview.tsx` | `frontend/src/features/dashboard/components/PortfolioOverview.tsx` |
| **UI-002** | Confirmed Defect | P2 | Misleading Target Alert Label | UI displayed `Target Alert` / `Target Alerts` despite absence of notification delivery engine | Rename labels to `Configured Price Target` / `Configured Price Targets` | `frontend/src/features/watchlists/components/AddToWatchlistModal.tsx`<br>`frontend/src/features/watchlists/components/WatchlistTable.tsx`<br>`frontend/src/features/watchlists/pages/WatchlistPage.tsx` |
| **UI-003** | Confirmed Defect | P2 | Manual Valuation Precision & Date | `ManualValuationModal.tsx` parsed amount via `parseFloat()` and used `toISOString()` for date, losing precision and shifting calendar days | Preserve exact string decimal input and use local calendar date | `frontend/src/features/investments/components/ManualValuationModal/ManualValuationModal.tsx` |
| **TST-001** | Preventive Safeguard | P1 | Concurrency Testing | Watchlist concurrency test was sequential; no multi-threaded tests for simultaneous publish, corrections, or imports | Implement genuine multi-threaded test cases using `ThreadPoolExecutor` | `backend/apps/market_data/tests/test_sprint_5_6_stabilization.py` |

---

## 3. Execution Path Risk Assessment

1. **Security Vulnerability in CSV Import:**  
   The API accepted both `batch_id` and `preview_result`. A malicious operator could craft an HTTP request containing `preview_result` with arbitrary unverified prices and commit them directly without passing server-side validation.
2. **Session Bleed Across Account Switches:**  
   On shared terminals or test environments, logging out left previous portfolio net worth and holdings in client-side React Query state.
3. **Valuation Engine Attribute Errors:**  
   Invoking digital gold, gold ETF, or REIT valuation when market prices were absent raised unhandled `AttributeError: type object 'ValuationStatus' has no attribute 'UNAVAILABLE'`.
4. **Data Contract Serialization Mismatch:**  
   While `PriceResolver` was upgraded to compute `published_at` and `age_seconds`, the DRF `MarketDataAnnotationSerializer` stripped those fields from responses, leaving frontend components with undefined values.
