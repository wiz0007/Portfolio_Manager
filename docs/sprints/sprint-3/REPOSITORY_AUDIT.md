# Sprint 3 — Repository Audit & Readiness Assessment

**Project:** Multi-Asset Portfolio Management Platform  
**Sprint:** 3 — Instrument Management, Provider-Agnostic Market Data Infrastructure & Demo Data System  
**Audit Date:** 2026-11-16  
**Status:** COMPLETE — READY FOR SPRINT 3 IMPLEMENTATION  

---

## 1. Executive Summary

Sprint 3 builds the core financial market data infrastructure, decoupling asset representation and quotes from specific external data vendors. The application must support a resilient, provider-agnostic market data pipeline with an active **DEMO mode** (serving deterministic synthetic market data based on researched November 2026 Indian stock prices) alongside adapters for real providers (AMFI for mutual funds, TrueData for equities pending credentials).

This repository audit analyzes the existing codebase state following the successful delivery and test certification of Sprint 1 (Investment Entry Foundation) and Sprint 2 (Investment Persistence & Integration).

---

## 2. Existing System Architecture & Reusability

### 2.1 Backend Architecture

- **Django Version & App Structure:**
  - `apps.market_data` is already configured in `INSTALLED_APPS` within `backend/config/settings/base.py`.
  - Scaffolding exists in `backend/apps/market_data/` with placeholder folders.
  - `apps.assets` contains the core `Investment` model (`backend/apps/assets/models/investment.py`) representing discrete portfolio holdings.
- **Investment-to-Instrument Decoupling:**
  - In Sprint 2, `Investment` stores asset attributes, contractual metadata, and current value.
  - In Sprint 3, `Investment` will gain a nullable ForeignKey to `apps.market_data.models.Instrument`. This ensures non-market assets (like real estate plots, manual savings accounts, vehicle loans) function without requiring market instruments, while market-linked assets (stocks, mutual funds, gold bonds) can attach to standardized market instruments.
- **Database Precision:**
  - All price and financial amount fields adhere strictly to `DecimalField(max_digits=18, decimal_places=4)` to eliminate floating-point calculation anomalies.

### 2.2 Provider Abstraction Pattern

- A pluggable `BaseMarketDataProvider` abstract class defines the canonical interface:
  - `get_quote(instrument: Instrument) -> QuoteData`
  - `get_quotes(instruments: List[Instrument]) -> Dict[str, QuoteData]`
  - `get_history(instrument: Instrument, start_date: date, end_date: date, interval: str) -> List[HistoricalDataPoint]`
  - `health_check() -> ProviderHealth`
- A centralized `ProviderRegistry` resolves the active provider by asset class and provider configuration.
- Three initial providers:
  1. `DemoMarketDataProvider` (Active by default): Deterministic synthetic data generator using researched live price anchors with realistic intraday and historical variance.
  2. `AMFIMarketDataProvider`: Ingests and parses official AMFI NAV data for Indian mutual funds.
  3. `TrueDataMarketDataProvider`: Scaffolded adapter with structured mocks/fixtures awaiting live API credentials.

### 2.3 Researched Market Data Anchors (November 2026)

| Symbol | Name | Asset Class | Exchange | Anchor Price / NAV (INR) | Synthetic Indicator |
|---|---|---|---|---|---|
| `NIFTY50` | Nifty 50 Index | Benchmark Index | NSE | ₹25,265.60 | `is_synthetic=True` |
| `SENSEX` | BSE SENSEX | Benchmark Index | BSE | ₹82,890.00 | `is_synthetic=True` |
| `RELIANCE` | Reliance Industries Ltd | Equity | NSE | ₹1,344.80 | `is_synthetic=True` |
| `TCS` | Tata Consultancy Services | Equity | NSE | ₹2,405.00 | `is_synthetic=True` |
| `HDFCBANK` | HDFC Bank Ltd | Equity | NSE | ₹813.50 | `is_synthetic=True` |
| `INFY` | Infosys Ltd | Equity | NSE | ₹1,145.90 | `is_synthetic=True` |
| `ICICIBANK` | ICICI Bank Ltd | Equity | NSE | ₹1,585.00 | `is_synthetic=True` |
| `SBIN` | State Bank of India | Equity | NSE | ₹1,090.50 | `is_synthetic=True` |
| `122639` | Parag Parikh Flexi Cap (Direct Gr) | Mutual Fund | AMFI | ₹94.2590 | `is_synthetic=True` |
| `118834` | Mirae Asset Large Cap (Direct Gr) | Mutual Fund | AMFI | ₹124.5000 | `is_synthetic=True` |
| `119598` | SBI Bluechip Fund (Direct Gr) | Mutual Fund | AMFI | ₹88.7500 | `is_synthetic=True` |
| `GOLD24K` | Sovereign Gold / 24K Gold (1g) | Commodity | COMMODITY | ₹7,850.00 | `is_synthetic=True` |

### 2.4 Frontend Architecture & UI Rulebook Compliance

- Located at `frontend/src/features/market-data/`:
  - `InstrumentSearch`: Real-time fuzzy instrument lookup by symbol, name, or ISIN.
  - `QuoteCard`: Standardized card displaying ticker, name, price, absolute/percentage change, 52-week high/low, and prominent synthetic indicator badge.
  - `PriceChart`: Responsive interactive historical timeline (1D, 1W, 1M, 1Y, ALL) with dark/light theme support.
  - `MarketOverviewPage`: Top market indices, active gainers/losers, and instrument watchlist explorer.
  - Persistent UI Banner/Badge: **"DEMO DATA — Synthetic prices, not live market quotations"** displayed conspicuously whenever synthetic data is loaded.

---

## 3. Database Migration Strategy & Neon Compatibility

1. **New Models in `backend/apps/market_data/models/`:**
   - `Instrument` (`instruments` table)
   - `ProviderInstrumentMapping` (`provider_instrument_mappings` table)
   - `InstrumentReferenceData` (`instrument_reference_data` table)
   - `MarketDataPoint` (`market_data_points` table)
2. **Foreign Key in `backend/apps/assets/models/investment.py`:**
   - Add `instrument = models.ForeignKey('market_data.Instrument', null=True, blank=True, on_delete=models.SET_NULL, related_name='investments')`.
   - Nullable foreign key guarantees zero regression for existing investments created in Sprint 2.
3. **Migration Plan:**
   - `market_data.0001_initial`: Creates instruments, provider mappings, reference data, and market data points.
   - `assets.0003_investment_instrument`: Adds `instrument` foreign key to `Investment`.
   - Migrations will be executed against Neon PostgreSQL.

---

## 4. Centralized Test Matrix Integration

The test suite will be extended in `backend/apps/market_data/tests/` and `frontend/src/features/market-data/`:
- **INS-001:** Instrument List and Filter API.
- **INS-002:** Instrument Search API with fuzzy matching.
- **INS-003:** Instrument Detail API with Reference Data and Latest Quote.
- **MKT-001:** Latest Quote Retrieval API (single and bulk).
- **MKT-002:** Historical Timeseries API with range and interval filtering.
- **MKT-003:** Provider Registry and Active Provider Resolution.
- **MKT-004:** Provider Health Check API.
- **MKT-005:** Demo Provider Deterministic Data and Synthetic Labeling Verification.

---

## 5. Audit Conclusion

The repository is clean and ready. Obsolete `.gitkeep` files in populated directories have been purged. The implementation sequence proceeds with:
- Phase B: Instrument domain models and migration.
- Phase C & D: Provider abstraction and market data persistence.
- Phase E: Synthetic demo provider with research-anchored Indian market data.
- Phase F: REST API viewsets and endpoints.
- Phase G: Frontend market data components and pages.
- Centralized testing verification.
