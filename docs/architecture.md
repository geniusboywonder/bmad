### **BotArmy Software Specification (Updated)**

This document outlines the technical specifications for the BotArmy Proof-of-Concept (POC), based on the architectural decisions and design principles discussed. The design adheres to the SOLID principles to ensure the system is maintainable, scalable, and extensible.

***

### **1. Overall System Architecture**

The system follows a modern microservice-oriented architecture consisting of a Python-based backend and a React-based frontend.

* **Frontend (React/Next.js)**: A single-page application (SPA) responsible for the user interface, real-time chat, and displaying workflow status. It consumes data from the backend via a WebSocket and REST APIs.
* **Backend (FastAPI)**: The core of the system. It hosts the Orchestrator, manages the agent workflows, and handles all data persistence and communication.
* **Task Queue (Celery)**: An asynchronous task management system to handle the execution of long-running agent tasks, ensuring the main application remains responsive.
* **Datastore (PostgreSQL)**: A relational database for persistent storage of core application data, including the Context Store and user-related information.
* **Caching (Redis)**: An in-memory key-value store used for caching and as the message broker for the task queue.
* **Real-time Communication (WebSocket)**: A dedicated service for live status updates and real-time event streaming between the backend and the frontend.

### **2. Adherence to SOLID Principles**

The design is intentionally crafted to follow the SOLID principles:

* **Single Responsibility Principle (SRP)**: Each class has a single, well-defined responsibility. The Orchestrator manages the workflow, the `HitlRequest` model handles its own state, and individual agents execute their specific tasks.
* **Open/Closed Principle (OCP)**: The system will be extensible without modification. We will use an agent framework like AutoGen, which supports a plugin architecture. New agents or tools can be added without altering the core Orchestrator code. The addition of the `amended` status is a key example of extending functionality without modifying existing core logic.
* **Liskov Substitution Principle (LSP)**: All agents will adhere to a common `Agent` interface, ensuring they can be used interchangeably by the Orchestrator. This allows for seamless substitution of one agent type for another, as long as they adhere to the contract.
* **Interface Segregation Principle (ISP)**: We will create small, client-specific interfaces. For example, a `TaskDelegator` interface for the Orchestrator and a `ContextReader` interface for agents that only need to read from the memory store. This prevents clients from depending on methods they don't use.
* **Dependency Inversion Principle (DIP)**: High-level modules (like the Orchestrator) will not depend on low-level modules (specific agents). Both will depend on abstractions (interfaces). Dependencies will be injected, allowing us to easily swap out implementations.

***

### **3. Data Models (Pydantic)**

We will use Pydantic models for type safety and validation across the FastAPI backend.

* `Task`: Represents a single unit of work for an agent. Contains `task_id`, `agent_type`, `status`, `context_ids`, and `instructions`.
* `AgentStatus`: Tracks the real-time status of each agent. Contains `agent_type`, `status` (e.g., `idle`, `working`, `waiting_for_hitl`), and `current_task_id`.
* `ContextArtifact`: Represents a piece of information stored in the persistent memory. Contains `context_id`, `source_agent`, `artifact_type`, and `content`. This is the core of our "Context Store Pattern".
* `HitlRequest`: A model for Human-in-the-Loop requests. Contains `request_id`, `task_id`, `question`, `options`, `status` (`pending`, `approved`, `rejected`, **`amended`**), and a history log to track changes.
* `HandoffSchema`: A generic JSON schema for structured handoffs between agents. This ensures consistency and is a key part of the Orchestrator's workflow.

***

### **4. API and Communication Specifications**

* **REST API (FastAPI)**: A set of endpoints for core functionalities.
  * `POST /api/project`: Initiates a new project.
  * `GET /api/project/{project_id}/status`: Retrieves the current project status.
  * `POST /api/hitl/{request_id}/respond`: The endpoint for the user to submit a response to a HITL request. This endpoint will accept `approve`, `reject`, or `amend` actions.

* **WebSocket Service (FastAPI)**: A single WebSocket endpoint at `/ws` that provides real-time updates.
  * **Agent Status**: Streams updates when an agent's status changes.
  * **Workflow Events**: Sends events like "Plan Approved," "Artifact Created," or "Task Started."
  * **HITL Requests**: Notifies the frontend when a HITL request is created or its status changes to `amended`.

***

### **5. Implementation Plan**

1. **Phase 1: Foundation (Backend)**
    * Set up a FastAPI project with a PostgreSQL database and Redis.
    * Implement the Pydantic data models, including the new `amended` status for `HitlRequest`.
    * Build the core WebSocket service for real-time communication.
    * Create a simple task queue with Celery and Redis.
2. **Phase 2: Core Logic (Backend)**
    * Integrate and configure the **AutoGen** framework.
    * Implement the Orchestrator service, adhering to the specified workflow and SOLID principles.
    * Develop the individual agent classes (Analyst, Architect, etc.) as AutoGen agents.
    * Implement the Context Store Pattern with a service layer that manages data access, abstracting the database details from the agents.
3. **Phase 3: Frontend Integration (React)**
    * Set up a Next.js project with Zustand for state management and Tailwind CSS for styling.
    * Build a WebSocket client to connect to the backend and handle real-time events.
    * Develop the main chat interface and UI components for displaying agent status and the workflow.
    * Create the HITL interface component that renders based on incoming WebSocket events and posts responses back to the REST API, now with explicit support for an `amend` action.
4. **Phase 4: Refinement & Testing**
    * Implement JSONL logging and ensure a full audit trail, including tracking `amended` requests.
    * Conduct end-to-end testing to ensure the entire workflow, including the new HITL amendment process, functions as designed.
    * Perform performance and security testing.

***

### **6. System Health Checks (First Pass)**

For the initial pass, we will implement a dedicated health endpoint to confirm that the key system components are online and communicating correctly. This will provide a clear, machine-readable status of the system's health.

* **Endpoint**: A simple `GET` endpoint at `/healthz` will return a JSON response with a status for each core component.

* **Health Checks**: The endpoint will perform the following checks:
  * **Backend Status**: A simple check to ensure the FastAPI service is running.
  * **LLM Connection Status**: A check to ensure the LLM provider's API is reachable and authorized.
  * **Task Queue Status**: A check to ensure the Redis broker and at least one Celery worker are online and available.
  * **Database Status**: A check to confirm connectivity to the PostgreSQL database.

* **Response**: The endpoint will return a 200 OK status code if all components are healthy, and a 503 Service Unavailable status code if any component is down. The JSON body will provide details on which components are healthy or unhealthy.

This simple API endpoint serves as both a human-readable status page and a robust health check for automated monitoring systems. We can expand upon it with more detailed metrics and alerting in future development phases.
