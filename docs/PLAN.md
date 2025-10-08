## 2025-10-07 13:41 UTC

- [x] Audit current HITL frontend/backend flow for action lifecycle and websocket updates.
- [x] Update backend approval endpoint to persist explicit actions and broadcast the selection.
- [x] Refine inline HITL UI to enforce single action selection and display the chosen action.
- [x] Update stores/websocket handlers/tests to surface final action state in chat.
- [ ] Validate changes with Playwright MCP run and document results (blocked: sandbox cannot open dev server port for Playwright).

## 2025-10-07 14:05 UTC

- [x] Review architecture docs for outdated HITL action handling descriptions.
- [x] Update source tree documentation to note new HITL processing points and store metadata.
- [x] Refresh tech stack documentation with current HITL frontend/backend responsibilities.

## 2025-10-07 14:25 UTC

- [x] Audit current HITL counter implementation across backend services, stores, and UI.
- [x] Implement auto-approval gating: respect toggle, decrement counter, prevent auto-processing at zero.
- [x] Render HITL counter limit message with toggle and Continue/Stop controls when limit reached.
- [x] Update tests (store + components) and document changes.

## 2025-10-07 15:02 UTC

- [ ] Confirm phase definitions, deliverables, and any agent overrides with product/ops to anchor the policy scope.
- [ ] Draft a phase→agent policy configuration with optional prompt tags so analysts, architects, etc. remain available for phase-relevant questions.
- [ ] Implement a `PhasePolicyService` that inspects project phase, requested agent, and prompt heuristics (keywords, deliverable references) to return allow/deny/review decisions.
- [ ] Integrate policy checks into all task creation paths (orchestrator core, REST task endpoint, websocket chat) while preserving direct chat UX for compliant prompts.
- [ ] Provide structured denial responses and websocket notices explaining blocked requests and listing currently available agents.
- [ ] Add unit/integration coverage for allowed, denied, and override scenarios plus prompt-classification edge cases.
- [ ] Document configuration/tuning guidance and note any follow-up work (advanced NLP, admin override UI) in `docs/CHANGELOG.md` and project notes.

## 2025-10-08 09:37 UTC

- [x] Extend app store with shared policy guidance state and normalize websocket payloads.
- [x] Surface current-phase policy guidance on `copilot-demo` page and gate agent selection based on allowed roles.
- [x] Parse policy-aware task creation errors in chat, disable input when agents are blocked, and show clarification messaging.
- [x] Add vitest coverage for policy normalization helper and chat input gating scenarios.
- [x] Run targeted frontend test suite (`npm run test -- policy-utils.test.ts copilot-chat.policy.test.tsx`) to validate policy gating.
