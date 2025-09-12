### **Sprint 2: Backend Core Logic & Agent Integration**

**Goal:** Integrate the multi-agent framework, implement the core Orchestrator logic, and enable the agents to perform their first tasks based on the `SDLC_Process_Flow`.

---

#### **Epic: Project Lifecycle & Orchestration**

* **Story:** Sequential Task Handoff
  * **Goal:** The Orchestrator can successfully pass a task from one agent to the next in the correct sequence.
  * **Tasks:**
    * Implement the `Orchestrator` service as the central manager of the workflow.
    * Develop the logic for the Orchestrator to read from the `SDLC_Process_Flow` and determine the next agent and task.
    * Implement the structured `HandoffSchema` for communication between agents.
    * Integrate the `AutoGen` framework as the foundation for the agent classes.

#### **Epic: Data & State Management**

* **Story:** Context Persistence
  * **Goal:** Agents can read and write artifacts from the persistent Context Store.
  * **Tasks:**
    * Implement the `ContextStore` service, which handles all CRUD operations on the `context_artifacts` table.
    * Develop the agents' ability to save their outputs as new `ContextArtifacts`.
    * Develop the agents' ability to retrieve relevant `ContextArtifacts` when a new task is assigned.

#### **Epic: Human-in-the-Loop (HITL) Interface**

* **Story:** Response to a HITL Request
  * **Goal:** The backend can process user responses (approve, reject, amend) and resume the workflow.
  * **Tasks:**
    * Create the `POST /api/v1/hitl/{request_id}/respond` endpoint.
    * Implement the backend logic to handle the `approve`, `reject`, and `amend` actions.
    * Develop the Orchestrator's logic to check the `HitlRequest` status and either resume the agent, re-assign the task with amended content, or halt the project.
