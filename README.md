# Portfolio Manager

A scalable, multi-asset portfolio management and financial intelligence platform designed to help users track, analyze, and optimize investments held across different asset classes (stocks, mutual funds, crypto, gold, real estate, and more).

## Tech Stack

- **Frontend:** React + TypeScript + Vite, Tailwind CSS, TanStack Query, React Router, React Hook Form + Zod, Lucide Icons.
- **Backend:** Python 3.12 + Django + Django REST Framework (Domain-Oriented Modular Monolith), Neon PostgreSQL.
- **API Contracts:** OpenAPI 3.0 via `drf-spectacular`.
- **Security:** Session-based authentication with HTTP-only cookies, CSRF protection, cryptographic signed email verification, and strict user ownership isolation.
- **Testing:** Pytest (54 backend tests) and Vitest (26 frontend tests).
- **CI/CD:** GitHub Actions shared workflows (linting, system checks, migration consistency, isolated PostgreSQL testing, and frontend bundle build).

---

## Monorepo Structure

```text
Portfolio_manager/
├── frontend/             # React + TypeScript + Vite SPA
├── backend/              # Django + DRF modular monolith
├── infrastructure/       # Docker & deployment configs
├── docs/                 # Architecture, domain models, and sprint roadmaps
└── .github/              # CI/CD workflows
```

---

## Branching & Release Strategy

- `production` - Untouched baseline production branch.
- `staging` - Pre-production / staging integration branch.
- `sprint-*` - Sprint feature branches (e.g., `sprint-1`, `sprint-2`, `sprint-3`, `sprint-4`). All changes are submitted as Pull Requests into `staging`.

---

## API Endpoints (MVP Foundation)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/health/` | System & DB health probe | No |
| `GET` | `/api/v1/auth/csrf/` | Initialize CSRF token | No |
| `POST` | `/api/v1/auth/register/` | Register new account & send verification email | No |
| `POST` | `/api/v1/auth/verify-email/` | Verify signed cryptographic token | No |
| `POST` | `/api/v1/auth/resend-verification/` | Throttled email verification resend | No |
| `POST` | `/api/v1/auth/login/` | Authenticate & create session | No |
| `POST` | `/api/v1/auth/logout/` | Invalidate session | No |
| `GET` | `/api/v1/auth/me/` | Current user profile & verification status | Yes |
| `PATCH` | `/api/v1/users/me/` | Update user profile | Yes |
| `GET` | `/api/v1/dashboard/overview/` | Dashboard stats & real user portfolios | Yes |
| `GET` | `/api/v1/portfolios/` | List user's portfolios | Yes |
| `POST` | `/api/v1/portfolios/` | Create a new portfolio | Yes |
| `GET` | `/api/v1/portfolios/<uuid:id>/` | Retrieve portfolio details | Yes |
| `PATCH` | `/api/v1/portfolios/<uuid:id>/` | Update portfolio metadata | Yes |
| `DELETE` | `/api/v1/portfolios/<uuid:id>/` | Delete portfolio | Yes |

---

## Quick Start (Local Development)

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements/development.txt
python manage.py migrate
python manage.py runserver
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`, Backend runs on `http://localhost:8000`.

---

## Running Test Suites

### Backend Tests (Pytest & Ruff)

```bash
cd backend
pytest
ruff check
```

### Frontend Tests (Vitest & Typecheck)

```bash
cd frontend
npm run typecheck
npm run test
npm run build
```
