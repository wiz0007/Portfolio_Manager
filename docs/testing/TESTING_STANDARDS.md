# Centralized Testing Standards & Conventions
**Project:** Portfolio Manager — Financial Intelligence Platform  
**Scope:** Test Architecture, Standards, Execution & Quality Controls  
**Target:** Sprints 1 through 9

---

# 1. Core Testing Architecture

## 1.1 Backend Standards (Pytest + Django REST Framework)

1. **Framework**: `pytest`, `pytest-django`, `rest_framework.test.APIClient`.
2. **Configuration**: Standardized in `backend/pytest.ini` with `DJANGO_SETTINGS_MODULE = config.settings.test`.
3. **Database Isolation**:
   - Local unit and fast lifecycle tests run against isolated in-memory SQLite via `config.settings.test`.
   - CI and integration runs target PostgreSQL test instances when configured via `CI_TEST_DATABASE_URL`.
4. **Data Creation & Factories**:
   - Located in `backend/tests/factories/` (`user_factory.py`, `portfolio_factory.py`, `investment_factory.py`).
   - All tests use factories with randomized, non-colliding entities.
   - Tests must never depend on the execution order or shared mutable global state.

## 1.2 Frontend Standards (Vitest + React Testing Library)

1. **Framework**: `vitest`, `@testing-library/react`, `@testing-library/user-event`.
2. **Provider Isolation**:
   - Tests involving router navigation wrap components with `<BrowserRouter>`.
   - Tests using mutations or queries wrap components with an isolated `<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}>`.
3. **Execution Commands**:
   - Fast unit & mapping suite: `npm test --prefix frontend -- --run`.
   - Type check: `npm run typecheck --prefix frontend`.
   - Production bundle test: `npm run build:frontend`.

---

# 2. Test Classification Guidelines

1. **API Lifecycle Tests**:
   - Must cover `POST` (Create), `GET` (List & Detail), `PATCH` (Partial Update), and `DELETE` (Removal).
   - Must test both 2xx success and 4xx failure scenarios (unauthenticated `401`, missing fields `400`, cross-user isolation `404`).
2. **Schema & Multi-Model Atomicity Tests**:
   - Must verify that parent holding, child detail (1:1), initial ledger transaction (1:N), and valuation snapshot (1:N) persist within a single atomic database transaction.
   - Must assert that partial failures roll back completely without orphaned child rows.
3. **Security & IDOR Isolation Tests**:
   - Must instantiate at least two independent users (`User Alpha` and `User Bravo`).
   - Must assert that User Bravo attempting to read, update, delete, or inject into User Alpha's portfolio or investments receives a non-disclosing `404 Not Found`.
4. **Deterministic Financial Verification**:
   - Formulas (interest calculations, capital outlays, ownership percentages, unrealized gains) must assert against exact decimal values without floating-point inaccuracies.

---

# 3. Execution Commands Quick Reference

```bash
# 1. Run all backend tests
cd backend
.\.venv\Scripts\python.exe -m pytest

# 2. Run specific backend test suites
.\.venv\Scripts\python.exe -m pytest apps/assets/tests/test_asset_lifecycle.py
.\.venv\Scripts\python.exe -m pytest tests/security/test_security_isolation.py
.\.venv\Scripts\python.exe -m pytest tests/integration/test_portfolio_investment_integration.py

# 3. Run all frontend tests
npm test --prefix frontend -- --run

# 4. Run TypeScript typecheck
npm run typecheck --prefix frontend

# 5. Run frontend production build
npm run build:frontend
```
