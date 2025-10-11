# Reconfigure HITL Investigation

**Author:** Codex (GPT-5)  
**Date:** 2025-10-10

## Executive Summary
- The `reconfigureHITL` CopilotKit action was briefly replaced and then restored on Oct 8 before being removed again on Oct 9; current code instructs agents to emit `<hitl-approval>` markdown tags instead of calling the tool.
- Backend governors (`backend/app/agents/adk_executor.py:90` and `backend/app/copilot/hitl_aware_agent.py:34`) still expect the tool call, so the present frontend change leaves the two halves misaligned.
- Documented failures stem from LiteLLM rejecting deferred tool responses plus UI handler issues (`docs/CHANGELOG.md:18-27`, `docs/architecture/HITL/HITL-UI-FIXES-SUMMARY.md:78`) rather than an incompatibility in CopilotKit itself.
- Re-enabling the action without first addressing the synchronous response requirement or upgrading CopilotKit will recreate the reported errors.

## History and Removal Timeline
- `fc30231332df030a57b352ca587554d6a456b4dd` (2025-10-08): Removed the action in favor of a WebSocket event, introduced `POST /api/v1/hitl/settings/{project_id}`.
- `46e26b7284e58894b37dbf0fb0ed37688afcca3f` (2025-10-08, minutes later): Reintroduced the native CopilotKit action with `useCopilotAction`.
- `e27d9e79b3af4b4d191e74bd2c62a802c989fcd3` (2025-10-09): Removed the action again, added markdown-based approvals, and documented tool-call failures in the changelog.

## Current Implementation Snapshot
- **Frontend (`frontend/app/copilot-demo/page.tsx:238-301`)**: Registers a `<hitl-approval>` markdown renderer, deduplicates requests via `createdApprovalIds`, and relies on the HITL store to surface inline approvals. Agents are told “Do not call frontend tools directly.”
- **Backend Governor (`backend/app/agents/adk_executor.py:90-105`)**: Still forces the LLM to call `reconfigureHITL` when the counter expires and passes current settings for the prompt.
- **Tool Result Handler (`backend/app/copilot/hitl_aware_agent.py:34-79`)**: Parses the tool payload and updates Redis via `HitlCounterService`. Without an actual tool result, this code path is never exercised.
- **Documentation (`docs/CHANGELOG.md:18-43`)**: Attributes failures to LiteLLM bad requests, broken async handler plumbing, and undefined action references.

## Documented Failure Modes
- `litellm.BadRequestError`: Triggered because the action handler deferred completion using an unresolved promise; LiteLLM expects an immediate tool response.
- `props.done is not a function` and `reconfigureHITL is not defined`: Caused by incorrect handler wiring and passing `actions` props that CopilotKit already supplies.
- Infinite re-render loop: The markdown renderer previously returned `null`, repeatedly calling `addRequest()`; fixed with the `createdApprovalIds` guard (`docs/architecture/HITL/HITL_INFINITE_LOOP_FIX.md:10-82`).

## Dependency Landscape
- CopilotKit packages remain on `@copilotkit/react-core@1.10.5` / `@copilotkit/react-ui@1.10.5` (`frontend/package.json`).
- Backend integration relies on `ag_ui_adk==0.3.1` and `google-adk==1.15.1` (`backend/requirements.txt`).
- No upgrades to the latest ADK, AG-UI, or CopilotKit releases have been attempted since the failures were logged.

## Reimplementation Assessment
- **Option A – Restore Tool Call**: Requires solving the synchronous response issue (e.g., ref-based resolver that immediately resolves the handler promise) or upgrading CopilotKit/LiteLLM to versions supporting deferred responses. Without that, the LiteLLM bad-request error will recur.
- **Option B – Keep Markdown Path**: Demands disabling the governor’s forced tool call and updating agent prompts to emit markdown consistently; otherwise backend assumptions remain broken.
- **Option C – Upgrade Dependencies First**: Test the latest CopilotKit/ADK/AG-UI releases in isolation to confirm whether the tool-call flow now supports deferred UI interactions before re-enabling it.

## Recommended Next Steps
1. Decide on the preferred interaction model (tool call vs. markdown) to align frontend prompts and backend governors.
2. If retaining tool calls, implement a synchronous handler response pattern or prototype against the newest CopilotKit release to verify native support.
3. If committing to markdown, remove the forced `reconfigureHITL` instruction from `ADKAgentExecutor`, adjust agent prompts, and retire the unused tool-result handler.
4. After changes, exercise the Copilot demo manually (`npm run dev`) with the backend running to confirm the counter exhaustion flow and watch for LiteLLM errors.

## Open Questions
- Are the agent markdown prompts still instructing the LLM to call `reconfigureHITL`, and should they be updated to match the chosen approach?
- Does a newer CopilotKit runtime resolve the synchronous tool-response limitation without custom plumbing?
- Should the Redis-backed counter migrate to a persistent store before further refactors (as raised in `docs/HITL_TOGGLE_COUNTER_SIMPLIFIED_PLAN.md`)?
