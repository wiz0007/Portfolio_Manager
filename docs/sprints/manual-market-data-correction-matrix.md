# Requirement-to-Code Correction Matrix & Gap Analysis
## Remaining Manual Market-Data Operations Capabilities

**Project:** Multi-Asset Portfolio Management Platform  
**Document Type:** Requirement-to-Code Gap Analysis & Correction Matrix  
**Status:** Mandatory Pre-Implementation Baseline  
**Date:** November 17, 2026  

---

## 1. Executive Mission & System Architecture

This document establishes the exact implementation gap and architectural correction matrix for the **Manual Market-Pricing System**. 

The system transitions the platform from reliance on external paid market-data APIs to a centrally managed, manually researched, verified, and shared pricing infrastructure. Prices collected by authorized operators are published once and shared across all user portfolios holding the same instrument.

### Core Operating Model & Lifecycle
```
[User Holding Creation] 
       │
       ▼
[Instrument Search] ──(Matched)──► [Link Instrument to Investment]
       │
   (Unmatched)
       │
       ▼
[Create InstrumentRequest]
       │
       ▼
[Operator Review Queue] ──(Approve / Match / Reject / Duplicate)
       │ (Atomic Approval)
       ▼
[Canonical Instrument Created] ──► [InstrumentCoverage Policy Activated]
                                            │
                                            ▼
                             [Daily Worklist Generation] (MD & CSV)
                                            │
                                            ▼
                        [Manual Entry OR Versioned CSV Import]
                                            │
                                            ▼
                             [Draft PriceObservation Created]
                                            │
                                            ▼
                            [Publisher Review & Publication]
                                            │
                                            ▼
                           [Central Shared Price Resolver]
                                            │
                                            ▼
                  [Valuation Engine Recalculates Affected Holdings]
                     (Non-mutating to acquisition cost/transactions)
```

---

## 2. Requirement-to-Code Correction Matrix

| Req ID | Requirement Description | Existing Code & Files | Identified Gap | Required Change | DB Impact | API / Frontend Impact | Automated Tests Required | Regression Risks |
|---|---|---|---|---|---|---|---|---|
| **CAT-001** | Canonical Instrument Catalogue & Identifiers | `backend/apps/market_data/models/instrument.py` | Lacks `product_type`, lifecycle `status` (ACTIVE, SUSPENDED, MATURED, DELISTED, INACTIVE), `scheme_code` (AMFI), and `security_code` (BSE). | Enhance `Instrument` with `product_type`, `status` choices, `scheme_code`, `security_code`, `metadata` JSONField. Ensure `is_active` mirrors `status == ACTIVE`. | Migration on `instruments` table. | Expose in `InstrumentSerializer`, filter by `status` and `product_type`. | Exact identifier matching (ISIN, scheme code, exchange:symbol), distinct MF plans/options, delisted state handling. | Ensure existing `is_active` property and queries continue working without regression. |
| **REQ-001** | Unknown-Instrument Request Creation | `backend/apps/assets/models/investment.py`, `backend/apps/assets/api/v1/serializers/investment.py` | No model or API to request unlisted instruments; users can only link existing instruments or enter free text without tracking. | Create `InstrumentRequest` model with raw name, asset class, product type, symbol/code, exchange, ISIN/scheme code, submitter, status, notes. Allow user investment creation to reference pending request. | New table `instrument_requests`. | POST `/api/v1/market-data/requests/`; frontend request modal in search. | Creation of request, field validation, duplicate detection, unauthenticated rejection. | None; additive model. |
| **REQ-002** | Request Deduplication & Validation | None | Duplicate requests for the same symbol/name can clutter review queues. | Implement deduplication checks preventing repeated pending requests for same symbol/exchange or ISIN. | Unique/index constraints on `(symbol, exchange, status)` where status is PENDING. | Returns 409 Conflict with reference to existing pending request. | Deduplication test across users; idempotency. | None. |
| **REQ-003** | Operator Review Workflow | `backend/apps/market_data/api/v1/views/__init__.py` | No queue or endpoints for staff to review, match, approve, request info, or reject requests. | Implement `InstrumentRequestViewSet` with actions: `match`, `approve`, `request_info`, `reject`, `mark_duplicate`. | Audit fields on `InstrumentRequest` (`reviewed_by`, `reviewed_at`, `rejection_reason`). | Staff endpoints under `/api/v1/market-data/requests/{id}/[action]/`; operator review queue UI. | Action state transitions, authorization enforcement (staff only). | None. |
| **REQ-004** | Atomic Request Approval & Policy Activation | None | Approving an instrument manually could leave it without a coverage policy. | Implement atomic approval method that creates canonical `Instrument` and active `InstrumentCoverage` policy in a single database transaction. | Foreign keys linked upon approval. | Returns newly created instrument and coverage details. | Transaction rollback on failure; atomic creation assertions. | None. |
| **COV-001** | Price Coverage Policy Model | `backend/apps/market_data/services/market_data_service.py` | Freshness and collection rules are hardcoded (15 min or 24 hr). No concept of expected price type, quotation unit, collection cadence, or permitted sources. | Create `InstrumentCoverage` model with fields: `instrument`, `price_type`, `currency`, `unit`, `cadence`, `market_timezone`, `freshness_hours`, `grace_period_hours`, `preferred_source`, `status`, `last_attempt_at`, `last_published_at`, `notes`. | New table `instrument_coverages`. | GET/POST/PATCH `/api/v1/market-data/coverage/`. Frontend coverage list/editor. | Creation, update, cadence validation, asset-specific quotation basis tests. | Default coverage fallback for existing instruments so no queries break. |
| **COV-002** | Asset-Specific Quotation Basis & Cadence | Hardcoded in providers | Different assets have different cadences (Trading Day for equities, NAV schedule for MFs, Weekly/Monthly for bonds, Appraisal for Real Estate). | Configure cadences (`EVERY_TRADING_DAY`, `EVERY_BUSINESS_DAY`, `WEEKLY`, `MONTHLY`, `ON_DEMAND`) and quotation units (`SHARES`, `UNITS`, `GRAMS_24K`, `GRAMS_22K`). | Stored in `InstrumentCoverage`. | Serializer validation for compatible price_type and unit. | Cadence-specific schedule checks, market holiday skips. | None. |
| **WRK-001** | Deterministic Worklist Generation | None | Operators have no systematic list of instruments needing prices today. | Implement `MarketDataWorklistService` identifying: due for first price, due today, stale/missing prices, conflicting observations, pending identity approval. | Tables `market_data_worklists` and `market_data_worklist_items`. | POST `/api/v1/market-data/worklists/generate/`, GET `/api/v1/market-data/worklists/{date}/`. | Deterministic ordering, idempotency, weekend/holiday filtering, first-price detection. | Generation is read-only regarding market prices; zero risk to valuations. |
| **WRK-002** | Markdown & CSV Worklist Export | None | No structured file output for offline research or external operator collaboration. | Implement serializers generating structured Markdown (`market-data/worklists/YYYY-MM-DD-market-data-worklist.md`) and standard CSV with stable worklist item IDs. | File export / streaming response. | GET `/api/v1/market-data/worklists/{date}/export-md/` & `export-csv/`. | File structure checks, column consistency, special character escaping. | None. |
| **OBS-001** | Append-Only Observation Lifecycle | `backend/apps/market_data/models/market_data_point.py` | `MarketDataPoint` is a flat table without lifecycle (`draft`, `pending_review`, `published`, `rejected`), actor tracking, or review lineage. | Create `PriceObservation` model with `status` (`DRAFT`, `PENDING_REVIEW`, `PUBLISHED`, `REJECTED`), `price_type`, `value` (Decimal), `currency`, `unit`, `effective_at`, `source`, `source_reference`, `recorded_by`, `published_by`, `published_at`, `provenance`. | New table `price_observations`. | GET/POST `/api/v1/market-data/observations/`. | State transition tests (draft -> pending -> published), actor audit preservation. | `MarketDataPoint` kept in sync upon publication for backwards compatibility. |
| **OBS-002** | Observation Immutability & Audit Chaining | None | Once published, quotes must never be edited in-place or deleted. | Enforce append-only constraint on published observations. Corrections create a new `PriceObservation` pointing to original via `correction_of` with mandatory reason. | Field `correction_of` FK to self. | POST `/api/v1/market-data/observations/{id}/correct/`. | Immutability check (reject update/delete on published), correction lineage integrity. | None. |
| **CSV-001** | Versioned CSV Import & Parsing | None | Operators can only enter prices one-by-one or via seeds. No bulk verification flow. | Implement `PriceImportService` supporting versioned CSV: `schema_version,worklist_item_id,instrument_id,price_type,value,currency,unit,effective_at,source_id,source_reference,notes`. | Tables `price_import_batches` and `price_import_row_errors`. | POST `/api/v1/market-data/import/preview/`, POST `/commit/`. | Schema version validation, column alignment, date formatting. | None. |
| **CSV-002** | Strict CSV Financial Validation & Formula Injection Defense | None | Malformed decimals, future dates, or formula injection (`=`, `+`, `-`, `@`) can corrupt database or compromise spreadsheets. | Validate: Decimal string conversion, positive values, non-future `effective_at`, permitted source, currency match, formula injection stripping/sanitization. | None. | Detailed row-level validation errors returned in preview response. | Formula injection sanitization test, future date rejection, decimal precision verification. | None. |
| **RES-001** | Shared Central Price Resolver | `backend/apps/market_data/services/market_data_service.py` | Service blindly retrieves latest quote without verifying publication state, `as_of` date bounds, or resolution status. | Implement `PriceResolver` service that checks published `PriceObservation` records matching instrument, price_type, currency, unit, and `effective_at <= as_of`. Returns explicit status: `AVAILABLE`, `STALE`, `MISSING`, `SYNTHETIC`, `UNSUPPORTED`. | None. | GET `/api/v1/market-data/resolve/{instrument_id}/`. | Resolution by historical `as_of`, draft exclusion, currency match, stale flag. | Demo provider fallback maintained in dev mode if no verified price exists. |
| **REF-001** | Valuation Refresh After Publication | `backend/apps/valuation/services/orchestrator.py` | Publishing a price does not automatically refresh holdings across user portfolios. | Implement `ValuationRefreshService`: on observation publication, query all `Investment` records linking to `instrument`, recalculate valuations using asset strategy, and update portfolio aggregates with failure isolation. | None (creates new `InvestmentValuation` snapshots). | Expose refresh count and errors in publication response. | Multi-user holding refresh, transaction immutability, individual holding error isolation. | Successful publication is not rolled back if a single downstream holding fails. |
| **SEC-001** | Role-Based Authorization & IDOR Defense | `backend/apps/users/` | Standard permissions only. No distinct operator vs publisher roles. | Implement `IsMarketDataOperator` (draft/import) and `IsMarketDataPublisher` (publish/approve/reject). Restrict draft visibility to staff. | Django permissions / groups. | Endpoints protected with 403 Forbidden for unauthorized roles. | Non-staff draft access blocked; operator cannot publish if separate publisher enforced; IDOR tests. | Ordinary users retain full access to search and view published quotes. |
| **FE-001** | User Request Flow & Feedback | `frontend/src/features/market-data/components/InstrumentSearch.tsx` | Search shows "No matching instruments found" with no action to request the instrument. | Add "Request this instrument" button opening `InstrumentRequestModal.tsx`. Display status badge on unverified holdings. | None. | Clean modal dialog using design system. | Vitest test for modal opening, submitting, and loading/error states. | None. |
| **FE-002** | Operator Portal & Worklist UI | `frontend/src/features/market-data/pages/MarketOverviewPage.tsx` | Overview page only displays ticker cards and charts; no operator controls. | Add Operator Management Tabs on `MarketOverviewPage`: Worklist view, Manual Entry modal, CSV Upload & Preview modal, Request Queue table. | None. | Accessible to staff users. | Vitest tests for worklist rendering, CSV preview error rendering, manual entry. | Non-staff users see clean overview without broken buttons. |

---

## 3. Database Schema Evolution Plan

### New Models to Create
1. **`InstrumentRequest`** (`market_data_instrument_requests`):
   - `id`: UUID (PK)
   - `user`: ForeignKey to `User` (submitter)
   - `raw_name`: CharField(255)
   - `asset_class`: CharField(32, choices=AssetClass.choices)
   - `product_type`: CharField(64)
   - `symbol`: CharField(64, blank=True)
   - `exchange`: CharField(32, blank=True)
   - `isin`: CharField(32, blank=True, null=True)
   - `scheme_code`: CharField(32, blank=True, null=True)
   - `notes`: TextField(blank=True)
   - `status`: CharField(choices=['PENDING', 'APPROVED', 'MATCHED', 'MORE_INFO_REQUESTED', 'REJECTED', 'DUPLICATE'])
   - `matched_instrument`: ForeignKey to `Instrument` (null=True)
   - `reviewed_by`: ForeignKey to `User` (null=True)
   - `reviewed_at`: DateTimeField(null=True)
   - `rejection_reason`: TextField(blank=True)
   - `created_at`, `updated_at`: DateTimeField

2. **`InstrumentCoverage`** (`instrument_coverages`):
   - `id`: UUID (PK)
   - `instrument`: OneToOneField to `Instrument` (related_name='coverage')
   - `price_type`: CharField(choices=['LTP', 'NAV', 'CLOSE', 'INDICATIVE_VALUATION', 'APPRAISAL'])
   - `currency`: CharField(max_length=10, default='INR')
   - `unit`: CharField(choices=['SHARES', 'UNITS', 'GRAMS_24K', 'GRAMS_22K', 'CURRENCY'])
   - `cadence`: CharField(choices=['EVERY_TRADING_DAY', 'EVERY_BUSINESS_DAY', 'WEEKLY', 'MONTHLY', 'ON_DEMAND', 'USER_REVIEW'])
   - `market_timezone`: CharField(default='Asia/Kolkata')
   - `freshness_hours`: PositiveIntegerField(default=24)
   - `grace_period_hours`: PositiveIntegerField(default=12)
   - `preferred_source`: CharField(max_length=64, default='MANUAL_VERIFIED')
   - `status`: CharField(choices=['ACTIVE', 'PAUSED', 'RETIRED', 'EXCLUDED'], default='ACTIVE')
   - `last_attempt_at`: DateTimeField(null=True)
   - `last_published_at`: DateTimeField(null=True)
   - `inclusion_reason`: TextField(blank=True)
   - `created_at`, `updated_at`: DateTimeField

3. **`MarketDataWorklist` & `MarketDataWorklistItem`** (`market_data_worklists`, `market_data_worklist_items`):
   - Master list record for a target date (`worklist_date`, `generated_at`, `status`, `total_items`, `completed_items`).
   - Line items linking `instrument`, `coverage`, `expected_price_type`, `due_reason` (`FIRST_PRICE`, `DUE_TODAY`, `STALE`, `CONFLICT`, `PENDING_APPROVAL`), `status` (`PENDING`, `COMPLETED`, `SKIPPED`).

4. **`PriceObservation`** (`price_observations`):
   - `id`: UUID (PK)
   - `instrument`: ForeignKey to `Instrument` (related_name='observations')
   - `price_type`: CharField(max_length=32)
   - `value`: DecimalField(max_digits=18, decimal_places=4)
   - `currency`: CharField(max_length=10, default='INR')
   - `unit`: CharField(max_length=32, default='UNITS')
   - `effective_at`: DateTimeField(db_index=True)
   - `source`: CharField(max_length=64)
   - `source_reference`: CharField(max_length=255, blank=True)
   - `notes`: TextField(blank=True)
   - `status`: CharField(choices=['DRAFT', 'PENDING_REVIEW', 'PUBLISHED', 'REJECTED'], default='DRAFT')
   - `is_synthetic`: BooleanField(default=False)
   - `recorded_by`: ForeignKey to `User` (related_name='recorded_observations')
   - `published_by`: ForeignKey to `User` (null=True, related_name='published_observations')
   - `published_at`: DateTimeField(null=True)
   - `rejection_reason`: TextField(blank=True)
   - `correction_of`: ForeignKey to self (null=True, blank=True, on_delete=models.SET_NULL, related_name='corrections')
   - `correction_reason`: TextField(blank=True)
   - `created_at`, `updated_at`: DateTimeField

5. **`PriceImportBatch` & `PriceImportRowError`** (`price_import_batches`, `price_import_row_errors`):
   - Tracks uploaded CSV batches, total rows, valid rows, error rows, committed drafts count, and row-level error messages for operator download.

### Existing Model Modifications
- **`Instrument`**: Add `product_type`, `status` (choices: ACTIVE, SUSPENDED, MATURED, DELISTED, INACTIVE), `scheme_code`, `security_code`, `metadata`. Maintain backward compatibility with `is_active`.

---

## 4. API Endpoints Contract

### Catalogue & Requests
- `GET /api/v1/market-data/instruments/` (Filter by `asset_class`, `product_type`, `status`, `exchange`, `search`)
- `GET /api/v1/market-data/instruments/{id}/`
- `GET /api/v1/market-data/instruments/search/?q={query}`
- `POST /api/v1/market-data/requests/` (Create unknown instrument request)
- `GET /api/v1/market-data/requests/` (List requests; user sees own, staff sees all)
- `POST /api/v1/market-data/requests/{id}/match/` (Staff matches to existing instrument)
- `POST /api/v1/market-data/requests/{id}/approve/` (Staff approves as canonical instrument + coverage)
- `POST /api/v1/market-data/requests/{id}/reject/` (Staff rejects with reason)
- `POST /api/v1/market-data/requests/{id}/duplicate/` (Staff marks duplicate)

### Coverage & Worklists
- `GET /api/v1/market-data/coverage/` (List coverage policies)
- `GET/PATCH /api/v1/market-data/coverage/{id}/` (Retrieve/update policy)
- `POST /api/v1/market-data/worklists/generate/` (Generate worklist for date)
- `GET /api/v1/market-data/worklists/{date}/` (Retrieve worklist items)
- `GET /api/v1/market-data/worklists/{date}/export-md/` (Download markdown)
- `GET /api/v1/market-data/worklists/{date}/export-csv/` (Download CSV)

### Price Observations & Import
- `POST /api/v1/market-data/observations/` (Create manual draft)
- `GET /api/v1/market-data/observations/` (List observations with status filter)
- `POST /api/v1/market-data/observations/{id}/publish/` (Publish observation & trigger refresh)
- `POST /api/v1/market-data/observations/{id}/reject/` (Reject draft)
- `POST /api/v1/market-data/observations/{id}/correct/` (Submit correction observation)
- `POST /api/v1/market-data/import/preview/` (Upload CSV and return validation report)
- `POST /api/v1/market-data/import/commit/` (Commit valid rows from preview as drafts)
- `GET /api/v1/market-data/resolve/{instrument_id}/` (Resolve shared published price)

---

## 5. Security & Verification Strategy

1. **Role Enforcement**:
   - `IsAuthenticated`: All endpoints.
   - `IsMarketDataOperator`: Can draft observations, upload CSVs, generate worklists.
   - `IsMarketDataPublisher` / `is_staff`: Can publish observations, approve instrument requests, issue corrections.
2. **Formula Injection Sanitization**:
   - Cells beginning with `=`, `+`, `-`, `@`, `\t`, `\r` in CSV export or import are strictly escaped/neutralized.
3. **Financial Precision**:
   - Every price uses `DecimalField(18, 4)` and string representation in JSON payloads.
4. **Valuation Protection**:
   - Publication triggers valuation refresh without modifying transaction amounts, invested capital, or acquisition records.
5. **Regression Verification**:
   - All 151 existing backend tests and 118 frontend tests must remain green.
