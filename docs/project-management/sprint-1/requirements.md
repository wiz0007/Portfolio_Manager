# Sprint 1 — Engineering Requirements: Foundation & Authentication

**Status:** Implementation Complete & Verified  
**Version:** 1.0  
**Phase:** Sprint 1

## 1. Objectives & Scope
Establish foundational application architecture and implement a complete, secure authentication system connecting frontend and backend.

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
