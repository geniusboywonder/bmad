# Agent Policy Enforcement Rollout Plan

## Context

Direct agent chats currently bypass workflow sequencing. Users can target any agent and send arbitrary prompts, and the orchestrator dutifully queues the task without verifying that the request aligns with the project’s SDLC phase. We need policy checks that still let users ask phase-relevant questions while blocking off-phase or unrelated work.

## Objectives

- Preserve the direct chat experience when prompts align with the active phase deliverables.
- Enforce phase→agent routing rules so off-phase tasks are rejected with clear guidance.
- Provide a foundation for richer heuristics (NLP, admin overrides) without breaking existing workflows.

## Work Breakdown

1. **Requirements Alignment**
   - Catalogue SDLC phases, their deliverables, and valid agent roles.
   - Identify exceptions (e.g., emergency recovery, admin override).
   - Define the user messaging tone for blocked requests.

2. **Policy Definition**
   - Create a configuration (Python dict or YAML) mapping each phase to allowed agents and optional `prompt_tags`.
   - Capture deliverable keywords per phase to support lightweight prompt heuristics (e.g., “architecture diagram” allowed in Design).

3. **Validation Service**
   - Implement `PhasePolicyService` (new module under `app/services/orchestrator/`) that exposes `evaluate(project_id, agent_type, instructions, *, override=False) -> PolicyDecision`.
   - Decision payload should include `status`, `reason_code`, `allowed_agents`, and suggested remediation text.
   - Heuristic strategy:
     - Look up phase via `ProjectManager.get_current_phase`.
     - If agent not in allowed list → deny.
     - Otherwise examine prompt for matching deliverable keywords; if none found return `needs_clarification` so UI can ask user to refine.

4. **Service Integration**
   - Inject `PhasePolicyService` into `OrchestratorCore` and `AgentCoordinator`.
   - Enforce policy in:
     - `AgentCoordinator.assign_agent_to_task`.
     - REST endpoint `/projects/{project_id}/tasks`.
     - WebSocket handler (chat/start_project).
   - Allow bypass only when trusted callers set an explicit `override` flag (e.g., recovery workflows).

5. **User Feedback**
   - Standardize denial response shape (`error`, `strategy`, `allowed_agents`, `current_phase`).
   - Emit WebSocket notifications when requests are blocked so the UI can surface guidance immediately.
   - Log policy denials with structured context for observability.

6. **Testing**
   - Unit tests for `PhasePolicyService` covering allow/deny/clarification scenarios and override handling.
   - Integration tests for REST/WebSocket endpoints ensuring policy checks engage before queuing tasks.
   - Regression check ensuring orchestrated workflow-generated tasks still pass automatically.

7. **Documentation & Follow-Up**
   - Update developer docs (architecture, onboarding) with the new policy flow.
   - Add changelog entry summarizing capability and configuration touchpoints.
   - Record potential enhancements (advanced NLP, UI pre-filtering) in backlog notes.

## Deliverables

- `PhasePolicyService` module + configuration.
- Updated orchestrator task pathways with policy enforcement.
- Automated tests validating behaviour.
- Documentation updates (CHANGELOG, architecture notes) and operational guidance.
