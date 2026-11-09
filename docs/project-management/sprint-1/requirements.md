# Sprint 1 Requirements: Project Foundation & Authentication

## Goal
Establish the application foundation and allow a user to register, log in, and maintain a secure authenticated session.

## User Stories
1. **User Registration:** As a prospective user, I want to create an account using my email and a strong password so that I can start tracking my portfolios.
2. **User Login:** As an existing user, I want to securely log in so that I can access my private financial data.
3. **Session Persistence:** As an authenticated user, my session should remain active across page reloads.
4. **Current User Profile:** As an authenticated user, the application should fetch my account details via `/api/v1/auth/me/`.
5. **User Logout:** As an authenticated user, I want to log out and invalidate my session securely.

## Acceptance Criteria
- User can register with valid email and password.
- Duplicate email registration returns a descriptive 400 validation error.
- Invalid credentials return 401 Unauthorized.
- Passwords are encrypted with Django's password hasher.
- Unauthenticated requests cannot access protected endpoints.
- Frontend forms display server validation errors accurately.
