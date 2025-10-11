# Plan: Real-time Process Summary UI

This document outlines two potential strategies for connecting the "Process Summary" UI to the backend to enable real-time updates.

## Option 1: "CopilotKit Native" Approach

This approach fully utilizes CopilotKit's shared state management features.

*   **Backend:**
    1.  Integrate CopilotKit's state management features (e.g., `CopilotState`) into the Python backend.
    2.  Create a new tool for agents, such as `update_process_status`.
    3.  Modify the agent execution logic to call this new tool whenever a task status changes or an artifact is generated.

*   **Frontend:**
    1.  Use a simple CopilotKit hook like `useCopilotState('processStatus')` in the `project-process-summary.tsx` component.
    2.  The component would automatically re-render whenever the shared state object is updated by the backend agents.

*   **Pros:**
    *   Much cleaner and simpler frontend code.
    *   Aligns perfectly with CopilotKit's intended design patterns.

*   **Cons:**
    *   Requires more significant backend modification.
    *   Involves creating a new tool and changing the agent's core logic, replacing a system that already broadcasts this information.

## Option 2: "Pragmatic Integration" Approach

This approach leverages the application's existing custom WebSocket infrastructure.

*   **Backend:**
    *   No changes are needed initially. The `AgentStatusService` already broadcasts all necessary events (`AGENT_STATUS_CHANGE`, `TASK_COMPLETED`, etc.) over the existing WebSocket connection.

*   **Frontend:**
    1.  Manually implement WebSocket connection logic in the `project-process-summary.tsx` component.
    2.  Write an `onmessage` handler to parse the incoming events and update the component's local React state.

*   **Pros:**
    *   Minimal backend changes, making it a less intrusive and faster initial implementation.
    *   Leverages existing, working infrastructure.

*   **Cons:**
    *   Requires more boilerplate code on the frontend to manage the WebSocket connection and event handling compared to the simplicity of a single `useCopilotState` hook.

## Recommendation

The "CopilotKit Native" approach (Option 1) is architecturally cleaner and represents a better long-term pattern for full adoption of the CopilotKit ecosystem.

However, the **"Pragmatic Integration" approach (Option 2) is recommended for the initial implementation.** It will deliver the desired real-time functionality with the least amount of disruption and risk by building on the existing, proven WebSocket system.

A future refactor to the "CopilotKit Native" model can be planned after the initial implementation is complete.
