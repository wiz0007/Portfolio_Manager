# Sprint 1 — Engineering Requirements: Foundation, Authentication & Neon PostgreSQL

**Status:** Implementation Complete & Verified  
**Version:** 1.1  
**Phase:** Sprint 1  
**Database Provider:** Neon PostgreSQL (`neondb`, AWS ap-southeast-1)

## 1. Objectives & Scope
Establish foundational application architecture and implement a complete, secure authentication system connecting frontend and backend, backed by Neon PostgreSQL.

### Functional Requirements Delivered
- **FR-01: User Registration**
  - Full Name, Email, Password, Password Confirmation
  - Email normalization, database uniqueness constraint
  - Password strength validation via Django's password validators
  - Passwords hashed using PBKDF2/SHA256, never stored in plain text
- **FR-02: User Login**
  - Email & Password input with rate limiting
  - Generic authentication failure ("Invalid email or password.")
  - Establishes HTTP-only session cookie with session ID regeneration
- **FR-03: Current User Profile**
  - Authenticated endpoint `GET /api/v1/auth/me/` returning public profile
  - Unauthenticated requests return `401 Unauthorized`
- **FR-04: User Logout**
  - `POST /api/v1/auth/logout/` invalidating session and clearing cookies
- **FR-05: Protected Routes**
  - Client-side navigation guards for `/dashboard`, `/settings/profile`, `/settings/account`
  - Public routes `/login`, `/register` redirecting to dashboard when authenticated
- **CSRF Token Handling**
  - `GET /api/v1/auth/csrf/` endpoint providing CSRF token and setting cookie

## 2. Neon PostgreSQL Integration & Database Hardening
- **Database Engine:** PostgreSQL 18 (Neon Serverless)
- **Database Name:** `neondb`
- **Application Role:** `main_dev`
- **Environment Management:** Connection read securely from `backend/.env` via `DATABASE_URL` (excluded from git tracking).
- **Migration Execution:** 19 migration records applied in dependency order.
- **Constraints Verified:** UUID primary key (`users_pkey`) and unique email constraint (`users_email_key`) verified on table `users`.
- **Driver Architecture:** Centralized configuration supporting Psycopg 3 in standard/Linux/Docker environments with pure-Python SSL adapter fallback for restricted platforms.
