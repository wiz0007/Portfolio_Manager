# Sprint 1 Technical Design

## Backend
- **Custom User Model:** `apps.users.models.User` extending `AbstractBaseUser` / `PermissionsMixin`. Primary key: UUID or BigAuto, email field unique, is_active, date_joined.
- **Authentication Endpoints:**
  - `POST /api/v1/auth/register/`
  - `POST /api/v1/auth/login/`
  - `POST /api/v1/auth/logout/`
  - `GET /api/v1/auth/me/`
- **Security:** CSRF protection, HTTPS-ready cookie flags, password validators.

## Frontend
- React Router routes for `/login` and `/register`.
- React Hook Form + Zod schema validation.
- Auth Context / TanStack Query hook `useAuth()` to manage session state.
