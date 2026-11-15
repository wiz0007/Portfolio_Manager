# API Test Registry
**Project:** Portfolio Manager — Financial Intelligence Platform  
**Scope:** Centralized API Lifecycle & Regression Registry (Sprint 1 through Sprint 9)  
**Last Updated:** Sprint 2 (2026-11-15)

---

## 1. Centralized API Registry Matrix

| API ID | Module | Method | Route | Purpose | Auth | Database Models Affected | Primary Test Files | Status |
|---|---|---|---|---|---|---|---|---|
| **SYS-001** | System | `GET` | `/api/v1/health/` | Service liveness & DB probe | None | None | `tests/test_health_api.py`, `tests/contract/test_api_contracts.py` | Verified |
| **SYS-002** | System | `GET` | `/api/schema/` | OpenAPI 3.0 schema generation | None | None | `tests/contract/test_api_contracts.py` | Verified |
| **AUTH-001** | Authentication | `GET` | `/api/v1/auth/csrf/` | Retrieve CSRF cookie token | None | Session | `apps/users/tests/test_auth_api.py` | Verified |
| **AUTH-002** | Authentication | `POST` | `/api/v1/auth/register/` | Register new user account | None | `User` | `apps/users/tests/test_auth_api.py`, `test_email_verification.py` | Verified |
| **AUTH-003** | Authentication | `POST` | `/api/v1/auth/login/` | Session login with credentials | None | `User`, Session | `apps/users/tests/test_auth_api.py` | Verified |
| **AUTH-004** | Authentication | `POST` | `/api/v1/auth/logout/` | Terminate active user session | Session | Session | `apps/users/tests/test_auth_api.py` | Verified |
| **AUTH-005** | Authentication | `GET` | `/api/v1/auth/me/` | Fetch authenticated identity | Session | `User` | `apps/users/tests/test_auth_api.py`, `tests/contract/test_api_contracts.py` | Verified |
| **AUTH-006** | User Profile | `PATCH` | `/api/v1/users/me/` | Update user display name | Session | `User` | `apps/users/tests/test_profile_api.py` | Verified |
| **AUTH-007** | Authentication | `POST` | `/api/v1/auth/verify-email/` | Validate token & mark verified | None | `User` | `apps/users/tests/test_email_verification.py` | Verified |
| **AUTH-008** | Authentication | `POST` | `/api/v1/auth/resend-verification/` | Resend verification mail | None | `User` | `apps/users/tests/test_email_verification.py` | Verified |
| **AUTH-009** | Authentication | `POST` | `/api/v1/auth/google/` | Google OAuth token login | None | `User`, Session | `apps/users/tests/test_google_auth.py` | Verified |
| **DASH-001** | Dashboard | `GET` | `/api/v1/dashboard/overview/` | User aggregated overview stats | Session | `User`, `Portfolio` | `apps/dashboard/tests/test_dashboard_api.py` | Verified |
| **PORT-001** | Portfolios | `POST` | `/api/v1/portfolios/` | Create user portfolio container | Session | `Portfolio` | `apps/portfolios/tests/test_portfolio_api.py` | Verified |
| **PORT-002** | Portfolios | `GET` | `/api/v1/portfolios/` | List portfolios owned by user | Session | `Portfolio` | `apps/portfolios/tests/test_portfolio_api.py` | Verified |
| **PORT-003** | Portfolios | `GET` | `/api/v1/portfolios/{id}/` | Retrieve single portfolio | Session | `Portfolio` | `apps/portfolios/tests/test_portfolio_api.py` | Verified |
| **PORT-004** | Portfolios | `PATCH` | `/api/v1/portfolios/{id}/` | Partial update portfolio | Session | `Portfolio` | `apps/portfolios/tests/test_portfolio_api.py` | Verified |
| **PORT-005** | Portfolios | `DELETE` | `/api/v1/portfolios/{id}/` | Delete user portfolio | Session | `Portfolio`, `Investment` | `apps/portfolios/tests/test_portfolio_api.py` | Verified |
| **INV-001** | Investments | `POST` | `/api/v1/portfolios/{portfolio_id}/investments/` | Persist investment & child details | Session | `Investment`, Detail, `InvestmentTransaction`, `InvestmentValuation` | `apps/assets/tests/test_investment_api.py`, `test_asset_lifecycle.py` | Verified |
| **INV-002** | Investments | `GET` | `/api/v1/portfolios/{portfolio_id}/investments/` | List holdings in portfolio | Session | `Investment` | `apps/assets/tests/test_investment_api.py`, `test_asset_lifecycle.py` | Verified |
| **INV-003** | Investments | `GET` | `/api/v1/portfolios/{portfolio_id}/investments/{id}/` | Retrieve holding specifications | Session | `Investment`, Detail, `InvestmentTransaction`, `InvestmentValuation` | `apps/assets/tests/test_investment_api.py`, `test_asset_lifecycle.py` | Verified |
| **INV-004** | Investments | `PATCH` | `/api/v1/portfolios/{portfolio_id}/investments/{id}/` | Partial update holding & details | Session | `Investment`, Detail | `apps/assets/tests/test_investment_api.py`, `test_asset_lifecycle.py` | Verified |
| **INV-005** | Investments | `DELETE` | `/api/v1/portfolios/{portfolio_id}/investments/{id}/` | Remove holding and cascades | Session | `Investment`, Detail, `InvestmentTransaction`, `InvestmentValuation` | `apps/assets/tests/test_investment_api.py`, `test_asset_lifecycle.py` | Verified |
| **INV-006** | Investments | `GET/POST` | `/api/v1/investments/` | Global holdings list & creation | Session | `Investment`, Detail | `tests/contract/test_api_contracts.py` | Verified |

---

## 2. Test Identifier Traceability Reference

- **`SYS-001-S01`**: Health check returns `200 OK` with database connected.
- **`SYS-001-E01`**: Health check returns `503 Service Unavailable` on DB drop without secret exposure.
- **`AUTH-002-S01`**: User registration persists user and sets session.
- **`AUTH-002-E01`**: Duplicate email returns `400 Bad Request`.
- **`AUTH-002-E02`**: Password mismatch or weak password (<8 characters) returns `400 Bad Request`.
- **`AUTH-007-S01`**: Valid verification token marks `email_verified_at` and `is_email_verified = True`.
- **`AUTH-007-E01`**: Expired token returns `400 Bad Request` with code `expired`.
- **`PORT-001-S01`**: Creates portfolio with default base currency `INR`.
- **`PORT-001-E01`**: Blank portfolio name or unsupported currency returns `400 Bad Request`.
- **`PORT-SEC-01`**: User B accessing User A's portfolio returns non-disclosing `404 Not Found`.
- **`INV-001-S01`**: Creates cash holding with `CashAccountDetail` and initial transaction.
- **`INV-001-S02`**: Creates agricultural land plot (`land_plot`) with Khasra number and circle rate valuation.
- **`INV-001-S03`**: Creates listed equity with ticker symbol, buy price, brokerage, and statutory taxes.
- **`INV-001-S04`**: Creates fixed deposit with tenure, compounding, and tax-saver flags.
- **`INV-001-S05`**: Creates recurring deposit with monthly installment.
- **`INV-001-S06`**: Creates sovereign/corporate bond with coupon rate and maturity.
- **`INV-001-S07`**: Creates mutual fund with direct growth plan, units, and purchase NAV.
- **`INV-001-S08`**: Creates physical gold & SGB series holdings.
- **`INV-001-S09`**: Creates crypto token with network transaction hash.
- **`INV-ATOM-01`**: Atomic rollback guarantees zero orphaned records on write failure.
- **`INV-SEC-01`**: Cross-user and cross-portfolio requests return `404 Not Found`.
