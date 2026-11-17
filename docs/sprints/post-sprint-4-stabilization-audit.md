# Post-Sprint 4 Stabilization & Consolidated Financial Integrity Audit

**Document Type:** Baseline Repository Audit & Requirement Mapping  
**Phase:** Post-Sprint 4 Stabilization and Correction  
**Date:** November 17, 2026  
**Status:** Audit Complete — Ready for Implementation  
**Base Branch:** `sprint-4`  

---

## 1. Executive Summary & Audit Methodology

This document establishes the pre-implementation baseline audit required by **Section 3** of the *Engineering Requirements Document: Portfolio Manager — Consolidated Financial Integrity, Domain Consistency & System Stabilization*.

In accordance with the primary engineering principle **"Correctness before convenience"**, no production file is modified prior to mapping the current implementation state, identifying shared root causes, and establishing verifiable test contracts for all requirement IDs across Workstreams A through J.

---

## 2. Workstream A — Canonical Asset & Investment Payload Contracts

| Requirement ID | Current Implementation | Existing Behavior | Required Behavior | Data Impact | Tests | Status |
|---|---|---|---|---|---|---|
| **FORM-001** | `frontend/src/features/investments/forms/CurrentAccountForm.tsx` & `backend/apps/assets/api/v1/serializers/details.py` | Selected account type defaults to `SAVINGS` if unspecified in payload. | Explicitly persist `account_type="CURRENT"` without fallback. | Backward compatible schema. | `FORM-001` | In Progress |
| **FORM-002** | `frontend/src/features/investments/forms/CashForm.tsx` & `CashAccountDetail` | Reuses current account bank fields requiring institution name. | Physical cash must not require bank details; distinguish physical cash from bank cash. | No schema change; adjust validator. | `FORM-002` | In Progress |
| **FORM-003** | `frontend/src/features/investments/forms/FixedDepositForm.tsx` & `FixedDepositDetailSerializer` | `bank_name` and `annual_rate_pct` aliases normalized after DRF checks required fields. | Normalize aliases upfront or enforce canonical `institution_name` and `interest_rate_pct`. | No migration needed. | `FORM-003` | In Progress |
| **FORM-004** | `frontend/src/features/investments/forms/RecurringDepositForm.tsx` & `RecurringDepositDetailSerializer` | Monthly installment sometimes mapped as total initial investment value. | Separate contractual `monthly_installment` from actual principal and total tenure. | Detail model preserves fields. | `FORM-004` | In Progress |
| **FORM-005** | `frontend/src/features/investments/forms/BondForm.tsx` & `BondDetailSerializer` | `bond_type` occasionally defaulted to pass validation; per-unit purchase price conflated. | Preserve `bond_type`, `face_value`, `units`, and explicit `purchase_price_per_unit`. | Preserve existing fields. | `FORM-005` | In Progress |
| **FORM-006** | `frontend/src/features/investments/forms/StockForm.tsx` & `EquityDetailSerializer` | Stock purchase considerations occasionally use `purchase_price` without fee/tax ledger breakdown. | Strict canonical ledger derivation: `gross = quantity * price`, `net = gross + fees + taxes`. | Uses canonical transaction contract. | `FORM-006` | In Progress |
| **FORM-007** | `frontend/src/features/investments/forms/MutualFundForm.tsx` & `MutualFundDetailSerializer` | Opening transaction amounts sometimes evaluate to 0 if NAV was parsed as price without unit consideration. | Distinguish `units`, `purchase_nav`, and transaction charges. | Transaction ledger consistency. | `FORM-007` | In Progress |
| **FORM-008** | `frontend/src/features/investments/forms/PhysicalGoldForm.tsx` & `GoldDetailSerializer` | String purity like `"22K"` rejected or defaulted to 24K in valuation. | Normalize `"22K"` to numeric 22.0 karats without defaulting invalid purities to 24K. | Preserves numeric purity. | `FORM-008` | In Progress |
| **FORM-009** | `frontend/src/features/investments/forms/DigitalGoldForm.tsx` | Treated identically to physical gold, ignoring provider fee structures. | Separate digital gold provider, weight in grams, charges, and provider price contract. | Dedicated product semantics. | `FORM-009` | In Progress |
| **FORM-010** | `frontend/src/features/investments/forms/GoldEtfForm.tsx` | Routed to gold grams instead of exchange units. | Represent ETF units, ticker, exchange, and unit NAV/price; never map to grams. | Use instrument-linked contract. | `FORM-010` | In Progress |
| **FORM-011** | `frontend/src/features/investments/forms/SgbForm.tsx` & `SovereignGoldBondDetail` | Missing quantity defaulted to 1 unit; generic gold pricing applied. | SGB units, series, issue price per gram, and 2.5% coupon basis preserved. | Retain SGB detail attributes. | `FORM-011` | In Progress |
| **FORM-012** | `frontend/src/features/investments/forms/RealEstateResidentialForm.tsx` | Form fields (plot area vs built-up area, locality) occasionally collapsed or omitted. | Persist all submitted residential fields including plot area, built-up area, and ownership %. | Serializer persists all fields. | `FORM-012` | In Progress |
| **FORM-013** | `frontend/src/features/investments/forms/RealEstateAgriculturalForm.tsx` | Land classification and area units occasionally omitted in backend payload. | Persist land classification, area units, survey details, and appraisal source. | Serializer persists all fields. | `FORM-013` | In Progress |
| **FORM-014** | `backend/apps/assets/constants/asset_mapping.py` | Certain incompatible category-product combinations allowed fallback. | Enforce strict compatibility registry; reject unknown or mismatched mappings. | None. | `FORM-014` | In Progress |
| **FORM-015** | `backend/apps/assets/api/v1/serializers/detail_validators.py` | PATCH validation previously re-evaluated required creation fields if omitted. | Partial update (PATCH) validates only submitted fields against existing detail state. | None. | `FORM-015` | In Progress |
| **FORM-016** | `backend/apps/assets/api/v1/serializers/investment.py` | Unrecognized submitted fields in nested detail were silently dropped. | Reject unrecognized detail fields or document explicit contract boundaries. | Prevents silent data loss. | `FORM-016` | In Progress |
| **FORM-017** | `backend/apps/assets/api/v1/serializers/details.py` | String booleans like `"false"` could evaluate to `True` via Python `bool()`. | Use strict DRF `serializers.BooleanField` parsing. | None. | `FORM-017` | In Progress |
| **FORM-018** | `frontend/src/features/investments/components/InvestmentEntryFlow/InvestmentEntryFlow.tsx` | Changing asset product preserved old product-specific fields in form state. | Changing asset category/product clears previous product-specific fields while preserving same-product back navigation. | Frontend state hygiene. | `FORM-018` | In Progress |

---

## 3. Workstream B — Investment Acquisition Cost & Transaction Ledger

| Requirement ID | Current Implementation | Existing Behavior | Required Behavior | Data Impact | Tests | Status |
|---|---|---|---|---|---|---|
| **TXN-001** to **TXN-013** | `backend/apps/assets/models/transactions.py` & `investment.py` | Opening transactions sometimes populated `tx_amount` while leaving `tx_gross`/`tx_net` zero. | All 13 supported products create opening transactions with canonical `gross_amount`, `fees`, `taxes`, and `net_cash_flow`. | Schema has columns (`0005`); data populated accurately. | `TXN-001` - `TXN-013` | In Progress |
| **TXN-014** | `backend/apps/assets/services/acquisition_service.py` | Financial math across purchase and sale transactions lacked unified ledger rules. | Purchase: `net = gross + fees + taxes`; Sale: `net = gross - fees - taxes`. | None. | `TXN-014` | In Progress |
| **TXN-015** | `backend/apps/assets/api/v1/serializers/transactions.py` | Negative transaction amounts permitted in certain edge cases. | Enforce non-negative consideration, fees, and taxes unless an explicit adjustment. | Validation rejection. | `TXN-015` | In Progress |
| **TXN-016** & **TXN-017** | `backend/apps/assets/api/v1/views/investment.py` | Retried investment creations could generate duplicate opening transactions. | Enforce idempotency key or deterministic operation identity on creation. | Unique constraint / idempotency cache. | `TXN-016`, `TXN-017` | In Progress |
| **TXN-018** & **TXN-019** | `backend/apps/assets/models/transactions.py` | Historical transactions could be modified directly via update. | Transactions are immutable; historical errors require reversal/correction workflow. | Add audit/reversal fields if needed. | `TXN-018`, `TXN-019` | In Progress |
| **TXN-020** & **TXN-021** | `backend/apps/assets/api/v1/serializers/investment.py` | Database atomicity not guaranteed if transaction or detail creation failed. | Enforce `transaction.atomic()` across Investment, Detail, Transaction, and Initial Valuation. | Ensures zero orphaned records. | `TXN-020`, `TXN-021` | In Progress |
| **TXN-022** | `backend/apps/assets/api/v1/serializers/transactions.py` | API serialization previously exposed only `amount`. | Expose `gross_amount`, `fees`, `taxes`, `net_cash_flow`, and currency. | DRF serializer fields. | `TXN-022` | In Progress |
| **TXN-023** | `backend/apps/assets/api/v1/views/investment.py` | Updating an investment could unintentionally alter historical transaction dates. | Investment PATCH strictly touches metadata; never rewrites historical transaction records. | Ledger immutability. | `TXN-023` | In Progress |

---

## 4. Workstream C — Investment Summary Values & Update Consistency

| Requirement ID | Current Implementation | Existing Behavior | Required Behavior | Data Impact | Tests | Status |
|---|---|---|---|---|---|---|
| **INV-001** to **INV-003** | `backend/apps/assets/api/v1/serializers/investment.py` | Client could pass `initial_value` or `current_value` directly. | Client values rejected or ignored; server calculates authoritative values from transactions. | Read-only client contract. | `INV-001` - `INV-003` | In Progress |
| **INV-004** | `backend/apps/assets/models/investment.py` | Summary values computed without checking all transaction ledger entries. | Authoritative summary derived strictly from valid transaction history. | Accurate acquisition cost. | `INV-004` | In Progress |
| **INV-005** & **INV-006** | `backend/apps/assets/api/v1/views/investment.py` | Detail updates could trigger un-audited changes to acquisition facts. | Detail updates distinguish descriptive metadata from financial terms requiring audit. | Audit log preservation. | `INV-005`, `INV-006` | In Progress |
| **INV-007** | `backend/apps/valuation/api/v1/views.py` | Investment PATCH could accidentally modify current valuation. | Valuation updates require dedicated valuation workflow; PATCH investment does not alter valuation snapshots. | Separation of concerns. | `INV-007` | In Progress |
| **INV-008** & **INV-009** | `backend/apps/assets/models/investment.py` | Truthiness checks treated zero current value as missing. | Explicit `None` check preserves valid zero valuation (`0.00`). | Preserves zero values. | `INV-008`, `INV-009` | In Progress |
| **INV-010** & **INV-011** | `backend/apps/assets/api/v1/serializers/details.py` | Cross-field validation could drop unmentioned nested fields. | PATCH preserves existing nested attributes; invalid cross-field PATCH rejected atomically. | Data preservation. | `INV-010`, `INV-011` | In Progress |
| **INV-012** | `backend/apps/assets/api/v1/views/investment.py` | Object-level permission checks required verification across all actions. | Enforce strict user/portfolio ownership on all investment mutation and read endpoints. | Security isolation. | `INV-012` | In Progress |

---

## 5. Workstream D & E — Asset Domain & Valuation Strategy Correctness

| Requirement ID | Current Implementation | Existing Behavior | Required Behavior | Data Impact | Tests | Status |
|---|---|---|---|---|---|---|
| **VAL-001** | `backend/apps/valuation/services/asset_valuation/base.py` | Strategy results varied across strategies. | Standardize `ValuationResult` across all strategies with explicit status, currency, timestamps, and notes. | Canonical contract. | `VAL-001` | In Progress |
| **VAL-002** | `backend/apps/valuation/services/asset_valuation/__init__.py` | Broad categories mapped unsupported products to generic strategies (e.g. PPF to FD, REIT to Real Estate, Silver to Gold). | Explicit product-strategy mapping; unsupported combinations return `UnsupportedStrategyError` with zero generic fallbacks. | None. | `VAL-002` | In Progress |
| **VAL-003** | Strategy classes (Equity, Bond, Gold, Mutual Fund) | Missing quantities defaulted to 1.0 or fell back to purchase price. | Missing quantity returns `ValuationStatus.INCOMPLETE_INPUT`; never defaults to 1.0. | Prevents fictitious valuations. | `VAL-003` | In Progress |
| **VAL-004** & **VAL-005** | Strategy classes | `if quote and quote.price` treated zero price as falsy and fell back to purchase price. | Explicit `None` check preserves valid zero market quote; missing quote returns `UNAVAILABLE`. | Correct market fidelity. | `VAL-004`, `VAL-005` | In Progress |
| **VAL-006** to **VAL-011** | `fixed_deposit.py`, `recurring_deposit.py`, `bond.py`, `gold.py`, `real_estate.py` | - FD quarterly compounding assumed for unknown frequencies.<br>- RD forced 1 installment for future start dates.<br>- Bond referenced nonexistent model fields.<br>- Gold purity conversion assumed 24K on invalid input.<br>- Real estate appraisal fell back to purchase price without label. | - FD normalizes annual, semi-annual, quarterly, monthly compounding; rejects unknown.<br>- RD uses actual paid installments; future start dates evaluate to 0 installments.<br>- Bond checks face value, units, accrued coupon correctly.<br>- Gold rejects invalid purity; fine gold conversion respects price basis.<br>- Real estate returns explicit appraisal or labeled cost-basis. | Accurate valuation math. | `VAL-006` - `VAL-011` | In Progress |
| **VAL-012** to **VAL-022** | `valuation_orchestrator.py` & `views.py` | - Snapshot ordering on same date lacked deterministic tie-breaker.<br>- Valuation POST returned HTTP 201 even when strategy failed.<br>- Zero cost percentage return displayed `0%` or `NaN%`. | - Valuation failure returns non-201 error response.<br>- Deterministic snapshot ordering (`valuation_date`, `observed_at`, `created_at`).br>- Zero cost basis reports percentage return as `None` / unavailable. | Prevents silent valuation errors. | `VAL-012` - `VAL-022` | In Progress |

---

## 6. Workstream F — Market-Data Infrastructure Correctness

| Requirement ID | Current Implementation | Existing Behavior | Required Behavior | Data Impact | Tests | Status |
|---|---|---|---|---|---|---|
| **MKT-001** to **MKT-003** | `backend/apps/market_data/services/market_data_service.py` | Cached quote selection did not always filter by provider and currency. | Cache selection strictly respects instrument, provider, data type, interval, and currency; no implicit demo fallback. | Cache key precision. | `MKT-001` - `MKT-003` | In Progress |
| **MKT-004** to **MKT-006** | `backend/apps/market_data/services/market_data_service.py` | Intraday 15-minute freshness applied equally to AMFI daily NAV; future timestamps accepted. | Reject future observation timestamps; daily NAV uses calendar-day freshness rule. | Freshness integrity. | `MKT-004` - `MKT-006` | In Progress |
| **MKT-007** to **MKT-010** | `backend/apps/market_data/providers/amfi_provider.py` | Historical requests raised raw `NotImplementedError`. | Check provider capabilities before calling history; return structured error. | Stable error handling. | `MKT-007` - `MKT-010` | In Progress |
| **MKT-011** & **MKT-012** | `backend/apps/market_data/models/quote.py` | Quote currency assumed matching instrument currency without verification. | Persist provider quote currency; validate against instrument currency. | Preserves quote currency. | `MKT-011`, `MKT-012` | In Progress |
| **MKT-013** to **MKT-015** | `backend/apps/market_data/providers/demo_provider.py` | Demo daily history used hardcoded `time(15, 30, tzinfo=timezone.utc)` (5.5 hrs into future relative to 15:30 IST). | 15:30 IST is 10:00 UTC (`time(10, 0, tzinfo=timezone.utc)`); seed idempotency enforced. | Correct market close timestamps. | `MKT-013` - `MKT-015` | In Progress |
| **MKT-016** & **MKT-017** | `backend/apps/market_data/models/instrument.py` | Uniqueness constraints on `symbol` alone caused collisions across exchanges/classes. | Enforce composite identity: `(symbol, exchange, asset_class)`. | Database constraint integrity. | `MKT-016`, `MKT-017` | In Progress |
| **MKT-018** to **MKT-022** | `backend/apps/market_data/api/v1/views/__init__.py` | Single instrument failure could crash market overview list. | Resilient per-instrument evaluation; pagination on instrument listings; no cross-provider history mixing. | API resilience. | `MKT-018` - `MKT-022` | In Progress |

---

## 7. Workstream H — Projection Engine

| Requirement ID | Current Implementation | Existing Behavior | Required Behavior | Data Impact | Tests | Status |
|---|---|---|---|---|---|---|
| **PROJ-001** & **PROJ-002** | `backend/apps/valuation/services/calculation/projection_engine.py` | Zero current value fell back to invested capital via truthiness. | Explicit `None` check; zero principal is valid and computes growth purely from contributions. | Accurate projection logic. | `PROJ-001`, `PROJ-002` | In Progress |
| **PROJ-003** to **PROJ-006** | `backend/apps/valuation/services/calculation/projection_engine.py` | Contribution frequency and compounding frequency assumed matching. | Independent frequencies: $i = (1 + r/m)^{m/k} - 1$; support beginning and end of period contributions. | Exact compounding math. | `PROJ-003` - `PROJ-006` | In Progress |
| **PROJ-007** & **PROJ-008** | `projection_engine.py` | Zero interest rate edge case could divide by zero. | Zero interest rate handled safely as linear sum of contributions; negative rates rejected. | Robust edge handling. | `PROJ-007`, `PROJ-008` | In Progress |
| **PROJ-009** & **PROJ-010** | `projection_engine.py` | Fractional horizons truncated contribution counts without clear convention. | Date-based contribution scheduling for fractional years with explicit convention. | Deterministic schedules. | `PROJ-009`, `PROJ-010` | In Progress |
| **PROJ-011** to **PROJ-020** | `projection_engine.py` & modal | Scenarios defaulted unknown names to generic 10%; projections lacked explicit assumption output. | Explicit scenario validation (`CONSERVATIVE`, `BASE`, `OPTIMISTIC`); return assumptions, formula ID, and non-mutating guarantee. | Mathematical auditability. | `PROJ-011` - `PROJ-020` | In Progress |

---

## 8. Workstream I — Frontend Financial Correctness

| Requirement ID | Current Implementation | Existing Behavior | Required Behavior | Data Impact | Tests | Status |
|---|---|---|---|---|---|---|
| **FE-001** & **FE-002** | `frontend/src/shared/components/forms/CurrencyInput.tsx` | Handled financial inputs with JS `Number` / `parseFloat`. | Preserve exact decimal strings; validate decimal syntax without precision loss. | Input fidelity. | `FE-001`, `FE-002` | In Progress |
| **FE-003** to **FE-005** | `frontend/src/features/investments/components/HoldingValuationCard.tsx` | Fallback calculation appeared authoritative when API was unavailable. | Show explicit loading, error, and unavailable states; only backend results labeled official. | Prevents misleading UI. | `FE-003` - `FE-005` | In Progress |
| **FE-006** | `HoldingValuationCard.tsx` | Provenance badge did not always reflect API `is_synthetic` flag. | Display clear provenance badges (`Synthetic Demo`, `Market Feed`, `Contractual`, `Manual Snapshot`). | Transparent provenance. | `FE-006` | In Progress |
| **FE-007** | `frontend/src/features/portfolios/` | Holdings with different currencies summed directly into one number. | Group totals by currency or mark aggregate unavailable if FX conversion absent. | Prevents invalid currency sums. | `FE-007` | In Progress |
| **FE-008** | `frontend/src/features/investments/components/HoldingsList/HoldingsList.tsx` | Inactive holdings could be included in active portfolio summary. | Inactive holdings excluded from active portfolio totals and counts. | Portfolio accuracy. | `FE-008` | In Progress |
| **FE-009** | `HoldingValuationCard.tsx` | Zero acquisition cost showed `0.00%` or `NaN%`. | Display `N/A (Zero Cost Acquisition)` when cost basis is zero. | Clear return display. | `FE-009` | In Progress |
| **FE-010** | `frontend/src/features/investments/api/investmentValuationApi.ts` | Recording manual valuation did not invalidate performance cache. | Invalidate investment detail, list, performance, valuation history, and portfolio summary. | Cache consistency. | `FE-010` | In Progress |
| **FE-011** & **FE-012** | `frontend/src/features/investments/components/InvestmentEntryFlow/InvestmentEntryFlow.tsx` | Switching asset product preserved old product fields in `formData`. | Reset product-specific fields on product switch; preserve inputs on back-navigation within same product. | Clean form state. | `FE-011`, `FE-012` | In Progress |
| **FE-013** to **FE-017** | Market overview & projection modal | Chart responses for old symbols could overwrite current chart; projection scenarios could not be edited independently. | Ignore stale chart responses; independent scenario editing; clear visual separation of actual vs projected values. | UI robustness. | `FE-013` - `FE-017` | In Progress |

---

## 9. Workstream J — Backend Validation & Security

| Requirement ID | Current Implementation | Existing Behavior | Required Behavior | Data Impact | Tests | Status |
|---|---|---|---|---|---|---|
| **SEC-001** to **SEC-005** | `backend/apps/assets/api/v1/serializers/details.py` & `validators.py` | Negative financial values or invalid enums permitted in certain detail fields. | Reject negative principal, negative gold weight, negative units, future acquisition dates, unsupported currencies. | Data cleanliness. | `SEC-001` - `SEC-005` | In Progress |
| **SEC-006** to **SEC-008** | `backend/apps/assets/api/v1/views/investment.py` | IDOR and mass-assignment protection required comprehensive testing. | Reject cross-user investment modification, nested relationship injection (`user`, `investment`), and mass-assignment. | Security hardening. | `SEC-006` - `SEC-008` | In Progress |
| **SEC-009** & **SEC-010** | `backend/apps/users/services/email_verification.py` & `auth.py` | Resend verification returned HTTP 429 only for existing unverified accounts, leaking account existence. | Return indistinguishable HTTP 200 responses with identical generic message for nonexistent, verified, and rate-limited emails. | Prevents account enumeration. | `SEC-009`, `SEC-010` | In Progress |
| **SEC-011** & **SEC-012** | `backend/apps/users/services/email_verification.py` | Email verification token replay and expiration behavior verified. | Tokens expire after timeout, cannot be replayed after verification, and bind to email + user ID. | Security verification. | `SEC-011`, `SEC-012` | In Progress |

---

## 10. Centralized Test Infrastructure & Audit Findings

The audit confirmed the following required test corrections from Section 15.4:
1. `test_valuation_registry.py` imports `get_strategy_for_investment` but registry exported `get_valuation_strategy`. Both names are now aligned to authoritative contracts.
2. Fixed Deposit annual compounding mapping in `fixed_deposit.py` (`'ANNUAL': 1`).
3. Cash balance valuation metadata `balance_date` normalized to ISO string format (`'2026-11-12'`).
4. `test_transaction_integrity.py` updated to verify transaction immutability and non-negative considerations.
5. `test_investment_security.py` added to verify IDOR, nested injection, and email verification enumeration protection.

---

## 11. Next Steps

With Phase 0 complete and documented in this audit, implementation proceeds sequentially across:
1. **Phase 1:** Canonical payload contracts and form state reset (`FORM-001` to `FORM-018`).
2. **Phase 2:** Transaction ledger and acquisition cost integrity (`TXN-001` to `TXN-023`).
3. **Phase 3:** Asset valuation strategies and mathematical precision (`VAL-001` to `VAL-022`).
4. **Phase 4:** Market-data infrastructure reliability (`MKT-001` to `MKT-022`).
5. **Phase 5:** Valuation orchestration, snapshots, and performance (`VAL-012` to `VAL-022`).
6. **Phase 6:** Projection engine formulas and scenario independence (`PROJ-001` to `PROJ-020`).
7. **Phase 7:** Frontend financial correctness and cache invalidation (`FE-001` to `FE-017`).
8. **Phase 8:** Full regression test suite, linting, and final delivery report.
