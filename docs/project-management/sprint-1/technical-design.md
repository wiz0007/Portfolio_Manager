# Sprint 1 — Technical Architecture & Design Document

## Backend Architecture
- **Framework:** Django 5.1 + Django REST Framework 3.15
- **Custom User Model:** `apps.users.models.User`
  - Inherits `AbstractBaseUser`, `PermissionsMixin`
  - Primary Key: UUID (`uuid.uuid4`)
  - Unique field: `email` (normalized, indexed)
  - Profile field: `full_name`
  - Timestamps: `date_joined`, `updated_at`
  - Status flags: `is_active`, `is_staff`, `is_superuser`
- **Authentication Scheme:**
  - `core.authentication.EnforcedSessionAuthentication` (HTTP-only session cookie)
  - Session key cycled on login to eliminate session fixation
  - Rate limiting via ScopedRateThrottle (`15/minute` on auth endpoints)
  - CSRF cookie (`csrftoken`) and `X-CSRFToken` verification on unsafe HTTP methods
- **API Endpoints:**
  - `GET /api/v1/auth/csrf/`: CSRF initialization
  - `POST /api/v1/auth/register/`: Account creation & session establishment
  - `POST /api/v1/auth/login/`: User authentication & session establishment
  - `POST /api/v1/auth/logout/`: Invalidate session and flush cookie
  - `GET /api/v1/auth/me/`: Current user profile (requires authentication)
- **API Documentation:**
  - OpenAPI 3.0 schema generation using `drf-spectacular`
  - Available at `/api/schema/`, `/api/docs/` (Swagger UI), and `/api/redoc/`

## Frontend Architecture
- **Framework:** React 18 + Vite + TypeScript
- **State Management:**
  - TanStack Query (`@tanstack/react-query`) for server state and user session caching
- **Form Management & Validation:**
  - React Hook Form + Zod (`registerSchema`, `loginSchema`)
- **API Client:**
  - Centralized client in `src/services/api/client.ts`
  - Cookie credentials mode (`credentials: 'include'`)
  - Automatic CSRF token extraction and `X-CSRFToken` header injection
  - Normalized error response handling
- **Routing & Navigation:**
  - React Router DOM v6
  - `ProtectedRoute`: Verifies session with backend, displays loading state, redirects unauthenticated users to `/login`
  - `PublicOnlyRoute`: Redirects authenticated users to `/dashboard`
- **Styling:**
  - Tailwind CSS with responsive layout and dark theme
