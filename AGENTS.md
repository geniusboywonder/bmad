# Repository Guidelines

## Code Standards

**IMPORTANT**: Always read and follow `docs/CODEPROTOCOL.md` before making any code changes. This file contains the complete development workflow, quality standards, and enforcement rules that must be followed for every task.
Read and follow the front-end style guide in `docs/STYLEGUIDE.md` before making any front-end changes.
Read and follow the SOLID principles in `docs/SOLID.md`.
Read and follow the architecture in `docs/architecture/architecture.md`.
Read and follow the test protocal in `docs/TESTPROTOCOL.md` before running any tests.

**ALWAYS USE A TODO LIST TO PLAN YOUR STEPS AND TRACK PROGRESS. UPDATE THE TODO AS YOU FINISH EACH STEP. THE TODO SHOULD INCLUDE BETWEEN 5-10 STEPS, THE MORE GANULAR THE BETTER**

Automatically run the `/compact` command when the context window reaches 5% remaining.

## Project Structure & Module Organization

The repository centers on `backend/` for FastAPI services and Celery workers, plus `frontend/` for the Next.js UI. API handlers live in `backend/app/api/`, domain logic in `backend/app/services/`, and tests under `backend/tests/`. UI routes sit inside `frontend/app/`, reusable pieces in `frontend/components/`, and Vitest specs in `frontend/tests/`. Process docs stay in `docs/`; deployment helpers live in `scripts/` and `deploy.py`.

## Build, Test, and Development Commands

- `cd backend && ./scripts/start_dev.sh`: boot the FastAPI server with Celery and support services for local work.
- `cd backend && uvicorn app.main:app --reload`: run only the API for quick iteration.
- `cd backend && pytest`: execute backend unit and integration tests with marker awareness.
- `cd frontend && npm install && npm run dev`: install UI deps and start the Next.js dev server.
- `cd frontend && npm run test` or `npx playwright test`: run Vitest suites or Playwright end-to-end checks.

## Coding Style & Naming Conventions

Python code uses Black (88-character lines) and isort; keep type hints, snake_case modules, and PascalCase classes. Frontend code follows ESLint/Next defaults, PascalCase components, hooks prefixed with `use`, and kebab-case route files. Tailwind tokens and base styles stay in `frontend/styles/`; reuse variables instead of hard-coded colors.

## Testing Guidelines

Use `pytest` markers (`real_data`, `external_service`, etc.) to declare integration depth and keep new tests in `backend/tests/test_*.py`. Frontend unit tests belong beside the component or within `frontend/tests/` as `*.spec.tsx`. Playwright suites live in `frontend/tests/e2e/`; refresh snapshots with `npx playwright test --update-snapshots`. Cover success, failure, and edge states for every change.

## Commit & Pull Request Guidelines

Adopt the Conventional Commits pattern already in history (`feat:`, `fix:`, `docs:`, etc.) and keep subject lines under 72 characters. Each PR should explain user impact, highlight touched areas (`backend`, `frontend`, infra), list validation commands, and link issues. Attach screenshots or recordings for UI changes and confirm lint/test jobs before requesting review.

## Security & Configuration Tips

Copy `backend/env.example` to `.env` (or `env.sqlite.example` for SQLite) and never check secrets into git. Frontend secrets belong in `frontend/.env.local`, while cloud credentials should follow `gcp-service-account-template.json`. Keep Docker, database, and Redis ports aligned with the samples, and rotate API keys referenced by deployment scripts.
