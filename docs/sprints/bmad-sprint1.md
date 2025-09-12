### **Sprint 1: The Foundation**

**Goal:** Lay the essential groundwork by establishing the core backend services, data models, and communication channels. This sprint focuses on the foundational components that the rest of the system will be built upon.

---

#### **Epic: Project Lifecycle & Orchestration**

* **Story:** Project Initiation
  * **Goal:** A user can successfully start a new project from the frontend.
  * **Tasks:**
    * Create the FastAPI endpoint for `/api/v1/projects`.
    * Implement the Pydantic data model for the `Project` and `Task`.
    * Create the initial database migrations for the `projects` and `tasks` tables.
    * Implement the logic in the Orchestrator to create a new project record and enqueue the first task (`Task 0.1: Project Planning`).

#### **Epic: Data & State Management**

* **Story:** Context & Task State Persistence
  * **Goal:** The system can reliably store project data and task status.
  * **Tasks:**
    * Implement the database models for `context_artifacts` and `event_log`.
    * Develop a service layer for all database interactions to abstract the data access logic from the Orchestrator, which adheres to the **Dependency Inversion Principle (DIP)**.

#### **Epic: Human-in-the-Loop (HITL) Interface**

* **Story:** Approval Request
  * **Goal:** The system can pause the workflow and generate a HITL request.
  * **Tasks:**
    * Implement the `hitl_requests` database model.
    * Develop the Orchestrator logic to create a new `HitlRequest` and change the agent's status to `waiting_for_hitl`.
    * Configure the WebSocket service to send a `hitl_request` event to the frontend.
