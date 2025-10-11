# Comprehensive Architectural Review & Refactoring Plan

**Document Version:** 2.0  
**Author:** Winston, Architect

## Introduction

This document provides a comprehensive architectural review of the frontend application, focusing on the Human-in-the-Loop (HITL) system and other custom-built components. It identifies architectural weaknesses and presents a detailed, multi-part refactoring plan with actionable TODO lists suitable for a junior developer.

---

## Part 1: HITL System Re-architecture

### 1.1. Initial Problem Analysis

- **Non-functional Counter:** The logic to track agent actions was disconnected from the UI, rendering the counter-based HITL trigger non-operational.
- **Weak Enforcement:** The system relied on "soft" enforcement via agent instructions rather than a programmatic "hard" gate.

### 1.2. Revised Architectural Vision

- **Backend Session Governor:** The backend will be the single source of truth for HITL state, reliably tracking agent actions (LLM calls) and enforcing limits.
- **Frontend Client-Side Action:** The frontend will define a native **client-side action** using the `useCopilotKitAction` hook. The backend will invoke this action to render an interactive UI prompt when limits are reached.

### 1.3. Detailed HITL Implementation Plan

#### Phase 1: Backend - The Governor

**Objective:** Implement the core logic for tracking, limiting, and pausing the agent.

**Task 1.1: Establish Session State Management**

**Developer TODO:**
- [ ] In your main backend application file (e.g., `backend/app/main.py`), create a simple in-memory Python dictionary to act as a session store. The key will be a user/session ID.
  ```python
  # In-memory store for demonstration purposes
  SESSION_STORE = {}
  ```
- [ ] Define a function `get_session(session_id: str) -> dict` that retrieves a user's session state or creates a new one with default values if it doesn't exist.
  ```python
  def get_session(session_id: str) -> dict:
      if session_id not in SESSION_STORE:
          SESSION_STORE[session_id] = {
              "isHitlEnabled": True,
              "actionLimit": 10,
              "actionCounter": 0,
          }
      return SESSION_STORE[session_id]
  ```
- [ ] In your main API route that handles agent requests (e.g., `/api/copilotkit`), ensure you have a `session_id` for each user and use `get_session()` to manage their state for every request.

**Task 1.2: Intercept Agent Actions**

**Developer TODO:**
- [ ] Find the function or class in your backend that makes the actual call to the LLM (e.g., `openai.chat.completions.create`).
- [ ] This is the point where you will insert the governor logic. You might wrap this call in a new function, e.g., `guarded_llm_call()`.

**Task 1.3: Implement Governor Logic**

**Developer TODO:**
- [ ] Inside your new `guarded_llm_call()` function, before making the LLM call, implement the core governor logic.
  ```python
  def guarded_llm_call(session_id: str, *llm_args, **llm_kwargs):
      session = get_session(session_id)

      if session["isHitlEnabled"] and session["actionCounter"] >= session["actionLimit"]:
          # Limit reached: BLOCK the call and return a tool call instruction
          print("HITL limit reached. Requesting user intervention.")
          # This structure will be sent back to the frontend by the CopilotKit runtime
          return {
              "tool_calls": [{
                  "id": f"call_{uuid.uuid4()[:8]}",
                  "type": "function",
                  "function": {
                      "name": "reconfigureHITL",
                      "arguments": json.dumps({
                          "actionLimit": session["actionLimit"],
                          "isHitlEnabled": session["isHitlEnabled"],
                      })
                  }
              }]
          }
      else:
          # Limit not reached: increment counter and proceed
          if session["isHitlEnabled"]:
              session["actionCounter"] += 1
          # response = openai.chat.completions.create(*llm_args, **llm_kwargs)
          # return response
  ```

**Task 1.4: Handle Action Result**

**Developer TODO:**
- [ ] The result from the frontend action will come back to the backend as a `tool_return` message in the agent's message history.
- [ ] In your main agent loop, add logic to detect when a `reconfigureHITL` tool has been executed.
- [ ] When you receive the result, parse it and update the session.
  ```python
  # In your agent loop, after the frontend returns the tool result:
  tool_result = {"newLimit": 20, "newStatus": True} # Example result
  session = get_session(session_id)

  session["actionLimit"] = tool_result.get("newLimit", session["actionLimit"])
  session["isHitlEnabled"] = tool_result.get("newStatus", session["isHitlEnabled"])
  session["actionCounter"] = 0 # Reset the counter

  print(f"HITL reconfigured. New limit: {session['actionLimit']}. Resuming agent.")
  # Now, resume the agent's paused task.
  ```

#### Phase 2: Frontend - The Native Action

**Objective:** Implement the interactive HITL prompt using the `useCopilotKitAction` hook.

**Task 2.1: Define the `reconfigureHITL` Action**

**Developer TODO:**
- [ ] In `frontend/app/copilot-demo/page.tsx`, import `useCopilotKitAction` from `@copilotkit/react-core`.
- [ ] Define the action within the `CopilotDemoPage` component.
  ```jsx
  useCopilotKitAction({
    name: "reconfigureHITL",
    description: "Renders a prompt to reconfigure HITL settings when the action limit is reached.",
    parameters: [
      { name: "actionLimit", type: "number" },
      { name: "isHitlEnabled", type: "boolean" },
    ],
    handler: async ({ actionLimit, isHitlEnabled }) => {
      // The handler will use render and getResponse from the hook
      // to manage the interactive UI. This part is conceptual;
      // you will need to adapt it to the exact hook implementation.
      console.log("Backend requested HITL reconfiguration.");
      // This is where you would render the component and wait for a response.
    },
  });
  ```

**Task 2.2: Create `HITLReconfigurePrompt.tsx` Component**

**Developer TODO:**
- [ ] Create a new file: `frontend/components/hitl/HITLReconfigurePrompt.tsx`.
- [ ] This component will receive `onContinue` and `onStop` as props.
- [ ] Use local state to manage the form inputs.
  ```jsx
  // HITLReconfigurePrompt.tsx
  import { useState } from 'react';
  import { Input } from '@/components/ui/input';
  import { Button } from '@/components/ui/button';
  import { Switch } from '@/components/ui/switch';

  export const HITLReconfigurePrompt = ({ initialLimit, initialStatus, onContinue, onStop }) => {
    const [limit, setLimit] = useState(initialLimit);
    const [isEnabled, setIsEnabled] = useState(initialStatus);

    const handleContinue = () => {
      onContinue({ newLimit: limit, newStatus: isEnabled });
    };

    return (
      <div className="p-4 border rounded-lg bg-muted/50 my-4">
        <p className="font-semibold">Agent Action Limit Reached</p>
        <div className="flex items-center gap-4 mt-2">
          <div>
            <label>Set Counter:</label>
            <Input type="number" value={limit} onChange={(e) => setLimit(parseInt(e.target.value, 10))} />
          </div>
          <div>
            <label>Toggle HITL:</label>
            <Switch checked={isEnabled} onCheckedChange={setIsEnabled} />
          </div>
          <Button onClick={handleContinue}>Continue</Button>
          <Button onClick={onStop} variant="destructive">Stop</Button>
        </div>
      </div>
    );
  };
  ```

**Task 2.3: Deprecate Old Frontend Logic**

**Developer TODO:**
- [ ] Delete the custom markdown tag renderer for `<hitl-reconfigure-prompt>` if you created one.
- [ ] Delete the `handleMessageSend` function from `copilot-demo/page.tsx`.
- [ ] Remove the `currentCounter` state variable.

---

## Part 2: Broader Custom Component Analysis

### 2.1. Component: `AgentProgressCard`

- **Recommendation:** Replace with the native `CopilotKit/AgentState` component.
- **Developer TODO:**
  - [ ] In `copilot-demo/page.tsx`, find where `<AgentProgressCard />` is used.
  - [ ] Comment out or delete the component and its import statement.
  - [ ] Import `AgentState` from the appropriate CopilotKit package (e.g., `@copilotkit/react-ui`).
  - [ ] Add `<AgentState />` to the page. You may need to wrap it in a CopilotKit provider if it's not already.

### 2.2. Component: `HITLAlertsBar`

- **Recommendation:** Replace with a standard Toast system from `shadcn/ui`.
- **Developer TODO:**
  - [ ] Follow the `shadcn/ui` documentation to add the `<Toaster />` component to your root layout file (e.g., `frontend/app/layout.tsx`).
  - [ ] In `copilot-demo/page.tsx`, import `useToast` from `@/components/ui/use-toast`.
  - [ ] Initialize the hook: `const { toast } = useToast()`.
  - [ ] Find all places where `setSystemAlerts` is called and replace them with a `toast()` call.
    ```jsx
    // Before
    setSystemAlerts(prev => [...prev, { id: '...', message: 'HITL approval required' }]);

    // After
    toast({ title: "HITL Alert", description: "Approval required for agent." });
    ```
  - [ ] Delete the `HITLAlertsBar` component and all related state (`systemAlerts`, `expandedAlerts`).

### 2.3. State Management: `useHITLStore` (Zustand)

- **Recommendation:** Deprecate and remove this store.
- **Justification:** The state of pending interactive requests is managed natively by the `useCopilotKitAction` hook.
- **Developer TODO:**
  - [ ] Search the entire codebase for usages of `useHITLStore`.
  - [ ] For each usage, confirm that the state it manages is now handled by the `useCopilotKitAction` flow.
  - [ ] Once all usages are removed, delete the store definition file (e.g., `frontend/lib/stores/hitl-store.ts`).

---

## Part 3: Final Conclusion

By following these detailed steps, the application will be refactored to use a more robust, maintainable, and framework-native architecture. This will reduce complexity, improve reliability, and make future development easier.
