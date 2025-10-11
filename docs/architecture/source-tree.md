# Source Tree Overview

```
bmad/
├── backend/               FastAPI application
│   ├── app/
│   │   ├── api/           REST & WebSocket endpoints
│   │   ├── agents/        ADK agent wrappers and persona markdown
│   │   ├── copilot/       CopilotKit runtime + HITL-aware agent
│   │   ├── services/      Business services (HITL, orchestrator, context, startup)
│   │   ├── tasks/         Celery task definitions
│   │   └── settings.py    Pydantic configuration (DB, Redis, HITL defaults)
│   ├── alembic/           Database migrations
│   └── requirements.txt   Python dependencies (FastAPI, google-adk, litellm, etc.)
├── frontend/              Next.js + CopilotKit UI
│   ├── app/               App Router pages (`copilot-demo`, dashboards, API routes)
│   ├── components/        Shared UI, HITL prompt, Sonner toaster wrapper
│   ├── lib/               Zustand stores, services, utilities
│   ├── public/            Static assets
│   └── package.json       Node dependencies (Next.js, CopilotKit 1.10.6)
├── docs/                  Architecture, changelog, process notes
└── scripts/               Operational helpers (e.g., `start_dev.sh`)
```

### HITL-related Highlights

- **Frontend:**  
  - `app/copilot-demo/page.tsx` – registers the `reconfigureHITL` Copilot action and renders the prompt.  
  - `components/hitl/HITLReconfigurePrompt.tsx` – approval UI that locks after a decision.
- **Backend:**  
  - `services/hitl_counter_service.py` – Redis-backed counter + settings.  
  - `agents/adk_executor.py` – governor that instructs the LLM to call the tool.  
  - `copilot/hitl_aware_agent.py` – processes tool results and resumes execution.  
  - `api/hitl_simplified.py` – eight essential HITL endpoints.
