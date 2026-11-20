# Master Stabilization & System Architecture Specification

**Document Type:** Technical Architecture & Domain Design Document  
**Scope:** Core Domain Contracts, Security Boundaries, State Machines, Valuation Pipeline, and Performance Standards  
**Date:** November 18, 2026  
**Status:** Approved Technical Design  

---

## 1. Domain Entities & Responsibilities

The system maintains 5 strictly separated domain entities:
1. **Instrument (Canonical Product):** Canonical financial security shared across all users (e.g., `NSE:INFY`, `ISIN:INF109K012R6`).
2. **Identifier / Listing:** Exchange tickers, ISINs, scheme codes, and operational metadata.
3. **Investment / Holding:** User-owned position in a portfolio, containing invested capital, quantities, and asset-specific details.
4. **Transaction:** Immutable financial event (buy, sell, deposit, withdrawal, interest) forming the position ledger.
5. **Market-Data Observation:** Timestamped price observation for an instrument series, carrying currency, unit, trust class, effective date, and publication lifecycle history.

---

## 2. Observation Lifecycle State Machine

Observations adhere to a deterministic, append-only lifecycle:

```
[ Operator Entry / CSV Preview ]
               │
               ▼
           [ DRAFT ]
               │
      submit_for_review()
               │
               ▼
       [ PENDING_REVIEW ]
         /           \
   publish()       reject()
       /               \
      ▼                 ▼
 [ PUBLISHED ]     [ REJECTED ]
      │
   correct() ──> Creates new [ PUBLISHED ] observation
                 linking back via `correction_of`
```

### Transition Enforcement Rules
- `DRAFT`: Only operators can create. Can transition to `PENDING_REVIEW` via `submit_for_review()`. Cannot be directly published.
- `PENDING_REVIEW`: Only authorized `MarketDataPublisher` can `publish()` or `reject()`.
- `PUBLISHED`: Immutable. Cannot be modified via `PUT`/`PATCH`. Cannot be deleted. Corrections create a new observation linking to the original.
- Competing Corrections: Once an observation has an active published correction, subsequent correction requests are rejected.

---

## 3. Server-Persisted Import Architecture

```
Client Upload (CSV)
       │
       ▼
PriceImportService.preview_csv()
  - Validates rows, currencies, units, and decimal formats
  - Creates PriceImportBatch(status=PREVIEWED, metadata={'valid_rows': ...})
  - Returns { batch_id, valid_count, errors }
       │
Client Reviews Preview
       │
Client Sends { batch_id } (NO client parsed rows accepted)
       │
       ▼
PriceImportService.commit_batch()
  - SELECT FOR UPDATE on PriceImportBatch(id=batch_id, user=request.user)
  - Asserts status == PREVIEWED
  - Creates PriceObservation(status=DRAFT) from server-persisted valid_rows
  - Sets batch.status = COMMITTED
```

---

## 4. Canonical Valuation Pipeline

All market-linked assets use one single source of truth: `PriceResolver.resolve_price()`:

```
Investment Holding
       │
       ▼
ValuationStrategy.evaluate(investment, as_of)
       │
       ▼
PriceResolver.resolve_price(instrument, as_of, price_type)
  - Checks InstrumentCoverage
  - Queries latest eligible PriceObservation(status=PUBLISHED)
  - Excludes superseded corrections
  - Resolves currency, unit, trust class, published_at, age_seconds
       │
       ▼
ValuationResult(
  current_value,
  status: SUCCESS | ESTIMATED | STALE_DATA | MARKET_DATA_UNAVAILABLE,
  source: MANUAL_VERIFIED | USER_ESTIMATE,
  currency,
  observed_at,
  metadata
)
       │
       ▼
ValuationOrchestrator.calculate_and_record()
  - Persists InvestmentValuation snapshot if status in (SUCCESS, ESTIMATED, STALE_DATA)
  - Updates Investment.current_value atomically if snapshot date >= latest existing
```

---

## 5. Performance & Database Pagination Design

### Full SQL Pagination on Holdings
`DashboardService.get_holdings_overview()` uses PostgreSQL annotations for gain/loss:
```python
inv_qs = inv_qs.annotate(
    db_gain_loss=ExpressionWrapper(
        F('current_value') - F('initial_value'),
        output_field=DecimalField(max_digits=18, decimal_places=4)
    )
).order_by(f"{prefix}{db_col}", '-id')[offset: offset + limit]
```
This guarantees $O(1)$ memory consumption, eliminating full-table loads into Python.
