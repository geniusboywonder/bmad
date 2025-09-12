### **Sprint 3: Frontend & Real-Time Integration**

**Goal:** Connect the frontend to the backend's core services, build the user interface for real-time interaction, and implement the full HITL flow.

---

#### **Epic: Agent Chat Interface**

* **Story:** Real-time Status Updates
  * **Goal:** The frontend can display the real-time status of agents and project progress.
  * **Tasks:**
    * Implement the WebSocket client in the React frontend.
    * Connect the client to the backend's `/ws` endpoint.
    * Set up the Zustand `agentStore` to receive and manage real-time agent status updates.
    * Build the `AgentStatusGrid` component to visualize the status of each agent.

#### **Epic: Project Lifecycle & Orchestration**

* **Story:** Final Artifact Generation
  * **Goal:** The frontend can display the final project artifacts for download.
  * **Tasks:**
    * Implement the logic to listen for the "project completed" event.
    * Build the `ArtifactSummary` component to list the generated artifacts.
    * Develop the functionality to serve the downloadable files (e.g., code, PDF) from the backend.

#### **Epic: Human-in-the-Loop (HITL) Interface**

* **Story:** User Interface for HITL
  * **Goal:** A user can see and respond to a HITL request in the UI.
  * **Tasks:**
    * Implement the `HitlPrompt` component to display the request and its action buttons.
    * Develop the frontend logic to dispatch `POST` requests to the `respond` endpoint based on user input.
    * Implement the `chatStore` to correctly manage the display of HITL prompts and user responses in the chat history.
