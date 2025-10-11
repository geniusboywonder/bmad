## 2025-10-07 13:55 UTC

- Documented current HITL approval updates with single-action enforcement and action feedback.
- Backend now records human decision via `process_approval_response` and emits WebSocket events.
- Frontend HITL store/chat display persist chosen action and hide buttons post-selection.
- Vitest suite (`hitl-store`) passing; Playwright run (chromium) blocked by sandbox port restrictions.

## 2025-10-07 14:12 UTC

- Refreshed architecture, source-tree, and tech-stack docs to describe the new `HitlAction` workflow and frontend decision persistence.
- Documented websocket `HITL_RESPONSE` metadata and inline approval locking behavior.

## 2025-10-07 16:45 UTC

- Implemented Redis-backed HITL counter service with FastAPI endpoints for toggling, updating limits, and continue/stop actions.
- Updated Celery task pipeline to auto-approve when allowed, decrement counters, and broadcast counter events when thresholds are reached.
- Added HITL counter settings to the Zustand store, websocket sync, and a new chat message card with toggle plus Continue/Stop controls.
- Extended tests (`frontend/lib/stores/hitl-store.test.ts`) covering server-applied settings and reran Vitest (`npm run test -- hitl-store`).

## 2025-10-07 15:08 UTC

- Captured agent policy enforcement requirements and developer plan.
- Logged step-by-step rollout tasks in `docs/PLAN.md` and drafted standalone roadmap (`docs/policy-agent-policy-plan.md`).
- Updated changelog to flag the new policy workstream documentation.

## 2025-10-08 09:37 UTC

- Added shared `policyGuidance` state to the app store and wired enhanced websocket handling so blocked tasks broadcast structured context.
- Updated `frontend/app/copilot-demo/page.tsx` to surface phase-aware guidance, restrict disallowed agent toggles, and mirror policy toasts.
- Gated chat submission in `frontend/components/chat/copilot-chat.tsx`, parsing REST errors into guidance and disabling input when agents are off-limits.
- Introduced `buildPolicyGuidance` helper plus new vitest suites (`policy-utils.test.ts`, `copilot-chat.policy.test.tsx`) covering normalization and UI gating.

## 2025-10-09 14:28 UTC

- Refactored `frontend/app/copilot-demo/page.tsx` to drop the `reconfigureHITL` Copilot action in favor of markdown-driven approvals.
- Registered a `<hitl-approval>` renderer that persists approvals via the HITL store and shows `InlineHITLApproval` inline cards.
- Updated agent-facing instructions/status copy and cleaned unused imports to reflect the markdown-based flow.
- Validation: queued targeted frontend tests; requires environment time to execute.

## 2025-10-09 14:36 UTC

- Introduced `frontend/components/ui/sonner.tsx` and wired the global `Toaster` through `ClientProvider` per shadcn guidance.
- Replaced `MainLayout`'s `HITLAlertsBar` with toast notifications keyed by approval ID, preventing duplicate banners.
- Removed the per-page `Toaster` instance from `copilot-demo` so all notifications route through the shared Sonner container.
- Testing: pending manual verification and Vitest/Playwright smoke runs once the environment is available.
