# ENGINEERING REQUIREMENTS DOCUMENT
# Sprint 1 — Investment Entry Foundation, Asset-Specific Forms and Domain Contracts

**Project:** Multi-Asset Portfolio Management Platform  
**Sprint:** Sprint 1  
**Document type:** Engineering Requirements Document (ERD)  
**Priority:** High  
**Status:** Implementation specification  
**Primary deliverable:** Reusable investment UI system, asset-specific investment entry workflows, validation architecture, and finalized backend domain/schema specifications.

---

# 1. SPRINT OBJECTIVE

## 1.1 Purpose
Build the foundation through which authenticated users can add, review, and manage different types of investments within their existing portfolios.
The platform must support different asset categories with their own financial characteristics, required fields, optional fields, validation rules, and valuation methods.
The implementation must not treat all investments as identical records with a generic name, amount, and date.

## 1.2 Primary objectives
1. Establish the complete investment category selection experience.
2. Build reusable form components and a consistent form architecture.
3. Implement dedicated investment forms for all initially supported asset categories.
4. Implement field-level and cross-field validation.
5. Implement dynamic fields based on selected investment type.
6. Provide calculation previews where formulas and assumptions are defined.
7. Define backend domain models and data contracts for Sprint 2.
8. Define asset-specific business rules.
9. Establish consistent loading, validation, error, success, and recovery behavior.
10. Ensure the system can support future asset categories without restructuring the entire investment domain.

## 1.3 Existing application context
The project already has:
- React + TypeScript + Vite frontend.
- Django + Django REST Framework backend.
- PostgreSQL database through Neon.
- Existing authentication.
- Existing user model.
- Existing portfolio CRUD.
- Existing authenticated application shell.
- CSS Modules and global design tokens.
- Light and dark theme infrastructure.
- Existing portfolio ownership relationships.

## 1.4 Sprint boundaries
### Included
- Investment category selection.
- Investment type selection.
- Asset-specific forms.
- Shared form components.
- Form state management.
- Client-side validation.
- Financial input formatting and parsing.
- Conditional field rendering.
- Calculation previews.
- Review and confirmation screens.
- Domain model specification.
- Backend serializer/API contract specification.
- Backend validation and business logic specification.
- Unit and component tests.
- Responsive and accessibility requirements.

### Not included
- Production database migrations for investment models.
- Persistent investment CRUD APIs.
- Full transaction ledger implementation.
- Market data integrations.
- Live stock and crypto prices.
- Mutual fund NAV integrations.
- Automatic bank-rate synchronization.
- Production valuation engine.
- Historical portfolio performance.
- Portfolio dashboard analytics.
- Watchlist.
- OpenAI integration.
- Automated investment recommendations.

---

# 2. CORE DOMAIN CONCEPTS
- Portfolio (container owned by user)
- Investment (owned position in an asset)
- Instrument (underlying financial product/asset)
- Transaction (economic change/cash flow event)
- Valuation (estimated/observed value at timestamp)
- Opening position (historical acquisition without fabricating current buy)

---

# 3. ASSET CATEGORIES & TYPES
1. Cash and banking: Savings account, current account, cash balance
2. Fixed income: Fixed deposit, recurring deposit, bonds
3. Equity: Listed stocks
4. Mutual funds: Mutual fund schemes (Direct/Regular, Growth/IDCW)
5. Gold: Physical gold, digital gold, gold ETF, sovereign gold bonds
6. Real estate: Residential, commercial, land
7. Cryptocurrency: Supported crypto assets
