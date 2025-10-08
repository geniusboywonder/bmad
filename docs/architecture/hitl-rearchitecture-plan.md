# Backend-Driven HITL Re-architecture Plan

**Document Version:** 1.0
**Author:** Winston, Architect

## 1. Introduction

This document outlines the architectural and implementation plan for refactoring the Human-in-the-Loop (HITL) system. The current frontend-based implementation is not correctly tracking agent actions and cannot enforce limits effectively.

The new architecture will implement a **backend-driven session governor** to reliably track agent actions (i.e., token-consuming LLM calls). When a pre-configured action limit is reached, the backend will command the frontend to render an interactive HITL control panel directly in the chat stream, adhering to the specified user workflow.

### Target Workflow

1.  **HITL OFF:** Agent operates with no limits; all actions are implicitly approved.
2.  **HITL ON:** The agent is given a budget of actions (the "Counter Limit"). Actions are auto-approved until this budget is depleted.
3.  **Counter Zero:** When the budget reaches zero, the agent is paused, and an interactive prompt is displayed in the chat, allowing the user to reconfigure and continue.
4.  **Reconfiguration:** The user can adjust the action budget and resume agent activity directly from this prompt.

## 2. Core Architectural Changes (Revised)

This revised plan leverages native CopilotKit features for a more elegant and robust implementation.

1.  **Backend Session Governor:** The backend remains the source of truth for HITL state and still intercepts agent actions to enforce limits.
2.  **Frontend Client-Side Action:** We will define a **client-side action** using the `useCopilotKitAction` hook. This action will be responsible for rendering the interactive HITL prompt.
3.  **Agent-Invoked UI:** Instead of sending a custom markdown tag, the backend will instruct the agent to invoke the frontend action. The entire interactive session will be managed by the CopilotKit runtime, eliminating the need for custom APIs for this interaction.

---

## 3. Implementation Phases (Revised)

### Phase 1: Backend - The Governor

**Objective:** Modify the governor to invoke a frontend action when the HITL limit is reached.

**Task 1.1: Establish Session State Management**
- (No change) Manage `isHitlEnabled`, `actionLimit`, and `actionCounter` in the user's session.

**Task 1.2: Intercept Agent Actions**
- (No change) Intercept all LLM calls to track agent "actions".

**Task 1.3: Implement Governor Logic (REVISED)**
- Before every LLM call, execute this logic:
  1.  If `isHitlEnabled` is `true` and `actionCounter >= actionLimit`:
     a. **BLOCK** the outbound LLM call.
     b. **PAUSE** the agent's current task (see Phase 3).
     c. **INSTRUCT AGENT TO INVOKE ACTION:** Formulate a standard "tool call" response that instructs the CopilotKit runtime to execute a client-side action named `reconfigureHITL`.

     **Example Backend Response (instructing frontend to run the action):**
     ```json
     {
       "tool_calls": [{
         "id": "call_abc123",
         "type": "function",
         "function": {
           "name": "reconfigureHITL",
           "arguments": "{\"actionLimit\": 10, \"isHitlEnabled\": true}"
         }
       }]
     }
     ```

**Task 1.4: Handle Action Result (REVISED)**
- The result from the frontend action (e.g., `{ newLimit: 20, newStatus: true }`) will be automatically sent back to the backend by the CopilotKit runtime.
- Your backend agent loop should be prepared to receive this tool result.
- When the result is received:
  1.  Update the `actionLimit` and `isHitlEnabled` values in the session state.
  2.  Reset the `actionCounter` to `0`.
  3.  Signal the paused agent task to resume (see Phase 3).
- The separate `POST /api/hitl/reconfigure` endpoint is **no longer needed**.

### Phase 2: Frontend - The Native Action

**Objective:** Implement the interactive HITL prompt using the `useCopilotKitAction` hook.

**Task 2.1: Define the `reconfigureHITL` Action**
- In your main frontend component (`copilot-demo/page.tsx`), define the action:
  ```javascript
  useCopilotAction({
    name: "reconfigureHITL",
    description: "Renders a prompt to reconfigure HITL settings when the action limit is reached.",
    parameters: [
      { name: "actionLimit", type: "number" },
      { name: "isHitlEnabled", type: "boolean" },
    ],
    handler: async (props) => {
      // This handler will use render and getResponse from the hook
      // to manage the interactive UI.
    },
  });
  ```
- The `handler` function will receive `render` and `getResponse` from the hook.
- Call `render(<HITLReconfigurePrompt {...props} />)` to display the UI in the chat.
- The `HITLReconfigurePrompt` component will receive `onContinue` and `onStop` callbacks from the handler.
- When the user clicks "Continue" in the UI, the `onContinue` callback will invoke `getResponse({ newLimit: 20, newStatus: true })`, which resolves the action and sends the data back to the backend agent.

**Task 2.2: Create `HITLReconfigurePrompt.tsx` Component (Revised)**
- The component no longer makes any API calls.
- It will receive `onContinue` and `onStop` as props and will invoke them to return control to the `useCopilotKitAction` handler.

**Task 2.3: Deprecate Old Frontend Logic (REVISED)**
- Remove the custom markdown tag renderer for `<hitl-reconfigure-prompt>`.
- All other deprecations from the previous plan remain (remove `handleMessageSend`, etc.).

### Phase 3: Backend - Agent State & Resumption

**Objective:** Ensure the agent can be gracefully paused and resumed.

**Task 3.1: Implement Agent Pausing**
- When the Session Governor blocks an action, the agent's state must be saved. This includes the conversation history and the task it was about to perform.
- Associate this saved state with a unique ID (which could be returned in the `<hitl-reconfigure-prompt>` tag if needed, though a session-based approach is simpler).

**Task 3.2: Implement Agent Resumption**
- When the `/api/hitl/reconfigure` endpoint is successfully called (i.e., the user clicks "Continue"), retrieve the saved agent state.
- Re-hydrate the agent and instruct it to retry the action that was originally blocked.

---
This plan provides a complete roadmap for building a robust and user-friendly HITL system that meets the specified requirements.
