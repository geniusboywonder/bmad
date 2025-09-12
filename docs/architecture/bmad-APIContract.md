### **Backend: Deep Dive & API Contract**

This document provides a detailed technical specification for the backend components, including the database schema, API contract, and the communication protocol between agents. This level of detail is crucial for development, ensuring all engineers are working from a single, consistent source of truth.

---

### **1. Database Schema (PostgreSQL ERD)**

Our data model is designed to be relational, highly normalized, and fully compliant with the "Context Store Pattern" to ensure data integrity and traceability. The primary key for all tables will be a UUID to prevent collisions and simplify distribution.

| Table Name | Purpose | Columns | Relationships |
| :--- | :--- | :--- | :--- |
| **`projects`** | Stores high-level project information. | `id` (UUID, PK)<br>`name` (TEXT)<br>`created_at` (TIMESTAMP)<br>`status` (ENUM: `active`, `completed`, `failed`) | One-to-many with `tasks`<br>One-to-many with `context_artifacts` |
| **`tasks`** | Represents a single unit of work for an agent. | `id` (UUID, PK)<br>`project_id` (UUID, FK)<br>`agent_type` (TEXT)<br>`instructions` (TEXT)<br>`status` (ENUM: `pending`, `working`, `waiting_for_hitl`, `completed`, `failed`)<br>`created_at` (TIMESTAMP)<br>`updated_at` (TIMESTAMP) | Many-to-one with `projects`<br>One-to-one with `hitl_requests` |
| **`context_artifacts`** | The core of the Context Store. Persists all outputs. | `id` (UUID, PK)<br>`project_id` (UUID, FK)<br>`source_agent` (TEXT)<br>`artifact_type` (TEXT: `spec`, `plan`, `code`, `log`)<br>`content` (JSONB) | Many-to-one with `projects`<br>One-to-one with `tasks` |
| **`hitl_requests`** | Manages human-in-the-loop requests. | `id` (UUID, PK)<br>`task_id` (UUID, FK)<br>`request_content` (TEXT)<br>`status` (ENUM: `pending`, `approved`, `rejected`, `amended`)<br>`response_content` (TEXT)<br>`created_at` (TIMESTAMP)<br>`updated_at` (TIMESTAMP) | One-to-one with `tasks` |
| **`event_log`** | An immutable audit trail of all major events. | `id` (UUID, PK)<br>`project_id` (UUID, FK)<br>`event_type` (TEXT: `task_start`, `task_complete`, `hitl_request`, `hitl_response`)<br>`timestamp` (TIMESTAMP)<br>`payload` (JSONB) | Many-to-one with `projects` |

---

### **2. API Contract**

The backend will expose a REST API for command-and-control functions and a WebSocket service for real-time event streaming.

#### **REST API Endpoints (`/api/v1`)**

| Method | Endpoint | Description | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/projects` | Creates a new project and initiates the first task. | `{ "product_idea": "string" }` | `{ "project_id": "uuid", "status": "string" }` |
| `GET` | `/projects/{project_id}` | Retrieves a project's full status and all artifacts. | None | `{ "project_id": "uuid", "status": "string", "tasks": [], "artifacts": [] }` |
| `POST` | `/hitl/{request_id}/respond` | Submits a user's response to a HITL request. | `{ "action": "string", "response_content": "string" }` | `{ "request_id": "uuid", "new_status": "string" }` |
| `GET` | `/healthz` | Health check endpoint for system monitoring. | None | `{ "api_status": "ok", "db_status": "ok", "celery_status": "ok", "llm_status": "ok" }` |

#### **WebSocket Service (`/ws`)**

The WebSocket connection will stream a JSON object for each event. The `event_type` field will be used by the frontend to determine how to handle the message.

| Event Type | Description | Sample Payload |
| :--- | :--- | :--- |
| `agent_status_update` | Notifies the frontend of an agent's status change. | `{ "agent_type": "analyst", "status": "working", "timestamp": "ISO 8601" }` |
| `new_message` | Streams a new message from an agent to the chat UI. | `{ "agent_type": "analyst", "message": "Analyzing requirements...", "timestamp": "ISO 8601" }` |
| `hitl_request` | Notifies the frontend that a HITL request requires user input. | `{ "request_id": "uuid", "task_id": "uuid", "question": "Please review the plan...", "timestamp": "ISO 8601" }` |
| `task_progress` | Provides a percentage or stage update for a long-running task. | `{ "task_id": "uuid", "progress": 50, "stage": "gathering_data" }` |

---

### **3. Agent Communication Protocol**

The agents will not communicate directly with each other. All handoffs will be orchestrated by the `Orchestrator` using a structured JSON schema. This adheres to the **Interface Segregation Principle** by ensuring each agent only receives the specific data it needs.

**`HandoffSchema`**
This is the base schema for all structured communication.

```json
{
  "project_id": "uuid",
  "source_agent": "string",
  "target_agent": "string",
  "handoff_type": "string",
  "content": "object"
}
```

Specific Handoff Schemas

`Analyst` to `Architect` Handover:

`handoff_type`: `"software_specification"`

content:

```json
{
  "requirements": ["list of strings"],
  "user_stories": ["list of strings"],
  "high_level_features": ["list of strings"],
  "core_idea": "string"
}
```

`Architect` to `Coder` Handover:
`handoff_type`: `"implementation_plan"`
content:

```json
{
  "architecture_diagram_url": "string",
  "database_schema": "string",
  "tech_stack": ["list of strings"],
  "task_breakdown": ["list of strings"]
}
```

This structured approach ensures that each agent can reliably parse and act upon the information it receives, minimizing integration errors and making the system more robust.
