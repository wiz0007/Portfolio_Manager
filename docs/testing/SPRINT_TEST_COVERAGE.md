# Sprint Test Coverage & Audit Report
**Project:** Portfolio Manager — Financial Intelligence Platform  
**Coverage Audit:** Sprints 1 and 2 Baseline  
**Date:** 2026-11-15

---

## 1. Executive Summary

| Layer | Total Tests | Passed | Failed | Status |
|---|---|---|---|---|
| **Backend Test Suite (Pytest)** | 151 | 151 | 0 | **100% Passed** |
| **Frontend Test Suite (Vitest)** | 118 | 118 | 0 | **100% Passed** |
| **Backend Linter (`ruff check`)** | N/A | 0 errors | 0 | **100% Clean** |
| **TypeScript Compilation (`tsc -b`)** | N/A | 0 errors | 0 | **100% Clean** |
| **Production Build (`vite`)** | N/A | Success | 0 | **100% Clean** |

---

## 2. Sprint 1 Retrospective Audit

### 2.1 Implemented & Tested Coverage
- **Authentication Lifecycle**:
  - CSRF cookie retrieval (`GET /api/v1/auth/csrf/`).
  - User registration with validation (`POST /api/v1/auth/register/`).
  - Session login & invalid password/inactive user rejection (`POST /api/v1/auth/login/`).
  - Session termination (`POST /api/v1/auth/logout/`).
  - Current user identity (`GET /api/v1/auth/me/`).
  - Profile update (`PATCH /api/v1/users/me/`).
  - Email verification token generation, expiration, and replay prevention.
  - Google OAuth identity token ingestion.
- **Portfolio Foundation**:
  - User-scoped portfolio CRUD (`/api/v1/portfolios/`).
  - Currency validation (`INR`, `USD`, `EUR`, `GBP`, `JPY`, etc.).
  - Cross-user non-disclosing `404 Not Found` isolation.
- **Frontend Entry Flow & Asset Registry**:
  - Validated 20 asset product detail forms across all 7 categories.
  - Resolved historical regression: **Listed Stocks / Shares** rendered without unsupported error.
  - Live client calculation previews: fixed deposits, recurring deposits, bonds, stocks, gold, real estate, and crypto.

---

## 3. Sprint 2 Coverage Matrix

### 3.1 Model & Schema Persistence
- Implemented models: `Investment`, `CashAccountDetail`, `DepositDetail`, `BondDetail`, `EquityDetail`, `MutualFundDetail`, `GoldDetail`, `RealEstateDetail`, `CryptoDetail`, `InvestmentTransaction`, `InvestmentValuation`.
- Database migration `0001_initial.py` applied and verified.
- **Multi-Model Atomicity**: Verified that investment, child extension, initial ledger transaction, and valuation snapshot are persisted atomically or rolled back completely on failure.

### 3.2 Asset-Specific Lifecycle Coverage
- **Cash**: Savings accounts (auto-sweep thresholds) and current accounts (overdraft limits).
- **Fixed Income**: Fixed deposits (tenure, compounding, tax-saver) and recurring deposits (monthly installment).
- **Bonds**: Sovereign & corporate bonds (coupon rate, credit rating, maturity).
- **Equities**: Listed stocks (exchange, average buy price, brokerage fees, statutory taxes).
- **Mutual Funds**: Direct growth schemes, NAV, units, and SIP configuration.
- **Gold**: Physical gold (grams, purity, making charges, GST) and Sovereign Gold Bonds (SGB series).
- **Real Estate & Land**: Plot / Agricultural Land (`land_plot`) with Khasra number, Tehsil, Village, District in Uttarakhand/Delhi, Area in Acres, Stamp duty, Registration charges, and Circle rate valuation.
- **Cryptocurrency**: Tokens with hardware/software wallet types and network transaction hashes.

### 3.3 Portfolio Integration
- `HoldingsList.tsx`: Empty state, summary metric calculations (Total Holdings, Invested Capital, Current Valuation, Unrealized P&L), category filter pills.
- Quick actions: Detail modal view, fast edit modal, and cascading delete confirmation modal.
- TanStack Query cache invalidation across portfolios and dashboard.

---

## 4. Sprint 3 Coverage Matrix (Market Data Infrastructure & Demo System)

### 4.1 Models, Normalization & Persistence
- **Models Implemented:** `Instrument`, `ProviderInstrumentMapping`, `InstrumentReferenceData`, `MarketDataPoint`.
- **Investment-Instrument Link:** Nullable `Investment.instrument` foreign key added without breaking non-market investments.
- **Precision:** Strict `DecimalField(max_digits=18, decimal_places=4)` across all prices and quotes.
- **Timestamps:** UTC normalized timestamps on all `MarketDataPoint` records.

### 4.2 Provider Abstraction & Synthetic Demo System
- **`BaseMarketDataProvider`**: Canonical adapter contract for quotes, history, and health.
- **`ProviderRegistry`**: Dynamic provider routing by asset class and system mode (`DEMO` vs `PRODUCTION`).
- **`DemoMarketDataProvider`**: Deterministic synthetic generator anchored to researched November 2026 Indian stock prices (NIFTY 50 @ 25,265.60, Reliance @ 1,344.80, TCS @ 2,405.00, HDFC Bank @ 813.50, Infosys @ 1,145.90, PPFAS @ 94.2590, Gold @ 7,850.00).
- **`AMFIMarketDataProvider`**: Mutual fund NAV provider with online/offline fallback.
- **`TrueDataMarketDataProvider`**: Scaffolded adapter reporting `PENDING_CREDENTIALS` until live keys are supplied.
- **Idempotent Management Command:** `python manage.py seed_demo_market_data`.

### 4.3 REST API Endpoints Verified
- `GET /api/v1/instruments/` (INS-001)
- `GET /api/v1/instruments/search/?q=` (INS-002)
- `GET /api/v1/instruments/{id}/` (INS-003)
- `GET /api/v1/market-data/quotes/{id}/` & `?symbols=` (MKT-001)
- `GET /api/v1/market-data/history/{id}/` (MKT-002)
- `GET /api/v1/market-data/providers/` (MKT-003)
- `GET /api/v1/market-data/health/` (MKT-004)
- `GET /api/v1/market-data/overview/` (MKT-005)

### 4.4 Frontend Components Verified
- `DemoBadge`: "DEMO DATA — Synthetic prices, not live market quotations" badge & banner.
- `QuoteCard`: Dynamic price, change percent, and visual indicators.
- `InstrumentSearch`: Real-time debounced instrument finder.
- `PriceChart`: Interactive SVG area chart with timeframe filters (1W, 1M, 3M, 1Y, ALL).
- `MarketOverviewPage`: Responsive market dashboard at `/markets`.

---

## 5. Known Regressions & Permanent Protection
1. **Dropdown Menu Breakout**: Fixed SearchSelect container CSS scoping to guarantee proper anchor positioning.
2. **Unsupported Asset Type: Listed Stocks**: Mapped `listed_stock` to `StockForm.tsx`.
3. **Unsupported Asset Type: Land / Plot**: Dedicated `AgriculturalLandForm.tsx` mapped to `land_plot`.
4. **Cross-User IDOR Access**: Verified in `backend/tests/security/test_security_isolation.py`.
5. **Sprint 4 Investment Integrity Hardening**: Dedicated category serializers with strict boolean, positive numeric ranges, immutable field injection rejection (`test_investment_security.py`).
6. **Sprint 4 Valuation & Projection Engine**: Deterministic asset strategies, compounding EAR verification, and scenario projections (`test_valuation_engine.py`, `test_projection_engine.py`).

---

## 6. Sprint 4 Test Matrix — Valuation Engine & Future Projections

| Test ID | Module | Description | Status |
|---|---|---|---|
| `VAL-001` | `apps.valuation` | Cash & banking balance valuation | Passed |
| `VAL-002` | `apps.valuation` | Fixed deposit contractual compounding with EAR | Passed |
| `VAL-003` | `apps.valuation` | Recurring deposit installment compounding | Passed |
| `VAL-004` | `apps.valuation` | Equity & MF valuation from live/demo market quotes | Passed |
| `VAL-005` | `apps.valuation` | Orchestrator atomic calculation & snapshot creation | Passed |
| `VAL-006` | `apps.valuation` | Manual point-in-time valuation snapshot recording | Passed |
| `VAL-007` | `apps.valuation` | Performance metrics (cost basis vs current valuation) | Passed |
| `VAL-008` | `apps.valuation` | REST API endpoints for calculate, list, performance | Passed |
| `PROJ-001` | `apps.valuation` | Lump sum compound growth math | Passed |
| `PROJ-002` | `apps.valuation` | Regular annuity contributions (end of period) | Passed |
| `PROJ-003` | `apps.valuation` | Regular annuity contributions (beginning of period) | Passed |
| `PROJ-004` | `apps.valuation` | Zero return rate annuity safety | Passed |
| `PROJ-005` | `apps.valuation` | Multi-scenario generation (Conservative, Base, Optimistic) | Passed |
| `PROJ-006` | `apps.valuation` | Custom rate projection simulation | Passed |
| `PROJ-007` | `apps.valuation` | Strictly non-mutating calculation guarantee | Passed |
| `PROJ-008` | `apps.valuation` | Projection calculation REST API endpoint | Passed |
| `SEC-001` | `apps.assets` | Rejection of immutable relationship fields (`id`, `portfolio`) | Passed |
| `SEC-002` | `apps.assets` | Rejection of negative quantities and prices | Passed |
| `SEC-003` | `apps.assets` | Strict boolean field parsing without `bool('false')` bug | Passed |
| `SEC-004` | `apps.assets` | Preserving initial acquisition cost on valuation updates | Passed |

---

## 7. Sprint 4 Stabilization & Correction Matrix

| Test ID | Module / File | Description | Status |
|---|---|---|---|
| `INV-001` | `test_investment_validation.py` | Mandatory acquisition field enforcement per product type | Passed |
| `INV-002` | `test_investment_validation.py` | Rejection of incompatible category/product-type combinations | Passed |
| `INV-003` | `test_investment_validation.py` | Strict decimal validation and boolean rejection | Passed |
| `INV-004` | `test_investment_validation.py` | Cross-field date validation (maturity >= start date) | Passed |
| `INV-005` | `test_investment_validation.py` | Partial update (PATCH) allows single field update | Passed |
| `INV-007` | `test_investment_validation.py` | Atomic rollback of parent investment when detail creation fails | Passed |
| `INV-008` | `test_investment_validation.py` | Authoritative cost derivation; arbitrary summary overrides rejected | Passed |
| `TXN-001` | `test_transaction_integrity.py` | Opening transaction mapped strictly to actual detail acquisition date | Passed |
| `TXN-002` | `test_transaction_integrity.py` | Canonical ledger contract (`gross_amount`, `fees`, `taxes`, `net_cash_flow`) | Passed |
| `TXN-003` | `test_transaction_integrity.py` | Idempotent transaction ledger creation at asset creation | Passed |
| `TXN-004` | `test_transaction_integrity.py` | Backward compatibility with legacy `amount` field | Passed |
| `VAL-001` | `test_valuation_registry.py` | Explicit product-type strategy mapping without silent generic fallbacks | Passed |
| `VAL-002` | `test_valuation_registry.py` | SGB separate from physical gold; Bond separate from Fixed Deposit | Passed |
| `VAL-004` | `test_valuation_registry.py` | Rejection of unsupported product types with `UnsupportedStrategyError` | Passed |
| `VAL-005` | `test_valuation_registry.py` | Rejection of mismatched category/product with `UnsupportedStrategyError` | Passed |
| `VAL-006` | `test_valuation_registry.py` | Blank/missing asset type fails loudly, never defaults to cash | Passed |
| `VAL-010` | `test_valuation_strategies.py` | 24K vs 22K gold purity conversion basis | Passed |
| `VAL-011` | `test_valuation_strategies.py` | Missing gold weight returns `INCOMPLETE_INPUT`, never defaults to 1.0g | Passed |
| `VAL-012` | `test_valuation_strategies.py` | SGB valuation includes semi-annual accrued coupon | Passed |
| `VAL-013` | `test_valuation_strategies.py` | Equity missing units returns `INCOMPLETE_INPUT` | Passed |
| `VAL-014` | `test_valuation_strategies.py` | FD Cumulative (compounded) vs Non-Cumulative (payout) | Passed |
| `VAL-015` | `test_valuation_strategies.py` | FD ceases compounding past maturity date | Passed |
| `VAL-016` | `test_valuation_strategies.py` | Real estate strictly scaled by `ownership_percentage / 100` | Passed |
| `VAL-017` | `test_valuation_strategies.py` | Cash valuation includes ISO `balance_date` metadata | Passed |
| `VAL-018` | `test_valuation_strategies.py` | Crypto zero/missing token quantity validation | Passed |
| `VAL-040` | `test_valuation_history.py` | Historical older snapshot never overwrites newer `current_value` | Passed |
| `VAL-041` | `test_valuation_history.py` | Newer snapshot properly updates `current_value` | Passed |
| `VAL-042` | `test_valuation_history.py` | Failed calculation preserves existing `current_value` | Passed |
| `VAL-043` | `test_valuation_history.py` | Zero cost basis returns `'unavailable'` return percentage | Passed |
| `VAL-044` | `test_valuation_history.py` | Legitimate zero valuation preserved | Passed |
| `PROJ-009` | `test_projection_engine.py` | Mixed contribution (k=12) vs compounding (m=4) frequency math | Passed |
| `PROJ-010` | `test_projection_engine.py` | Fractional time horizon (e.g. 2.5 years) schedule | Passed |
| `PROJ-011` | `test_projection_engine.py` | Gold category explicit default assumption rates (6%, 9%, 12%) | Passed |
| `FE-001` | `valuationIntegration.test.tsx` | HoldingValuationCard renders authoritative backend performance metrics | Passed |
| `FE-002` | `valuationIntegration.test.tsx` | Zero cost basis renders `N/A` return percentage without NaN% | Passed |
| `FE-003` | `valuationIntegration.test.tsx` | Provenance badges: `Synthetic Demo`, `Market Feed`, `Contractual`, etc. | Passed |
| `FE-004` | `valuationIntegration.test.tsx` | ProjectionCalculatorModal renders disclaimer banner & schedule | Passed |

