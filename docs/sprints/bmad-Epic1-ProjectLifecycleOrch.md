### **Epic 1: Project Lifecycle & Orchestration**

**Goal:** This epic covers the core workflow of a project, from the initial user input to the final project completion. It ensures the Orchestrator can manage and track the entire sequential process across multiple agents.

#### **User Stories & Acceptance Criteria**

**Story 1: Project Initiation**

* **As a** user, I want to start a new project by providing a product idea so that the agents can begin their work.
* **Acceptance Criteria:**
  * **Given** a new user visits the application, **when** they enter a high-level product idea into the chat and submit it, **then** the system must create a new `Project` record in the database.
  * **When** the project is created, **then** the Orchestrator must immediately instantiate the first agent (`Analyst`) and pass the initial user input as a task.
  * **Then** the frontend must display a message confirming the project has started.

**Story 2: Sequential Task Handoff**

* **As an** Orchestrator, I need to manage the state of the project so that I can hand off tasks between agents in the correct order.
* **Acceptance Criteria:**
  * **Given** an agent completes a task, **when** it returns a success status to the Orchestrator, **then** the Orchestrator must update the task's status in the database.
  * **Then** the Orchestrator must check the `SDLC_Process_Flow` to identify the next agent in the sequence.
  * **When** the next agent is identified, **then** the Orchestrator must compose a new task using relevant context artifacts from the previous task's output.
  * **When** the new task is composed, **then** it must be submitted to the task queue for the next agent to pick up.

**Story 3: Real-time Status Updates**

* **As a** user, I want to see the real-time status of each agent so that I know what is happening with my project.
* **Acceptance Criteria:**
  * **Given** an agent begins a task, **when** it changes its status to `working`, **then** a real-time event must be sent via WebSocket to the frontend.
  * **Then** the frontend must update the status of that agent and the current task in the UI.
  * **Given** an agent encounters an error, **when** it reports the error to the Orchestrator, **then** a real-time event must be sent to the frontend with an `error` status and a message.
  * **When** an agent completes a task, **then** a final event must be sent, and the agent's status should return to `idle`.

**Story 4: Final Artifact Generation**

* **As a** user, I want the system to generate and provide the final project artifacts so that I can download and use them.
* **Acceptance Criteria:**
  * **Given** all agents have completed their tasks, **when** the final agent (`Deployer`) reports a successful run, **then** the Orchestrator must trigger the final document generation process.
  * **Then** the system must make the final code and a PDF version of the Software Specification available for download via the frontend.
  * **Then** the frontend UI must show a "Project Complete" status and provide clear download links.
