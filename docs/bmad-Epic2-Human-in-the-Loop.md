### **Epic 2: Human-in-the-Loop (HITL) Interface**

**Goal:** This epic focuses on the critical interaction between the human user and the AI agents. It ensures the user has a clear and powerful way to provide feedback, approve progress, or amend agent outputs, guaranteeing the final product aligns with their vision.

#### **User Stories & Acceptance Criteria**

**Story 1: Approval Request**

* **As a** user, I want to be prompted for approval when an agent finishes a key planning task so that I can provide feedback before they proceed.
* **Acceptance Criteria:**
  * **Given** an agent completes a task that requires human review (e.g., the `Analyst` completing the `Software Specification`), **when** it submits its output to the Orchestrator, **then** the Orchestrator must generate a new `HitlRequest` record in the database with the status `pending`.
  * **When** the `HitlRequest` is created, **then** the Orchestrator must send a real-time event via WebSocket to the frontend, notifying the user that a decision is needed.
  * **Then** the agent's status should change to `waiting_for_hitl` and its process should pause.

**Story 2: Response to a HITL Request**

* **As a** user, I want to approve, reject, or amend an agent's response so that I can guide the workflow.
* **Acceptance Criteria:**
  * **Given** a `HitlRequest` is displayed on the frontend, **when** the user selects `approve`, **then** a `POST` request must be sent to the `/api/hitl/{request_id}/respond` endpoint with the action `approve`.
  * **When** the user selects `reject`, **then** a `POST` request must be sent to the `/api/hitl/{request_id}/respond` endpoint with the action `reject`.
  * **When** the user selects `amend`, **then** the system must provide an input field to collect the user's edits, and a `POST` request must be sent to the `/api/hitl/{request_id}/respond` endpoint with the action `amend` and the new content.
  * **When** the request is submitted, **then** the backend must update the `HitlRequest` record with the chosen action and the user's response.

**Story 3: HITL State Management**

* **As an** Orchestrator, I need to know the outcome of a HITL request so that I can resume or modify the agent's workflow accordingly.
* **Acceptance Criteria:**
  * **Given** the `HitlRequest` status changes to `approved`, **then** the Orchestrator must send a resume command to the agent, allowing it to proceed to the next step.
  * **Given** the `HitlRequest` status changes to `rejected`, **then** the Orchestrator must send a termination command to the agent and notify the user.
  * **Given** the `HitlRequest` status changes to `amended`, **then** the Orchestrator must take the new content from the `HitlRequest` record, update the relevant `ContextArtifact`, and re-assign the original task to the agent with the new information.
  * **Then** the Orchestrator must update the agent's status from `waiting_for_hitl` to `working`.

**Story 4: Request History**

* **As a** user, I want to see a history of all HITL requests and my responses so that I can review past decisions.
* **Acceptance Criteria:**
  * **Given** a project has multiple HITL requests, **when** the user scrolls up in the chat, **then** the frontend must display all past requests and the user's corresponding responses.
  * **Then** the user's response should be clearly labeled as `approved`, `rejected`, or `amended`, along with a timestamp.
  * **Given** a request was amended, **then** the history must show both the original agent output and the final user-amended content.
