# Sprint 1 — Test Cases & Automated Verification Matrix

## Automated Test Results

### Backend Tests (Pytest) - 17 Passed, 0 Failed
| Test ID | Description | Suite | Result |
|---|---|---|---|
| TC-UNIT-01 | Create user with valid email, password, full_name | `test_models.py` | PASS |
| TC-UNIT-02 | Normalize mixed-case email during user creation | `test_models.py` | PASS |
| TC-UNIT-03 | Reject user creation without email | `test_models.py` | PASS |
| TC-UNIT-04 | Enforce database uniqueness constraint on email | `test_models.py` | PASS |
| TC-UNIT-05 | Create superuser with required staff/superuser flags | `test_models.py` | PASS |
| TC-API-01 | Fetch CSRF cookie and token via `/api/v1/auth/csrf/` | `test_auth_api.py` | PASS |
| TC-API-02 | Register user successfully with valid payload (201) | `test_auth_api.py` | PASS |
| TC-API-03 | Reject duplicate email registration (400) | `test_auth_api.py` | PASS |
| TC-API-04 | Reject password confirmation mismatch (400) | `test_auth_api.py` | PASS |
| TC-API-05 | Reject weak password shorter than 8 chars (400) | `test_auth_api.py` | PASS |
| TC-API-06 | Reject invalid email format (400) | `test_auth_api.py` | PASS |
| TC-API-07 | Login with valid credentials and establish session (200) | `test_auth_api.py` | PASS |
| TC-API-08 | Reject invalid password with generic error message (400) | `test_auth_api.py` | PASS |
| TC-API-09 | Reject non-existent email with generic error message (400) | `test_auth_api.py` | PASS |
| TC-API-10 | Reject inactive user account login attempt (400) | `test_auth_api.py` | PASS |
| TC-API-11 | Return 401 Unauthorized when unauthenticated accessing `/me/` | `test_auth_api.py` | PASS |
| TC-API-12 | Terminate session and invalidate cookie on logout (200 -> 401) | `test_auth_api.py` | PASS |

### Frontend Tests (Vitest) - 12 Passed, 0 Failed
| Test ID | Description | Suite | Result |
|---|---|---|---|
| TC-FE-01 | Validate login schema with valid inputs | `authSchemas.test.ts` | PASS |
| TC-FE-02 | Fail login schema on invalid email format | `authSchemas.test.ts` | PASS |
| TC-FE-03 | Fail login schema on empty password | `authSchemas.test.ts` | PASS |
| TC-FE-04 | Validate register schema with matching passwords | `authSchemas.test.ts` | PASS |
| TC-FE-05 | Fail register schema on password mismatch | `authSchemas.test.ts` | PASS |
| TC-FE-06 | Fail register schema on password < 8 characters | `authSchemas.test.ts` | PASS |
| TC-FE-07 | Fail register schema on full_name < 2 characters | `authSchemas.test.ts` | PASS |
| TC-FE-08 | Render LoginPage elements properly | `LoginPage.test.tsx` | PASS |
| TC-FE-09 | Display field-level validation errors on empty login submit | `LoginPage.test.tsx` | PASS |
| TC-FE-10 | Render RegisterPage elements properly | `RegisterPage.test.tsx` | PASS |
| TC-FE-11 | Display field-level validation errors on empty register submit | `RegisterPage.test.tsx` | PASS |
| TC-FE-12 | Validate password mismatch in UI | `RegisterPage.test.tsx` | PASS |

---

## Neon PostgreSQL Verification Matrix (Section 3.6 & 3.7)

| Verification Check | Target | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| **Database Connectivity** | `current_database()` | `neondb` | `neondb` | **VERIFIED** |
| **Application Role** | `current_user` | `main_dev` | `main_dev` | **VERIFIED** |
| **Engine & Version** | `version()` | PostgreSQL 18.x | PostgreSQL 18.6 | **VERIFIED** |
| **Pending Migration Check** | `makemigrations --check` | Clean | `No changes detected` | **VERIFIED** |
| **Migration Execution** | `migrate` | 19 migrations | 19 applied OK | **VERIFIED** |
| **Schema Integrity** | `users` table | `users_pkey` (UUID), `users_email_key` | Confirmed in `pg_constraint` | **VERIFIED** |
| **Registration Workflow** | `/api/v1/auth/register/` | 201 Created & Neon persistence | User created in Neon, PBKDF2 hashed | **VERIFIED** |
| **Duplicate Rejection** | `/api/v1/auth/register/` | 400 Bad Request | Duplicate email rejected | **VERIFIED** |
| **Login Workflow** | `/api/v1/auth/login/` | 200 OK & session established | Session active | **VERIFIED** |
| **Profile Retrieval** | `/api/v1/auth/me/` | 200 OK | Profile returned | **VERIFIED** |
| **Session Invalidation** | `/api/v1/auth/logout/` | 200 OK -> subsequent 401 | Invalidated, 401 returned | **VERIFIED** |
| **Multi-user Isolation** | `/api/v1/auth/me/` | User B cannot view User A | Verified isolation | **VERIFIED** |
| **Secret Exemption** | `git check-ignore` | Ignored by Git | `backend/.env` is ignored | **VERIFIED** |
