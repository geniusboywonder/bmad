# HITL Messaging Protocol Fix

## 1. Problem Summary

When an agent requires human approval (HITL), it triggers errors on the frontend (`Event from an unknown agent: system` and `Force-closing unterminated streaming message`).

The root cause is a protocol mismatch between the backend and the frontend for handling HITL requests.

-   **Backend Behavior**: The backend programmatically creates a HITL request in the database and broadcasts a custom `HITL_REQUEST_CREATED` WebSocket event.
-   **Frontend Expectation**: The frontend's CopilotKit runtime is designed to receive a simple text stream from the agent. It expects to find a special markdown tag (`<hitl-approval>`) within that text to trigger the HITL UI components.

The custom WebSocket event from the backend is not recognized by the CopilotKit runtime, causing it to fail.

## 2. Workflow Correction

### Incorrect Workflow (Before Fix)

1.  **Backend**: Agent task starts.
2.  **Backend**: A `HitlAgentApprovalDB` record is created in the database.
3.  **Backend**: A custom `HITL_REQUEST_CREATED` event is broadcast over WebSocket.
4.  **Frontend**: CopilotKit runtime receives this unknown event and crashes.
5.  **UI**: No HITL alert or inline approval component is displayed.

### Correct Workflow (After Fix)

1.  **Backend**: The agent task determines a HITL approval is needed.
2.  **Backend**: A `HitlAgentApprovalDB` record is created to track the request.
3.  **Backend**: The agent's text response is formatted to include the required markdown tag: `<hitl-approval requestId="...">Description of task...</hitl-approval>`.
4.  **Backend**: This formatted text is sent to the frontend as a standard agent chat message.
5.  **Frontend**: The `CopilotSidebar`'s `markdownTagRenderers` detects the tag.
6.  **Frontend**: The renderer function:
    a.  Renders the `InlineHITLApproval` component in the chat window.
    b.  Calls `addRequest` on the `useHITLStore`, which in turn makes the `HITLAlertsBar` display the new pending request.
7.  **UI**: The user sees both the inline approval buttons and the alert in the top bar, and the system functions as designed.

## 3. Implementation Details

The fix will be implemented in `/Users/neill/Documents/AI Code/Projects/bmad/backend/app/tasks/agent_tasks.py`.

1.  **Remove Custom Event**: The code that broadcasts the `HITL_REQUEST_CREATED` WebSocket event will be removed. This is the direct source of the frontend error.
2.  **Remove Polling**: The database polling logic, where the Celery task waits for approval, will be removed. The agent's responsibility ends after requesting approval.
3.  **Format Agent Output**: The agent's final output will be intercepted. A unique `requestId` will be used (matching the one stored in the database) and the output text will be wrapped in the `<hitl-approval requestId="...">...</hitl-approval>` tag before being sent to the frontend.

This change aligns the backend's behavior with the frontend's architecture, ensuring the HITL feature works as intended without requiring any frontend modifications.
