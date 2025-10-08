# Refactoring Opportunities for CopilotKit Integration

This document outlines opportunities to refactor the existing chat components to better leverage the native features of CopilotKit. The goal of this refactoring is to simplify the codebase, reduce maintenance overhead, and improve the overall developer experience.

## 1. Unified Backend Endpoint

### Current Implementation

The backend currently creates a separate API endpoint for each agent (e.g., `/api/copilotkit/analyst`, `/api/copilotkit/coder`). This is done in `backend/app/copilot/adk_runtime.py` using the `add_adk_fastapi_endpoint` function from the `ag_ui_adk` library.

```python
# backend/app/copilot/adk_runtime.py

# ...
add_adk_fastapi_endpoint(app, analyst_adk, path="/api/copilotkit/analyst")
add_adk_fastapi_endpoint(app, architect_adk, path="/api/copilotkit/architect")
add_adk_fastapi_endpoint(app, coder_adk, path="/api/copilotkit/coder")
# ...
```

While this approach works, it has a few drawbacks:

*   **Scalability**: Adding a new agent requires modifying the backend code to create a new endpoint.
*   **Complexity**: It increases the number of API endpoints, which can make the backend more difficult to manage.
*   **Redundancy**: Each endpoint likely performs a similar function, leading to code duplication.

### Proposed Refactoring

The backend could be refactored to use a single, dynamic endpoint that can handle requests for all agents. This could be achieved by creating a new endpoint that accepts the agent name as a parameter (e.g., `/api/copilotkit/{agent_name}`). This endpoint would then be responsible for looking up the appropriate agent and forwarding the request.

This approach would have several benefits:

*   **Scalability**: Adding a new agent would not require any changes to the backend API.
*   **Simplicity**: It would reduce the number of API endpoints, making the backend easier to manage.
*   **Flexibility**: It would allow for more dynamic agent management.

### Code to Change

*   **`backend/app/copilot/adk_runtime.py`**: Instead of creating a separate endpoint for each agent, create a single, dynamic endpoint.
*   **`frontend/app/copilot-demo/page.tsx`**: Update the frontend to use the new, dynamic endpoint.

## 2. Native Frontend Actions

### Current Implementation

The frontend currently uses a mix of custom code and `useCopilotAction` to handle user interactions. For example, the `reconfigureHITL` action is implemented using `useCopilotAction`, but the handling of the response is done in a custom `useEffect` hook.

```typescript
// frontend/app/copilot-demo/page.tsx

const reconfigureHITL = useCopilotAction({
  // ...
});

useEffect(() => {
  // ...
  const handlePolicyViolation = (event: PolicyViolationEvent) => {
    // ...
  };
  // ...
}, [isClient]);
```

This approach can lead to a separation of concerns that makes the code harder to follow and maintain.

### Proposed Refactoring

The frontend could be refactored to use `useCopilotAction` for all frontend actions. This would involve moving the logic from the `useEffect` hook into a new `useCopilotAction` hook. This would make the code more self-contained and easier to understand.

This approach would have several benefits:

*   **Simplicity**: It would consolidate the logic for handling frontend actions in one place.
*   **Readability**: It would make the code easier to read and understand.
*   **Maintainability**: It would make the code easier to maintain and debug.

### Code to Change

*   **`frontend/app/copilot-demo/page.tsx`**: Move the logic from the `useEffect` hook into a new `useCopilotAction` hook.

## 3. Generative UI

### Current Implementation

The frontend currently uses a custom component (`HITLReconfigurePrompt`) to get user input for reconfiguring the HITL settings. This component is rendered by the `reconfigureHITL` action.

```typescript
// frontend/app/copilot-demo/page.tsx

const reconfigureHITL = useCopilotAction({
  // ...
  render: (props) => {
    // ...
    return (
      <HITLReconfigurePrompt
        // ...
      />
    );
  },
});
```

While this approach works, it requires creating and maintaining a custom React component for each user interaction.

### Proposed Refactoring

The frontend could be refactored to use CopilotKit's native Generative UI features. This would involve replacing the custom `HITLReconfigurePrompt` component with a combination of `useCopilotAction` and CopilotKit's built-in UI components.

This approach would have several benefits:

*   **Simplicity**: It would eliminate the need to create and maintain custom React components for user interactions.
*   **Consistency**: It would ensure a consistent look and feel for all user interactions.
*   **Flexibility**: It would allow for more dynamic and complex user interactions.

### Code to Change

*   **`frontend/app/copilot-demo/page.tsx`**: Replace the custom `HITLReconfigurePrompt` component with CopilotKit's native Generative UI features.
*   **`frontend/components/hitl/HITLReconfigurePrompt.tsx`**: This component could be deprecated or removed.

## 4. Shared State

### Current Implementation

The frontend currently uses a custom Zustand store (`useAppStore`) to manage application state. This store is used to share state between different components, such as the selected agent and the policy guidance.

```typescript
// frontend/app/copilot-demo/page.tsx

const { selectedAgent, setSelectedAgent } = useAgent();
const policyGuidance = useAppStore((state) => state.policyGuidance);
```

While this approach works, it requires setting up and maintaining a custom state management solution.

### Proposed Refactoring

The frontend could be refactored to use CopilotKit's shared state features. This would involve replacing the custom Zustand store with CopilotKit's `useCopilotState` hook.

This approach would have several benefits:

*   **Simplicity**: It would eliminate the need to set up and maintain a custom state management solution.
*   **Integration**: It would provide seamless integration with other CopilotKit features.
*   **Scalability**: It would provide a scalable solution for managing application state.

### Code to Change

*   **`frontend/app/copilot-demo/page.tsx`**: Replace the custom Zustand store with CopilotKit's `useCopilotState` hook.
*   **`frontend/lib/stores/app-store.ts`**: This file could be deprecated or removed.
*   **`frontend/lib/context/agent-context.tsx`**: This file could be deprecated or removed.