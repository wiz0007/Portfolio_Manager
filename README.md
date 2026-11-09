# Portfolio Manager

A scalable, multi-asset portfolio management and financial intelligence platform designed to help users track, analyze, and optimize investments held across different asset classes (stocks, mutual funds, crypto, gold, real estate, and more).

## Tech Stack

- **Frontend:** React 19 + TypeScript + Vite, Tailwind CSS + shadcn/ui, TanStack Query, React Router, React Hook Form + Zod, Apache ECharts.
- **Backend:** Python + Django + Django REST Framework (Domain-Oriented Modular Monolith), PostgreSQL, Redis, Celery.
- **AI Analytics:** OpenAI API server-side integration (post-foundation phase).
- **API Contracts:** OpenAPI schemas.
- **Containerization:** Docker & Docker Compose.

## Monorepo Structure

```text
Portfolio_manager/
├── frontend/             # React + TypeScript + Vite SPA
├── backend/              # Django + DRF modular monolith
├── contracts/            # OpenAPI specifications and generated types
├── infrastructure/       # Docker, Nginx, deployment & monitoring configs
├── docs/                 # Architecture, domain models, and sprint roadmaps
└── .github/              # CI/CD workflows
```

## Branching Strategy

- `production` - Production deployable branch (default branch)
- `staging` - Pre-production / staging environment branch
- `feature/*` - Sprint and feature branches

## Quick Start (Local Development)

### Prerequisites

- Node.js >= 18
- Python >= 3.11
- Docker & Docker Compose

### Running with Docker Compose

```bash
docker compose up -d
```

Frontend will be available at `http://localhost:5173` and Backend at `http://localhost:8000`.
