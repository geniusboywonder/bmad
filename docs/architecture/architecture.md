# BMAD Architecture

_Last updated: 2025-10-10_

BMAD is a two-tier platform that pairs a FastAPI backend with a Next.js (App Router) frontend. The system coordinates Google ADK agents, persists state in PostgreSQL, and enforces human-in-the-loop (HITL) safety through a Redis-backed governor and CopilotKit native actions.

---

## 1. Platform Overview

- **Frontend:** Next.js 15 + React 19, TypeScript, Tailwind, Zustand, CopilotKit UI.
- **Backend:** FastAPI (async), Uvicorn, Google ADK agent runtime, Celery workers.
- **Persistence:** PostgreSQL for durable data, Redis for queues/counters.
- **Messaging:** WebSockets for agent progress, safety alerts, and HITL notifications.
- **Orchestration:** Celery executes agent jobs; settings and budget controls guard every task.
- **Deployment Notes:** `.env` values configure API keys, database/Redis URLs, and default HITL behaviour.

---

## 2. Frontend Architecture

### 2.1 Application Shell

- App Router pages under `frontend/app/`; shared UI in `frontend/components/`.
- `ClientProvider` wraps the tree with ThemeProvider, WebSocketProvider, AgentProvider, CopilotKit, and Sonner `Toaster`.
- State is stored in small Zustand slices (e.g. `agent-context`, `app-store`, `hitl-store`).
- WebSocket `EnhancedWebSocketClient` streams policy violations, HITL events, and agent status into the stores.

### 2.2 Copilot & HITL Flow

- The Copilot demo (`frontend/app/copilot-demo/page.tsx`) renders CopilotKit’s `CopilotSidebar`.
- Instructions now state: “When you need approval, call the `reconfigureHITL` tool. Default settings are limit = 10, enabled = true unless the user has changed them.”
- `useHumanInTheLoop("reconfigureHITL")` registers the HITL prompt and returns a render callback that waits for the user’s decision.  
  - **Handler:** raises a toast (“Analyst requires your attention…”) with a “Review” button that scrolls to the prompt.  
  - **Render:** mounts `HITLReconfigurePrompt`, writes REST updates to `/api/v1/hitl/settings/{projectId}`, and resolves the Promise to unblock the backend.
- `HITLReconfigurePrompt` locks once a decision is made: inputs become read-only and the chosen button displays as disabled while alternatives disappear.
- Policy violations open a banner via Zustand; toasts and inline UI share a single Sonner instance.

---

## 3. Backend Architecture

### 3.1 Service Layout

- Entry point: `app/main.py` (FastAPI app, lifespan startup that flushes stale Redis keys and HITL approvals).
- API packages under `app/api/` (projects, agents, artifacts, audit, health, system, simplified HITL, CopilotKit).
- Services in `app/services/` encapsulate orchestration, context storage, safety, and workflow logic.
- Agent runtime:
  - `app/agents/adk_executor.py` wraps Google ADK `LlmAgent`.
  - `app/copilot/adk_runtime.py` exposes per-agent HTTP endpoints for CopilotKit.
  - `app/copilot/hitl_aware_agent.py` intercepts `reconfigureHITL` tool results.
- Background work: Celery tasks (`app/tasks/agent_tasks.py`) orchestrate agent execution and call the executor.

### 3.2 Data & Infrastructure

- **PostgreSQL:** projects, tasks, agent status, context artifacts, HITL approvals, audit log.
- **Redis:** single database for Celery queues, WebSocket sessions, and the HITL counter (`hitl:project:{uuid}` hash storing `enabled`, `limit`, `remaining`).
- **Celery:** broker/backend Redis; purged on startup by `startup_service.perform_startup_cleanup()`.
- **Configuration:** `app/settings.py` (Pydantic settings) exposes defaults such as `hitl_default_counter=10`, `hitl_default_enabled=True`.

### 3.3 Agent Execution Flow

1. API request creates a task record and enqueues a Celery job.
2. Celery worker calls `ADKAgentExecutor.execute_task`.
3. HITL counter is checked via `HitlCounterService`.  
   - If limit remains, counter decrements and the agent runs immediately.  
   - If exhausted, the executor sends a governor message instructing the LLM to call `reconfigureHITL`.
4. Google ADK streams responses; if the last message is a tool result, `HITLAwareLlmAgent` parses the JSON, updates Redis, strips the tool call from history, and reruns the conversation.

---

## 4. Human-in-the-Loop Workflow

### 4.1 End-to-End Sequence

```
User request (frontend) ──▶ FastAPI /projects → Celery task queued
                               │
                               ▼
                         Celery worker
                               │
                               ├─▶ HitlCounterService (Redis hash)
                               │     • remaining > 0 → decrement & execute
                               │     • remaining == 0 → governor message
                               │
                               ▼
                      ADKAgentExecutor (Google ADK)
                               │
                               ├─▶ LLM executes task
                               └─▶ LLM issues tool call `reconfigureHITL`
                                         │
                                         ▼
                    CopilotKit action handler (frontend)
                      ├─ shows toast “{Agent} requires your attention…”
                      ├─ scrolls to HITLReconfigurePrompt (locks after decision)
                      └─ resolves tool call with `{ newLimit, newStatus, stop }`
                                         │
                                         ▼
                    HITLAwareLlmAgent (backend)
                      ├─ parses JSON result, updates Redis counter/toggle
                      └─ trims tool call then replays conversation
                                         │
                                         ▼
                    Task completes → HitlAgentApprovalDB updated, WebSocket events broadcast
```

### 4.2 Key Points

- Counter defaults come from `settings.hitl_default_counter` (10) and can be overridden per project.
- The front-end prompt locks after the first decision, preventing conflicting updates.
- Toast action anchors the user back to the relevant chat message.
- `HITLSafetyService` records the final approval decision; downstream services read `HitlAgentApprovalDB` before continuing work.
- Policy enforcement is applied twice: once when REST clients create tasks, and again inside `HITLAwareLlmAgent` for CopilotKit sessions (denied agents return a violation message and trigger a WebSocket event).

---

## 5. Observability & Health

- **Logging:** `structlog` JSON logs with request IDs and event metadata.
- **Health checks:** `/health` (fast) and `/health/detailed` (database, Redis, Celery, LLM providers).
- **WebSocket Monitoring:** Safety events (policy, HITL, emergency stop) are broadcast through the WebSocket manager for real-time dashboards.
- **Startup Diagnostics:** Queue flushing and stale approval rejection are logged on launch; errors surface in the console to catch missing Redis/Celery dependencies.

---

## 6. Key Source Locations

- `frontend/app/copilot-demo/page.tsx` – Copilot demo, HITL action registration, UI glue.
- `frontend/components/hitl/HITLReconfigurePrompt.tsx` – Inline approval prompt.
- `backend/app/services/hitl_counter_service.py` – Redis-backed auto-approval governor.
- `backend/app/agents/adk_executor.py` – ADK execution wrapper and governor logic.
- `backend/app/copilot/hitl_aware_agent.py` – Tool-result handler that resumes conversations.
- `backend/app/api/hitl_simplified.py` – Eight essential HITL endpoints.

This document reflects the current, tool-driven HITL implementation and replaces older markdown-centric descriptions.
