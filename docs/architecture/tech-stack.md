# Technology Stack (2025-10-10)

## Backend

- **Runtime:** Python 3.11+, FastAPI 0.118, Uvicorn ASGI.
- **Agents:** Google ADK 1.16.0 (`LlmAgent`), LiteLLM 1.77.7 for multi-provider routing.
- **Task Execution:** Celery 5.3 with Redis broker/result backend.
- **Data Layer:** PostgreSQL 13+, SQLAlchemy 2.0, Alembic migrations.
- **Caching & Counters:** Redis 6 (single database) for Celery queues, WebSocket sessions, and HITL limits.
- **Safety Services:** `HitlCounterService`, `HitlApprovalService`, `HitlSafetyService`, `StartupService` (queue cleanup + stale approval rejection).
- **Observability:** Structlog JSON logs, `/health` endpoints, WebSocket safety events.

## Frontend

- **Framework:** Next.js 15 (App Router) with React 19 and TypeScript 5.
- **State & Styling:** Tailwind CSS, Zustand, Sonner toasts, lucide-react icons.
- **Copilot Integration:** CopilotKit 1.10.6 (`@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime`).
- **Real-time:** Enhanced WebSocket client (auto reconnect, project scope).
- **HITL UI:** `HITLReconfigurePrompt` locks after action; toasts link back to the prompt.
- **Build Tooling:** ESLint, Prettier, Next bundler (SWC/Turbopack), Vitest/React Testing Library (tests WIP).

## Shared Infrastructure

- **Configuration:** `.env` (backend), `.env.local` (frontend) control database/Redis URLs, API keys, HITL defaults.
- **Scripts:** `scripts/start_dev.sh` launches FastAPI, Celery, Redis, Postgres for local runs.
- **Package Management:** `backend/requirements.txt`, `frontend/package.json` (Node 18+ recommended).

## HITL Tool Flow (Stack Dependencies)

1. `HitlCounterService` (Redis script) gates the task before execution.  
2. `ADKAgentExecutor` tells the LLM to call `reconfigureHITL`.  
3. CopilotKit action renders `HITLReconfigurePrompt`, calls `/api/v1/hitl/settings/{projectId}`.  
4. `HITLSafetyService` broadcasts updates; `HITLAwareLlmAgent` trims the tool call and reruns the conversation.
