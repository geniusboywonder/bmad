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

**Project Management:**

| Method | Endpoint | Description | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/projects` | Creates a new project and initiates the first task. | `{ "product_idea": "string" }` | `{ "project_id": "uuid", "status": "string" }` |
| `GET` | `/projects/{project_id}` | Retrieves a project's full status and all artifacts. | None | `{ "project_id": "uuid", "status": "string", "tasks": [], "artifacts": [] }` |
| `GET` | `/projects/{project_id}/completion` | Get detailed project completion status and metrics. | None | `{ "project_id": "uuid", "completion_percentage": 85.5, "total_tasks": 12, "completed_tasks": 10, "artifacts_available": true }` |
| `POST` | `/projects/{project_id}/check-completion` | Trigger manual project completion check. | None | `{ "is_complete": false, "completion_indicators": [] }` |
| `POST` | `/projects/{project_id}/force-complete` | Force project completion (admin function). | None | `{ "status": "completed", "artifacts_generated": true }` |

**Agent Status Management (Sprint 3):**

| Method | Endpoint | Description | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/agents/status` | Get real-time status of all agents. | None | `{ "agents": [{ "agent_type": "analyst", "status": "working", "last_activity": "datetime" }] }` |
| `GET` | `/agents/status/{agent_type}` | Get specific agent status. | None | `{ "agent_type": "analyst", "status": "idle", "current_task_id": "uuid", "last_activity": "datetime" }` |
| `GET` | `/agents/status-history/{agent_type}` | Get agent status history from database. | None | `{ "history": [{ "status": "working", "timestamp": "datetime" }] }` |
| `POST` | `/agents/status/{agent_type}/reset` | Reset agent status to idle (admin function). | None | `{ "message": "Agent analyst status reset to idle", "status": "idle" }` |

**Artifact Management (Sprint 3):**

| Method | Endpoint | Description | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/artifacts/{project_id}/generate` | Generate downloadable project artifacts. | None | `{ "artifacts_generated": 5, "zip_created": true, "download_available": true }` |
| `GET` | `/artifacts/{project_id}/summary` | Get summary of generated artifacts. | None | `{ "artifacts": [{ "name": "README.md", "type": "documentation", "size": 1024 }] }` |
| `GET` | `/artifacts/{project_id}/download` | Download project artifacts as ZIP file. | None | `Binary ZIP file download` |
| `DELETE` | `/artifacts/{project_id}/artifacts` | Clean up project artifacts. | None | `{ "cleaned_files": 3, "status": "success" }` |
| `DELETE` | `/artifacts/cleanup-old` | Admin endpoint to cleanup old artifacts. | `{ "max_age_hours": 24 }` | `{ "cleaned_files": 15, "freed_space_mb": 128 }` |

**BMAD Core Template System (Task 3):**

| Method | Endpoint | Description | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/workflows/templates` | List all available templates from `.bmad-core/templates/`. | None | `{ "templates": [{ "id": "string", "name": "string", "description": "string", "version": "string" }] }` |
| `GET` | `/workflows/templates/{template_id}` | Get specific template details. | None | `{ "id": "string", "name": "string", "content": {}, "variables": [], "sections": [] }` |
| `POST` | `/workflows/templates/{template_id}/render` | Render template with variable substitution. | `{ "variables": { "key": "value" }, "output_format": "markdown" }` | `{ "rendered_content": "string", "format": "markdown", "variables_used": [] }` |
| `GET` | `/workflows/workflows` | List all available workflows from `.bmad-core/workflows/`. | None | `{ "workflows": [{ "id": "string", "name": "string", "description": "string", "phases": [] }] }` |
| `GET` | `/workflows/workflows/{workflow_id}` | Get specific workflow definition. | None | `{ "id": "string", "name": "string", "steps": [], "handoffs": [], "validation_rules": [] }` |
| `POST` | `/workflows/workflows/{workflow_id}/execute` | Execute workflow with orchestration. | `{ "project_id": "uuid", "context": {}, "parameters": {} }` | `{ "execution_id": "uuid", "status": "started", "estimated_duration": 300 }` |
| `GET` | `/workflows/workflows/{workflow_id}/status/{execution_id}` | Get workflow execution status. | None | `{ "execution_id": "uuid", "status": "running", "current_step": "string", "progress": 75, "results": {} }` |
| `GET` | `/workflows/teams` | List all available agent teams from `.bmad-core/agent-teams/`. | None | `{ "teams": [{ "id": "string", "name": "string", "agents": [], "compatibility": [] }] }` |
| `GET` | `/workflows/teams/{team_id}` | Get specific team configuration. | None | `{ "id": "string", "name": "string", "agents": [], "workflows": [], "capabilities": [] }` |
| `POST` | `/workflows/teams/{team_id}/validate` | Validate team compatibility with workflow. | `{ "workflow_id": "string" }` | `{ "compatible": true, "warnings": [], "recommendations": [] }` |

**Human-in-the-Loop (HITL):**

| Method | Endpoint | Description | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/hitl/{request_id}/respond` | Submits a user's response to a HITL request. | `{ "action": "string", "response_content": "string" }` | `{ "request_id": "uuid", "new_status": "string" }` |
| `GET` | `/hitl/{request_id}` | Get HITL request details. | None | `{ "request_id": "uuid", "question": "string", "status": "pending" }` |
| `GET` | `/hitl/project/{project_id}/requests` | Get all HITL requests for a project. | None | `{ "requests": [], "pending_count": 2 }` |

**System Health:**

| Method | Endpoint | Description | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/healthz` | Health check endpoint for system monitoring. | None | `{ "api_status": "ok", "db_status": "ok", "celery_status": "ok", "llm_status": "ok" }` |

#### **WebSocket Service (`/ws`)**

The WebSocket connection will stream a JSON object for each event. The `event_type` field will be used by the frontend to determine how to handle the message.

| Event Type | Description | Sample Payload |
| :--- | :--- | :--- |
| `agent_status_change` | Real-time agent status updates (Sprint 3). | `{ "event_type": "agent_status_change", "agent_type": "analyst", "data": { "status": "working", "current_task_id": "uuid", "last_activity": "ISO 8601" } }` |
| `artifact_created` | Notification when project artifacts are ready for download (Sprint 3). | `{ "event_type": "artifact_created", "project_id": "uuid", "data": { "message": "Project artifacts are ready for download", "download_available": true, "generated_at": "ISO 8601" } }` |
| `workflow_event` | Project completion and major workflow notifications (Sprint 3). | `{ "event_type": "workflow_event", "project_id": "uuid", "data": { "event": "project_completed", "message": "Project has completed successfully", "completed_at": "ISO 8601", "artifacts_generating": true } }` |
| `hitl_response` | Enhanced HITL response broadcasting (Sprint 3). | `{ "event_type": "hitl_response", "project_id": "uuid", "data": { "request_id": "uuid", "action": "approved", "response": "Looks good!", "timestamp": "ISO 8601" } }` |
| `agent_status_update` | Legacy agent status updates (pre-Sprint 3). | `{ "agent_type": "analyst", "status": "working", "timestamp": "ISO 8601" }` |
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
