# Sprint Test Coverage & Audit Report
**Project:** Portfolio Manager — Financial Intelligence Platform  
**Coverage Audit:** Sprints 1 and 2 Baseline  
**Date:** 2026-11-15

---

## 1. Executive Summary

| Layer | Total Tests | Passed | Failed | Status |
|---|---|---|---|---|
| **Backend Test Suite (Pytest)** | 95 | 95 | 0 | **100% Passed** |
| **Frontend Test Suite (Vitest)** | 123 | 123 | 0 | **100% Passed** |
| **TypeScript Compilation (`tsc`)** | N/A | 0 errors | 0 | **100% Clean** |
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
