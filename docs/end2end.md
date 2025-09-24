# End-to-End Testing Guide

## Overview

This document provides a comprehensive guide for performing end-to-end testing of the BMAD Enterprise AI Orchestration Platform. It includes the complete UI interaction sequence, expected API calls, and validation checkpoints for a typical project lifecycle.

## Test Environment Setup

### Prerequisites

1. **Backend Services Running:**
   - FastAPI backend at `http://localhost:8000`
   - PostgreSQL database
   - Redis cache/queue system
   - Celery workers

2. **Frontend Application:**
   - Next.js frontend at `http://localhost:3000`
   - WebSocket connection enabled

3. **Required Test Data:**
   - Clean database state
   - No existing projects (for fresh test)
   - Health endpoints responding

### Pre-Test Validation

Before starting the test sequence, verify these endpoints are healthy:

```bash
# Health check endpoints
GET http://localhost:8000/health                 # Should return 200 OK
GET http://localhost:8000/health/detailed        # Should show all services healthy
GET http://localhost:8000/api/v1/projects        # Should return empty array []
```

## Happy Path Test Sequence

### Phase 1: Application Load and Initial State

**UI Action:** Navigate to `http://localhost:3000`

**Expected UI State:**
- Main page loads with "BotArmy Agentic Builder" header
- "No projects yet" state is displayed
- "Create Your First Project" button is visible
- Connection status shows "Connected" (green dot)
- WebSocket connection established

**Technical UI Elements:**
- `[data-testid="main-layout"]` - Main layout container
- `[data-testid="project-dashboard"]` - Project dashboard component
- `[data-testid="project-stats"]` - Project statistics cards
- `[data-testid="empty-projects-state"]` - Empty state when no projects
- `button[data-testid="create-first-project"]` - "Create Your First Project" button
- `[data-testid="connection-status"]` - WebSocket connection indicator
- `[data-testid="connection-status-dot"]` - Connection status dot (green/red)

**Expected API Calls:**
1. `GET /api/v1/projects` - Fetches existing projects (returns `[]`)
2. WebSocket connection to `ws://localhost:8000/ws/` - Real-time event stream

**Validation Points:**
- [ ] Page loads within 3 seconds
- [ ] No JavaScript console errors
- [ ] WebSocket connection status: "Connected"
- [ ] Projects list shows empty state

---

### Phase 2: Project Creation Flow

#### Step 2.1: Open Project Creation Dialog

**UI Action:** Click "Create Your First Project" button

**Technical UI Action:**
```javascript
await page.click('button[data-testid="create-first-project"]');
```

**Expected UI State:**
- Modal dialog opens with title "Create New Project"
- Form fields are visible and empty
- "Create Project" button is disabled (form validation)

**Technical UI Elements:**
- `[data-testid="project-creation-dialog"]` - Modal dialog container
- `[data-testid="project-creation-form"]` - Main form element
- `input[data-testid="project-name-input"]` - Project name field
- `textarea[data-testid="project-description-input"]` - Description field
- `select[data-testid="project-priority-select"]` - Priority dropdown
- `input[data-testid="project-duration-input"]` - Duration field
- `input[data-testid="project-budget-input"]` - Budget field
- `input[data-testid="project-tags-input"]` - Tags input field
- `button[data-testid="add-tag-button"]` - Add tag button
- `button[data-testid="create-project-submit"]` - Submit button (disabled initially)

**Expected API Calls:** None

**Validation Points:**
- [ ] Modal opens smoothly
- [ ] All form fields are present and accessible
- [ ] Form validation is active

#### Step 2.2: Fill Project Details

**UI Actions (in sequence):**

1. **Project Name Field:**
   - Click on "Project Name" input field
   - Type: `"A simple To-Do list"`

   **Technical UI Actions:**
   ```javascript
   await page.click('input[data-testid="project-name-input"]');
   await page.fill('input[data-testid="project-name-input"]', 'A simple To-Do list');
   ```

2. **Description Field:**
   - Click on "Description" textarea
   - Type: `"Build a modern to-do list application with task management, and notifications."`

   **Technical UI Actions:**
   ```javascript
   await page.click('textarea[data-testid="project-description-input"]');
   await page.fill('textarea[data-testid="project-description-input"]', 'Build a modern to-do list application with task management, and notifications.');
   ```

3. **Priority Selection:**
   - Click on Priority dropdown
   - Select: `"Medium"`
   - Verify badge shows "MEDIUM PRIORITY" in default color

   **Technical UI Actions:**
   ```javascript
   await page.click('select[data-testid="project-priority-select"]');
   await page.selectOption('select[data-testid="project-priority-select"]', 'medium');
   await page.waitForSelector('[data-testid="priority-badge"]:has-text("MEDIUM PRIORITY")');
   ```

4. **Estimated Duration:**
   - Click on "Estimated Duration" input
   - Clear existing value
   - Type: `8`

   **Technical UI Actions:**
   ```javascript
   await page.click('input[data-testid="project-duration-input"]');
   await page.fill('input[data-testid="project-duration-input"]', '8');
   ```

5. **Budget Limit:**
   - Click on "Budget Limit" input
   - Clear existing value
   - Type: `5`

   **Technical UI Actions:**
   ```javascript
   await page.click('input[data-testid="project-budget-input"]');
   await page.fill('input[data-testid="project-budget-input"]', '5');
   ```

6. **Add Tags:**
   - Click on tags input field
   - Type: `"to-do"` and press Enter or click "Add"
   - Type: `"app"` and press Enter or click "Add"
   - Type: `"test"` and press Enter or click "Add"

   **Technical UI Actions:**
   ```javascript
   // Add first tag
   await page.fill('input[data-testid="project-tags-input"]', 'to-do');
   await page.click('button[data-testid="add-tag-button"]');
   await page.waitForSelector('[data-testid="tag-badge"]:has-text("to-do")');

   // Add second tag
   await page.fill('input[data-testid="project-tags-input"]', 'app');
   await page.click('button[data-testid="add-tag-button"]');
   await page.waitForSelector('[data-testid="tag-badge"]:has-text("app")');

   // Add third tag
   await page.fill('input[data-testid="project-tags-input"]', 'test');
   await page.click('button[data-testid="add-tag-button"]');
   await page.waitForSelector('[data-testid="tag-badge"]:has-text("test")');
   ```

**Expected UI State:**
- All fields are populated with test data
- Priority badge shows "MEDIUM PRIORITY" in default color
- Three tags are visible as badges with × symbols
- "Create Project" button becomes enabled
- No validation errors displayed

**Expected API Calls:** None (client-side validation only)

**Validation Points:**
- [ ] All input fields accept and display data correctly
- [ ] Priority dropdown updates badge color
- [ ] Tags are added and displayed as removable badges
- [ ] Form validation passes (Create button enabled)
- [ ] No form errors displayed

#### Step 2.3: Submit Project Creation

**UI Action:** Click "Create Project" button

**Technical UI Action:**
```javascript
await page.click('button[data-testid="create-project-submit"]');
await page.waitForSelector('button[data-testid="create-project-submit"]:has-text("Creating...")');
```

**Expected UI State:**
- Button shows loading state: "Creating..." with spinner
- Form becomes disabled during submission
- Modal remains open during creation

**Technical UI Elements:**
- `button[data-testid="create-project-submit"]:has-text("Creating...")` - Loading state button
- `[data-testid="loading-spinner"]` - Spinner icon in button
- `[data-testid="project-creation-form"][disabled]` - Disabled form during submission

**Expected API Calls:**
1. `POST /api/v1/projects` with request body:
   ```json
   {
     "name": "A simple To-Do list",
     "description": "Build a modern to-do list application with task management, and notifications.",
     "priority": "medium",
     "budget_limit": 5,
     "estimated_duration": 8,
     "tags": ["to-do", "app", "test"],
     "status": "pending",
     "agent_config": {
       "max_agents": 3,
       "agent_types": ["analyst", "architect", "developer"]
     }
   }
   ```

**Expected API Response:**
```json
{
  "data": {
    "id": "uuid-string",
    "name": "A simple To-Do list",
    "description": "Build a modern to-do list application with task management, and notifications.",
    "status": "active",
    "created_at": "2025-01-XX...",
    "updated_at": "2025-01-XX..."
  },
  "success": true,
  "message": "Project created successfully"
}
```

**Validation Points:**
- [ ] API call made with correct endpoint and payload
- [ ] Response returns 201 Created status
- [ ] Response contains valid project ID (UUID format)
- [ ] Response includes all submitted fields

#### Step 2.4: Project Creation Success

**Expected UI State:**
- Modal closes automatically
- Toast notification appears: "Project Created - Project 'A simple To-Do list' has been created successfully."
- Dashboard refreshes and shows the new project
- Project card displays with correct information
- Project becomes selected (highlighted with ring border)

**Technical UI Elements:**
- `[data-testid="project-creation-dialog"]` - Modal should close/disappear
- `[data-testid="toast-notification"]` - Success toast notification
- `[data-testid="toast-title"]:has-text("Project Created")` - Toast title
- `[data-testid="projects-grid"]` - Projects grid container
- `[data-testid="project-card"]` - Individual project card
- `[data-testid="project-card-selected"]` - Selected project card with ring border
- `[data-testid="project-title"]:has-text("A simple To-Do list")` - Project name in card

**Technical UI Validations:**
```javascript
// Wait for modal to close
await page.waitForSelector('[data-testid="project-creation-dialog"]', { state: 'hidden' });

// Wait for toast notification
await page.waitForSelector('[data-testid="toast-notification"]');
await page.waitForSelector('[data-testid="toast-title"]:has-text("Project Created")');

// Wait for project card to appear
await page.waitForSelector('[data-testid="project-card"]');
await page.waitForSelector('[data-testid="project-title"]:has-text("A simple To-Do list")');

// Verify project is selected
await page.waitForSelector('[data-testid="project-card-selected"]');
```

**Expected API Calls:**
1. `GET /api/v1/projects` - Refetches projects list

**WebSocket Events:**
- Project creation event broadcasted
- Status change events

**Validation Points:**
- [ ] Modal closes smoothly
- [ ] Success toast notification appears and auto-dismisses
- [ ] Projects list updates with new project
- [ ] Project card shows correct data
- [ ] Project card is selected (ring border visible)

---

### Phase 3: Project Dashboard Interaction

#### Step 3.1: Verify Project Card Display

**Expected UI State:**
- Project card shows:
  - Title: "A simple To-Do list"
  - Status badge: "ACTIVE" (green)
  - Description: Full description text (truncated if long)
  - Progress bar: 0%
  - Created date: Today's date
  - Time elapsed: "Just started"
  - Budget: "$5"
  - Duration: "8h est."
  - Tags: "to-do", "app", "test"
- Project stats updated:
  - Total Projects: 1
  - Active: 1
  - Completed: 0
  - Total Budget: $5

**Validation Points:**
- [ ] All project details display correctly
- [ ] Status badge color matches project status
- [ ] Progress bar shows 0%
- [ ] All metadata fields populated
- [ ] Statistics counters updated

#### Step 3.2: Project Details View

**UI Action:** Click on the project card (if not already selected)

**Expected UI State:**
- Project details panel appears on the right side
- Project information displayed:
  - Name: "A simple To-Do list"
  - Status: "active"
  - Progress: "0%"
  - Budget: "$5"
  - Duration: "8h"
  - Description: Full text

**Expected API Calls:**
1. `GET /api/v1/projects/{project_id}/status` - Fetch project tasks and detailed status

**Validation Points:**
- [ ] Project details panel populates
- [ ] All fields match creation data
- [ ] Status API call made for detailed information

#### Step 3.3: Chat Interface Activation

**Expected UI State after Project Selection:**
- Chat interface appears in the right column (alongside project details)
- CopilotChat component renders with project context
- Chat window shows project-specific conversation
- Welcome message appears: "You're now working on: A simple To-Do list"
- Chat input field is active and ready for user input

**Technical UI Elements:**
- `[data-testid="chat-interface"]` - Main chat container
- `[data-testid="copilot-chat"]` - CopilotChat component
- `[data-testid="chat-messages"]` - Chat messages container
- `[data-testid="chat-welcome-message"]` - Welcome message
- `[data-testid="chat-input"]` - Chat input field
- `[data-testid="chat-send-button"]` - Send message button
- `[data-testid="project-details-panel"]` - Project details panel (left column)

**Technical UI Validations:**
```javascript
// Wait for chat interface to appear
await page.waitForSelector('[data-testid="chat-interface"]');
await page.waitForSelector('[data-testid="copilot-chat"]');

// Verify welcome message
await page.waitForSelector('[data-testid="chat-welcome-message"]:has-text("A simple To-Do list")');

// Verify chat input is active
await page.waitForSelector('[data-testid="chat-input"]');
await expect(page.locator('[data-testid="chat-input"]')).toBeEnabled();
```

**Expected API Calls:**
1. WebSocket connection scoped to project: `ws://localhost:8000/ws/{project_id}`
2. `GET /api/v1/projects/{project_id}/context` - Load project conversation history

**Validation Points:**
- [ ] Chat window appears and is functional
- [ ] Project-scoped WebSocket connection established
- [ ] Chat input field accepts user input
- [ ] Project context loaded in chat interface

#### Step 3.4: User-Agent Chat Interaction

**UI Actions:**
1. **User Input:**
   - Click in chat input field
   - Type: `"Let's start building the to-do app. What should we do first?"`
   - Press Enter or click Send button

   **Technical UI Actions:**
   ```javascript
   await page.click('[data-testid="chat-input"]');
   await page.fill('[data-testid="chat-input"]', "Let's start building the to-do app. What should we do first?");
   await page.click('[data-testid="chat-send-button"]');
   ```

2. **Expected Chat Flow:**
   - User message appears in chat with timestamp
   - "Agent is typing..." indicator appears
   - System processes message and determines appropriate agent response

   **Technical UI Elements:**
   - `[data-testid="user-message"]` - User message bubble
   - `[data-testid="message-timestamp"]` - Message timestamp
   - `[data-testid="agent-typing-indicator"]` - "Agent is typing..." indicator
   - `[data-testid="agent-message"]` - Agent response message

**Expected UI State:**
- User message bubble appears (right-aligned, user styling)
- Loading indicator shows agent is processing
- Chat window auto-scrolls to show latest message

**Expected API Calls:**
1. `POST /api/v1/chat/message` with payload:
   ```json
   {
     "project_id": "uuid",
     "message": "Let's start building the to-do app. What should we do first?",
     "user_id": "current_user",
     "timestamp": "2025-01-XX..."
   }
   ```

2. Agent processing triggers task creation automatically
3. WebSocket events for real-time chat updates

**Expected Agent Response:**
- Agent message appears (left-aligned, agent styling)
- Message content suggests next steps:
  ```
  "I'll help you build the to-do app! Let me start by analyzing the requirements.
  I'm creating a task to gather detailed requirements and user stories.
  You'll need to approve this task before I can proceed."
  ```

**WebSocket Events:**
- Chat message events
- Agent status updates
- Task creation notifications

**Validation Points:**
- [ ] User message appears correctly in chat
- [ ] Agent processes message and responds appropriately
- [ ] Chat interface updates in real-time via WebSocket
- [ ] Agent automatically creates relevant tasks based on conversation

---

### Phase 4: Task Creation and Management

#### Step 4.1: Create First Task

**UI Action:** Navigate to project management or use task creation interface

**Expected UI Actions:**
1. Click "Create Task" or equivalent button
2. Fill task form:
   - Agent Type: `"analyst"`
   - Instructions: `"Analyze requirements for the to-do list application and create detailed user stories"`
   - Context IDs: `[]` (empty)
   - Estimated Tokens: `500`

**Expected API Calls:**
1. `POST /api/v1/projects/{project_id}/tasks` with payload:
   ```json
   {
     "agent_type": "analyst",
     "instructions": "Analyze requirements for the to-do list application and create detailed user stories",
     "context_ids": [],
     "estimated_tokens": 500
   }
   ```

**Expected API Response:**
```json
{
  "task_id": "uuid-string",
  "celery_task_id": "celery-uuid",
  "status": "submitted",
  "hitl_required": true,
  "estimated_tokens": 500,
  "message": "Task created but requires HITL approval before execution"
}
```

**Validation Points:**
- [ ] Task creation API succeeds
- [ ] Response indicates HITL approval required
- [ ] Celery task ID returned for tracking

#### Step 4.2: HITL Approval Process and UI Integration

**Expected WebSocket Events:**
- New HITL request notification
- Task status change events
- HITL alert broadcasting

**Expected API Calls (automatic):**
1. `GET /api/v1/hitl/requests` - Fetch pending HITL requests
2. WebSocket events for real-time updates

**Expected UI State Changes:**

1. **HITL Alerts Bar Activation:**
   - HitlAlertsBar component appears at top of interface
   - Alert notification shows: "⚠️ HITL Approval Required"
   - Alert shows task details: "Analyst task needs approval"
   - Click-through link to approval interface
   - Red/orange styling to indicate urgency

   **Technical UI Elements:**
   - `[data-testid="hitl-alerts-bar"]` - Main alerts bar container
   - `[data-testid="hitl-alert"]` - Individual HITL alert
   - `[data-testid="hitl-alert-icon"]` - Warning icon (⚠️)
   - `[data-testid="hitl-alert-title"]` - Alert title text
   - `[data-testid="hitl-alert-details"]` - Task details text
   - `[data-testid="hitl-alert-link"]` - Click-through link to approval
   - `[data-testid="hitl-alert-dismiss"]` - Dismiss button (if present)

2. **Chat Window Integration:**
   - Agent message appears in chat:
     ```
     "🤖 I've created a requirements analysis task that needs your approval.
     Task: Analyze requirements for the to-do list application
     Estimated cost: $2.50 (500 tokens)
     Please approve this task so I can proceed."
     ```
   - HITL approval buttons embedded in chat message:
     - ✅ "Approve" button (green)
     - ❌ "Reject" button (red)
     - 💬 "Comment" field for feedback

   **Technical UI Elements:**
   - `[data-testid="hitl-chat-message"]` - HITL request message in chat
   - `[data-testid="hitl-message-content"]` - Message content text
   - `[data-testid="hitl-task-details"]` - Task details within message
   - `[data-testid="hitl-cost-estimate"]` - Cost estimate display
   - `[data-testid="hitl-approve-button"]` - Approve button in chat
   - `[data-testid="hitl-reject-button"]` - Reject button in chat
   - `[data-testid="hitl-comment-input"]` - Comment input field
   - `[data-testid="hitl-buttons-container"]` - Container for action buttons

3. **Project Status Updates:**
   - Task status shows "Pending Approval" with pending icon
   - Project progress paused until approval

**UI Actions for HITL Approval:**

**Option A - Via Alerts Bar:**
1. Click on HITL alert in alerts bar
2. Review task details in modal/panel
3. Click "Approve" button
4. Optional: Add approval comment

**Technical UI Actions (Option A):**
```javascript
// Click on HITL alert
await page.click('[data-testid="hitl-alert"]');

// Wait for approval modal/panel
await page.waitForSelector('[data-testid="hitl-approval-modal"]');

// Review details and approve
await page.click('[data-testid="hitl-modal-approve-button"]');

// Optional: Add comment
await page.fill('[data-testid="hitl-modal-comment"]', 'Approved - proceed with requirements analysis');
```

**Option B - Via Chat Interface:**
1. Scroll to agent message with HITL request
2. Click embedded "Approve" button in chat
3. Optional: Add comment in embedded field
4. Confirm approval

**Technical UI Actions (Option B):**
```javascript
// Scroll to HITL message in chat
await page.scrollIntoViewIfNeeded('[data-testid="hitl-chat-message"]');

// Optional: Add comment before approving
await page.fill('[data-testid="hitl-comment-input"]', 'Approved - proceed with requirements analysis');

// Click approve button in chat
await page.click('[data-testid="hitl-approve-button"]');

// Wait for approval confirmation
await page.waitForSelector('[data-testid="hitl-approved-indicator"]');
```

**Expected API Calls for Approval:**
```json
POST /api/v1/hitl/requests/{request_id}/respond
{
  "action": "approve",
  "content": null,
  "comment": "Approved - proceed with requirements analysis"
}
```

**Expected UI State After Approval:**

1. **Alerts Bar:**
   - HITL alert disappears or shows "✅ Approved"
   - Green success notification briefly appears

2. **Chat Window:**
   - Agent follow-up message appears:
     ```
     "✅ Task approved! Starting requirements analysis now.
     I'll analyze the to-do list requirements and create user stories.
     This should take about 2-3 minutes..."
     ```
   - HITL approval buttons become disabled/hidden
   - "Approved" status shown on the message

3. **Project Dashboard:**
   - Task status changes to "In Progress"
   - Agent status indicator shows "Working"
   - Progress bar may increment slightly

**WebSocket Events During HITL Flow:**
1. `hitl_request_created` - Triggers alerts bar and chat notification
2. `hitl_request_approved` - Updates UI states
3. `task_status_updated` - Changes task from pending to in_progress
4. `agent_status_updated` - Shows agent as active/working

**Performance Expectations:**
- HITL alert appears within 500ms of task creation
- Chat message appears within 1 second
- Approval action processes within 2 seconds
- UI state updates appear immediately via WebSocket

**Validation Points:**
- [ ] HITL alert appears in alerts bar immediately
- [ ] Agent posts HITL request message in chat
- [ ] Approval buttons are functional in both locations
- [ ] WebSocket events trigger real-time UI updates
- [ ] Task status updates after approval
- [ ] Agent begins work after approval confirmation
- [ ] All UI components sync state correctly

---

### Phase 5: Real-Time Monitoring

#### Step 5.1: WebSocket Event Verification

**Expected WebSocket Events During Test:**
1. Project creation event
2. Task submission event
3. HITL request creation
4. Status change events
5. Progress updates

**Event Structure:**
```json
{
  "type": "project_update",
  "project_id": "uuid",
  "data": {
    "status": "active",
    "progress": 15,
    "updated_at": "timestamp"
  }
}
```

**Validation Points:**
- [ ] WebSocket connection remains stable
- [ ] Events received in real-time
- [ ] UI updates reflect event data
- [ ] No connection drops or errors

#### Step 5.2: Health Monitoring

**Expected API Calls (periodic):**
1. `GET /health` - Basic health check
2. `GET /health/detailed` - Component health status

**Expected UI Indicators:**
- Connection status: "Connected" (green)
- System health: All services operational
- Performance metrics within normal ranges

**Validation Points:**
- [ ] Health endpoints respond < 200ms
- [ ] All system components healthy
- [ ] Connection status indicators accurate

---

### Phase 6: Project Status Updates

#### Step 6.1: Status Change Operations

**UI Actions to Test:**

1. **Pause Project:**
   - Click project card dropdown menu (⋮)
   - Select "Pause Project"
   - Verify status changes to "PAUSED" (yellow badge)

2. **Resume Project:**
   - Click dropdown menu again
   - Select "Resume Project"
   - Verify status returns to "ACTIVE" (green badge)

**Expected API Calls:**
1. `PUT /api/v1/projects/{project_id}` with status update
2. `GET /api/v1/projects` - Refresh projects list

**WebSocket Events:**
- Project status change notifications
- Real-time UI updates

**Validation Points:**
- [ ] Status changes reflected immediately
- [ ] API calls successful
- [ ] WebSocket events fired
- [ ] UI updates without page refresh

#### Step 6.2: Progress Tracking

**Expected Behavior:**
- Progress bar updates as tasks complete
- Percentage calculated based on task completion
- Real-time updates via WebSocket

**API Monitoring:**
1. `GET /api/v1/projects/{project_id}/status` - Progress updates
2. WebSocket events for real-time progress

**Validation Points:**
- [ ] Progress calculations accurate
- [ ] Real-time updates working
- [ ] Visual indicators update smoothly

---

### Phase 7: Completion and Cleanup

#### Step 7.1: Project Completion

**UI Action:** Mark project as complete

**Expected API Calls:**
1. `POST /api/v1/projects/{project_id}/check-completion` - Verify completion criteria
2. `POST /api/v1/projects/{project_id}/force-complete` - If manual completion

**Expected API Response:**
```json
{
  "project_id": "uuid",
  "is_complete": true,
  "message": "Project completion checked and completed"
}
```

**Expected UI Changes:**
- Project status badge changes to "COMPLETED" (blue)
- Project moves to completed section
- Statistics update: Completed count increases

**Validation Points:**
- [ ] Completion API succeeds
- [ ] Status updates correctly
- [ ] UI reflects completion state

#### Step 7.2: Final Verification

**Final State Checks:**
1. Project appears in completed projects
2. All tasks marked as complete
3. Final artifacts generated (if applicable)
4. Audit trail complete

**API Verification:**
1. `GET /api/v1/projects` - Final projects list
2. `GET /api/v1/audit/events` - Audit trail verification

**Validation Points:**
- [ ] Project lifecycle completed successfully
- [ ] All data persisted correctly
- [ ] Audit trail captures all events
- [ ] No data corruption or loss

---

## Error Scenarios to Test

### Network Failures

1. **WebSocket Disconnection:**
   - Disconnect network during test
   - Verify reconnection and state sync
   - Check for lost events

2. **API Timeout:**
   - Simulate slow backend responses
   - Verify timeout handling and retries
   - Check user feedback

### Validation Errors

1. **Invalid Project Data:**
   - Submit empty project name
   - Exceed budget limits
   - Verify error handling

2. **Duplicate Operations:**
   - Create duplicate projects
   - Submit multiple identical tasks
   - Verify conflict resolution

### State Management Issues

1. **Concurrent Operations:**
   - Multiple users modifying same project
   - Verify optimistic updates
   - Check conflict resolution

2. **Browser Refresh:**
   - Refresh during operations
   - Verify state recovery
   - Check data consistency

---

## Performance Benchmarks

### Response Time Targets

- **Page Load:** < 3 seconds
- **API Calls:** < 200ms average
- **WebSocket Latency:** < 100ms
- **UI Interactions:** < 150ms

### Load Testing

1. **Concurrent Users:** Test with 10+ simultaneous users
2. **Project Volume:** Test with 50+ projects
3. **Task Throughput:** Test with 100+ concurrent tasks

### Memory and Resource Usage

- **Frontend Memory:** Monitor for memory leaks
- **WebSocket Connections:** Verify proper cleanup
- **API Rate Limiting:** Test rate limit boundaries

---

## Automation Commands

### Complete Puppeteer Test Script

```javascript
const { test, expect } = require('@playwright/test');

test('Complete E2E Project Creation and HITL Flow', async ({ page }) => {
  // Phase 1: Navigate to application
  await page.goto('http://localhost:3000');

  // Wait for initial load
  await page.waitForSelector('[data-testid="project-dashboard"]');
  await page.waitForSelector('[data-testid="connection-status-dot"]');

  // Verify empty state
  await page.waitForSelector('[data-testid="empty-projects-state"]');

  // Phase 2: Create new project
  await page.click('button[data-testid="create-first-project"]');
  await page.waitForSelector('[data-testid="project-creation-dialog"]');

  // Fill project details
  await page.fill('input[data-testid="project-name-input"]', 'A simple To-Do list');
  await page.fill('textarea[data-testid="project-description-input"]', 'Build a modern to-do list application with task management, and notifications.');

  // Set priority
  await page.selectOption('select[data-testid="project-priority-select"]', 'medium');
  await page.waitForSelector('[data-testid="priority-badge"]:has-text("MEDIUM PRIORITY")');

  // Add budget and duration
  await page.fill('input[data-testid="project-budget-input"]', '5');
  await page.fill('input[data-testid="project-duration-input"]', '8');

  // Add tags
  await page.fill('input[data-testid="project-tags-input"]', 'to-do');
  await page.click('button[data-testid="add-tag-button"]');
  await page.waitForSelector('[data-testid="tag-badge"]:has-text("to-do")');

  await page.fill('input[data-testid="project-tags-input"]', 'app');
  await page.click('button[data-testid="add-tag-button"]');
  await page.waitForSelector('[data-testid="tag-badge"]:has-text("app")');

  await page.fill('input[data-testid="project-tags-input"]', 'test');
  await page.click('button[data-testid="add-tag-button"]');
  await page.waitForSelector('[data-testid="tag-badge"]:has-text("test")');

  // Submit form
  await page.click('button[data-testid="create-project-submit"]');
  await page.waitForSelector('button[data-testid="create-project-submit"]:has-text("Creating...")');

  // Phase 3: Verify project creation success
  await page.waitForSelector('[data-testid="project-creation-dialog"]', { state: 'hidden' });
  await page.waitForSelector('[data-testid="toast-notification"]');
  await page.waitForSelector('[data-testid="project-card"]');
  await page.waitForSelector('[data-testid="project-title"]:has-text("A simple To-Do list")');

  // Phase 4: Verify chat interface activation
  await page.waitForSelector('[data-testid="chat-interface"]');
  await page.waitForSelector('[data-testid="copilot-chat"]');
  await page.waitForSelector('[data-testid="chat-welcome-message"]');

  // Phase 5: Test user-agent interaction
  await page.click('[data-testid="chat-input"]');
  await page.fill('[data-testid="chat-input"]', "Let's start building the to-do app. What should we do first?");
  await page.click('[data-testid="chat-send-button"]');

  // Wait for user message to appear
  await page.waitForSelector('[data-testid="user-message"]');

  // Wait for agent response and HITL request
  await page.waitForSelector('[data-testid="agent-message"]');
  await page.waitForSelector('[data-testid="hitl-chat-message"]');

  // Phase 6: Test HITL approval flow
  // Verify HITL alerts bar appears
  await page.waitForSelector('[data-testid="hitl-alerts-bar"]');
  await page.waitForSelector('[data-testid="hitl-alert"]');

  // Test approval via chat interface
  await page.scrollIntoViewIfNeeded('[data-testid="hitl-chat-message"]');
  await page.fill('[data-testid="hitl-comment-input"]', 'Approved - proceed with requirements analysis');
  await page.click('[data-testid="hitl-approve-button"]');

  // Verify approval success
  await page.waitForSelector('[data-testid="hitl-approved-indicator"]');
  await page.waitForSelector('[data-testid="agent-message"]:has-text("Task approved")');

  // Verify HITL alert disappears or shows success
  await page.waitForSelector('[data-testid="hitl-alerts-bar"]', { state: 'hidden' });

  console.log('✅ Complete E2E test passed successfully');
});
```

### API Test Sequence

```bash
#!/bin/bash

# Health check
curl -s http://localhost:8000/health | jq .

# Create project
PROJECT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "A simple To-Do list",
    "description": "Build a modern to-do list application with task management, and notifications."
  }')

PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.data.id')

# Create task
curl -s -X POST http://localhost:8000/api/v1/projects/$PROJECT_ID/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "analyst",
    "instructions": "Analyze requirements for the to-do list application",
    "estimated_tokens": 500
  }' | jq .

# Check project status
curl -s http://localhost:8000/api/v1/projects/$PROJECT_ID/status | jq .
```

---

## Test Results Documentation

### Success Criteria

For a successful end-to-end test, all of the following must pass:

- [ ] **UI Loading:** All pages load within performance targets
- [ ] **API Integration:** All API calls succeed with correct responses
- [ ] **WebSocket Communication:** Real-time events work correctly
- [ ] **Data Persistence:** All data survives operations and refreshes
- [ ] **Error Handling:** Graceful degradation for error scenarios
- [ ] **Performance:** Response times within acceptable ranges
- [ ] **Security:** No exposed sensitive data or security vulnerabilities

### Reporting Template

```markdown
## Test Execution Report

**Date:** [Date]
**Tester:** [Name]
**Environment:** [Dev/Staging/Prod]
**Duration:** [X minutes]

### Results Summary
- Total Test Steps: [X]
- Passed: [X]
- Failed: [X]
- Skipped: [X]

### Failed Tests
[List any failed tests with details]

### Performance Metrics
- Average API Response Time: [X]ms
- Page Load Time: [X]s
- WebSocket Latency: [X]ms

### Issues Found
[List any bugs or issues discovered]

### Recommendations
[Any recommendations for fixes or improvements]
```

This comprehensive end-to-end testing guide ensures thorough validation of the BMAD platform's complete functionality, from initial load through project completion, with specific UI interactions, API calls, and validation points clearly defined for repeatable testing.

Flow Diagram (Mermaid)
sequenceDiagram
    participant User
    participant Frontend
    participant Backend_API
    participant Orchestrator
    participant WebSocket
    participant Database
    participant Celery
    participant Agent
    participant Redis
    participant Startup_Script

    box "System Initialization"
        participant Startup_Script
        participant Redis
    end

    box "User Interface"
        participant User
        participant Frontend
    end

    box "Backend Services"
        participant Backend_API
        participant Orchestrator
        participant WebSocket
        participant Celery
        participant Agent
    end

    box "Data Stores"
        participant Database
    end

    Note over Startup_Script, Celery: Step 0: System Initialization
    Startup_Script->>Redis: Flush cache
    Startup_Script->>Celery: Purge tasks

    Note over User, Agent: Steps 1-3: Initial Load & Chat Interaction
    User->>Frontend: 1. Load application
    Frontend->>Backend_API: 2. GET /api/v1/projects
    Backend_API->>Database: Query projects

    User->>Frontend: 3. Send chat message
    Frontend->>Backend_API: POST /api/v1/chat/message
    Backend_API->>Orchestrator: Forward message

    Note over User, Agent: Steps 4-7: Orchestration & Task Dispatch
    Orchestrator->>Database: 4. Create task (status: pending)
    Orchestrator->>WebSocket: 5. Broadcast 'hitl_request_created'
    WebSocket-->>Frontend: Display approval UI

    User->>Frontend: 6. Approve task
    Frontend->>Backend_API: POST /hitl/.../respond
    Backend_API->>Orchestrator: Forward approval

    Orchestrator->>Database: 7. Update task (status: in_progress)
    Orchestrator->>Celery: Dispatch task to Agent

    Note over User, Agent: Steps 8-10: Agent Action & Completion
    activate Celery
    Celery->>Agent: 8. Pick up and execute task
    activate Agent
    Agent->>Database: 9. Update status to 'complete' & save results
    deactivate Agent
    deactivate Celery

    Orchestrator->>WebSocket: 10. Broadcast 'task_complete'
    WebSocket-->>Frontend: Display final status
   1

  ---

  Step-by-Step Flow (Text)

    1 ### Definitive Happy Path: Full Component Flow with Orchestrator (v2)
    2
    3 0.  **System Initialization (Server Startup):**
    4     `Startup Script` -> `Redis` (Flushes cache) & `Celery` (Purges tasks) to ensure a clean state.
    5
    6 1.  **Initial Load:**
    7     `User` -> `Frontend` -> `Backend (API)` -> `Database`
    8
    9 2.  **Project Creation:**
   10     `User` -> `Frontend` (Submits form) -> `Backend (API)` -> `Database` (Saves project)
   11     *Then:* `Backend (API)` -> `WebSocket` -> `Frontend` (UI updates in real-time)
   12
   13 3.  **Chat Interaction:**
   14     `User` -> `Frontend` (Sends chat message) -> `Backend (API)`
   15     *Then:* `Backend (API)` -> `Orchestrator` (Forwards user message for processing)
   16
   17 4.  **Orchestration & Task Creation:**
   18     `Orchestrator` (Determines an `Analyst` agent is needed and a new task must be created for HITL) ->
      `Database` (Creates task with 'pending' status)
   19
   20 5.  **HITL Approval Request:**
   21     `Orchestrator` -> `WebSocket` -> `Frontend` (Displays approval UI)
   22
   23 6.  **User Approval:**
   24     `User` -> `Frontend` (Approves task in UI) -> `Backend (API)`
   25     *Then:* `Backend (API)` -> `Orchestrator` (Forwards the approval)
   26
   27 7.  **Task Dispatch by Orchestrator:**
   28     `Orchestrator` (Receives approval) -> `Database` (Updates task status to 'in_progress')
   29     *And:* `Orchestrator` -> `Celery` (Dispatches the task to be picked up by an `Analyst` agent)
   30
   31 8.  **Agent Action:**
   32     `Celery` -> `Agent (Analyst)` (Picks up and executes the task)
   33
   34 9.  **Agent Reports Completion:**
   35     `Agent (Analyst)` (Finishes task) -> `Database` (Updates task status to **'complete'** and saves
      results)
   36
   37 10. **Final State Broadcast:**
   38     `Orchestrator` (Detects the 'complete' status in the database) -> `WebSocket` -> `Frontend`
      (Displays the final task status)
