# Engineering Requirements Document
# Sprint 2 — Investment Persistence, Portfolio Integration & Real Estate Form Completion

**Project:** Portfolio Manager — Financial Intelligence Platform  
**Sprint:** 2  
**Architecture:** React + TypeScript + Vite / Django + Django REST Framework / PostgreSQL (Neon)  
**Database:** Existing PostgreSQL database  
**Development approach:** Modular monolith  
**Document type:** Implementation-level engineering specification

---

# 1. Sprint Objective

Sprint 2 transforms the investment-entry foundation created in Sprint 1 into a functional investment-management system.

A user must be able to:

1. Open an existing portfolio.
2. Select an investment category and product.
3. Complete the corresponding investment form.
4. Review and confirm the entered information.
5. Persist the investment in PostgreSQL.
6. Return to the selected portfolio.
7. View the saved investment.
8. Open its details.
9. Edit the investment.
10. Delete the investment with appropriate confirmation.

The sprint must also resolve the remaining unsupported asset-type issue:

- Real Estate → Plot / Agricultural Land.

The Equity & Stocks → Listed Stocks / Shares issue is already resolved and must not be reintroduced or unnecessarily modified.

## 1.1 Definition of completion

Sprint 2 is complete when an investment entered through the frontend is genuinely persisted, correctly associated with its portfolio and user, retrieved through the backend, and displayed in the portfolio interface.

A temporary frontend state, mock API response, local-storage-only implementation, or hardcoded investment must not be considered persistence.

---

# 2. Existing System Context

The following functionality already exists and must be reused.

## 2.1 Authentication

- Custom UUID user model.
- Email-based authentication.
- Session-based authentication.
- CSRF protection.
- Current-user endpoint.
- Profile management.
- Email verification.

## 2.2 Portfolio management

Existing portfolio model:

- UUID primary key.
- User foreign key.
- Name.
- Optional description.
- Base currency.
- Created timestamp.
- Updated timestamp.

Existing APIs:

- GET /api/v1/portfolios/
- POST /api/v1/portfolios/
- GET /api/v1/portfolios/{id}/
- PATCH /api/v1/portfolios/{id}/
- DELETE /api/v1/portfolios/{id}/

All portfolio operations are user-scoped.

## 2.3 Sprint 1 investment-entry foundation

Reuse the existing:

- Investment selection flow.
- Category and product selection.
- Asset-specific forms.
- Form components.
- Validation utilities.
- Review and confirmation screens.
- Asset-product-to-form mapping.

Do not rebuild working Sprint 1 components without a demonstrated technical reason.

---

# 3. Scope and Boundaries

## 3.1 Included in Sprint 2

1. Real Estate agricultural land form completion.
2. Investment domain database models.
3. Database migrations.
4. Investment creation API.
5. Investment retrieval APIs.
6. Investment update API.
7. Investment deletion API.
8. Investment-to-portfolio association.
9. Portfolio investment listing.
10. Investment detail page.
11. Frontend/backend integration.
12. Server-side validation.
13. Transactional persistence.
14. Error handling.
15. Automated tests.
16. Manual verification.

## 3.2 Explicitly excluded

Do not implement the following in this sprint:

- Live stock market prices.
- Mutual fund NAV integrations.
- Cryptocurrency exchange integrations.
- Automated bank synchronization.
- Property market-rate APIs.
- Portfolio performance analytics.
- CAGR and XIRR.
- Profit/loss reporting.
- Asset allocation analytics.
- Benchmark comparisons.
- AI investment analysis.
- OpenAI API integration.
- Predictive financial recommendations.
- Automated future-value forecasting based on external market data.

These should be separate future implementation stages.

## 3.3 Important distinction

Sprint 2 stores investment information and the user's acquisition/opening position.

It does not build a complete market-data or investment-performance engine.

A saved purchase price is not automatically a current market price. A user-entered estimated property value is not a verified market valuation.
