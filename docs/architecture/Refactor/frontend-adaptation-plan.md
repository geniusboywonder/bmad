# Frontend Adaptation Plan: v0-botarmy-poc → BMAD Frontend

## Executive Summary

I've successfully analyzed the existing UI codebase and backend API structure. The existing frontend provides an **excellent foundation** with 80% of components directly applicable. However, significant adaptation is required to integrate with the new backend API contract and fulfill Task 7 requirements.

---

## Analysis: Existing UI Assets

### ✅ **Directly Usable Components (Minimal Changes)**

**1. Enhanced Chat Interface** (`components/mockups/enhanced-chat-interface.tsx`)
- **Status**: Production-ready with minor API integration
- **Features**: Resizable panels, collapsible messages, real-time status overlays, role-based icons
- **Integration Needed**: WebSocket event mapping to backend `/ws/{project_id}` format

**2. UI Component Library** (`components/ui/*`)
- **Status**: Complete shadcn/ui implementation
- **Assets**: 25+ production-ready components (Card, Button, Input, ScrollArea, etc.)
- **Integration**: Zero changes required

**3. Zustand State Management** (`lib/stores/*`)
- **Existing Stores**: 10+ stores including `hitl-store`, `process-store`, `artifact-store`
- **Integration**: Schema updates for backend data structures

**4. WebSocket Infrastructure** (`hooks/use-websocket-connection.ts`, `lib/websocket/*`)
- **Status**: Core architecture complete
- **Integration**: Event mapping and connection URL updates

---

## Gap Analysis: Backend Integration Requirements

### 🔴 **Critical Missing Components (New Development)**

**1. Project Management Interface**
```typescript
// Required: frontend/src/components/ProjectDashboard.tsx
// Maps to: POST /api/v1/projects, GET /api/v1/projects/{id}
// Features: Project creation, status monitoring, completion tracking
```

**2. HITL Approval Interface**
```typescript
// Required: frontend/src/components/HitlApprovalPanel.tsx
// Maps to: POST /hitl/{request_id}/respond, GET /hitl/pending
// Features: Approve/Reject/Amend actions, context viewing
```

**3. Context Artifact Viewer**
```typescript
// Required: frontend/src/components/ArtifactViewer.tsx
// Maps to: GET /context/artifacts/{id}, GET /artifacts/{project_id}/download
// Features: Artifact display, ZIP download functionality
```

**4. Real-time Agent Status Display**
```typescript
// Required: frontend/src/components/AgentStatus.tsx
// Maps to: GET /agents/status, WebSocket agent_status_change events
// Features: Live agent monitoring, status history
```

### 🟡 **Major Adaptations Required**

**1. API Service Layer** (`lib/api/*)
- **Current**: Mock data and placeholder endpoints
- **Required**: Complete REST client for 67 backend endpoints
- **Implementation**: TypeScript client with proper error handling

**2. Type Definitions** (`lib/types.ts`)
- **Current**: Frontend-focused types (Task, Artifact, ProcessStage)
- **Required**: Backend-aligned schemas (Project, HitlRequest, EventLog)
- **Gap**: UUID handling, backend enum values, API response structures

**3. WebSocket Event Handling**
- **Current**: Generic message handling
- **Required**: Specific event types: `hitl_request`, `agent_status_change`, `workflow_event`, `artifact_created`

---

## Implementation Strategy

### Phase 1: Foundation Setup (Days 1-2)
```bash
# 1. Initialize Next.js project in frontend/
cd frontend/
npm install
npm run dev  # Verify base setup

# 2. Update configurations
# - Update WebSocket URL to ws://localhost:8000/ws/{project_id}
# - Configure API base URL to http://localhost:8000
# - Update package.json scripts for backend integration
```

### Phase 2: Backend Integration (Days 3-5)
```typescript
// 3. Create API service layer
// File: frontend/src/services/api.ts
export class BmadApiClient {
  // Project Management
  async createProject(productIdea: string): Promise<Project>
  async getProject(projectId: string): Promise<ProjectDetails>

  // HITL Management
  async getPendingHitlRequests(): Promise<HitlRequest[]>
  async respondToHitlRequest(requestId: string, action: HitlAction): Promise<void>

  // Agent Status
  async getAgentStatus(): Promise<AgentStatus[]>

  // Artifacts
  async getArtifacts(projectId: string): Promise<Artifact[]>
  async downloadArtifacts(projectId: string): Promise<Blob>
}

// 4. Update type definitions
// File: frontend/src/types/backend.ts
interface Project {
  id: string;
  name: string;
  status: 'active' | 'completed' | 'failed';
  created_at: string;
}

interface HitlRequest {
  id: string;
  task_id: string;
  request_content: string;
  status: 'pending' | 'approved' | 'rejected' | 'amended';
}
```

### Phase 3: Component Development (Days 6-8)
```typescript
// 5. Build core components
// ProjectDashboard.tsx - Project creation and monitoring
// HitlApprovalPanel.tsx - Human oversight interface
// ArtifactViewer.tsx - Context artifact display
// AgentStatus.tsx - Real-time agent monitoring

// 6. Update existing components
// Enhanced chat interface WebSocket event mapping
// Store integrations with backend schemas
```

### Phase 4: Real-time Integration (Days 9-10)
```typescript
// 7. WebSocket event handling
const websocketEvents = {
  'agent_status_change': handleAgentStatusUpdate,
  'hitl_request': handleNewHitlRequest,
  'workflow_event': handleWorkflowProgress,
  'artifact_created': handleArtifactReady,
}

// 8. End-to-end testing
// User creates project → Agent execution → HITL approval → Artifact download
```

---

## Detailed Component Specifications

### 1. **ProjectDashboard Component**

**Purpose**: Central project management interface
**Location**: `frontend/src/components/ProjectDashboard.tsx`

```typescript
interface ProjectDashboardProps {
  projectId?: string;
}

interface ProjectMetrics {
  completion_percentage: number;
  total_tasks: number;
  completed_tasks: number;
  artifacts_available: boolean;
}

// Features:
// - Project creation form (product idea input)
// - Real-time project status display
// - Task progress visualization
// - Completion metrics dashboard
// - Force completion admin function
```

**API Integration**:
- `POST /api/v1/projects` - Project creation
- `GET /api/v1/projects/{project_id}` - Status retrieval
- `GET /api/v1/projects/{project_id}/completion` - Metrics display

### 2. **HitlApprovalPanel Component**

**Purpose**: Human-in-the-loop decision interface
**Location**: `frontend/src/components/HitlApprovalPanel.tsx`

```typescript
interface HitlApprovalPanelProps {
  requestId?: string;
  showPending?: boolean;
}

interface HitlAction {
  action: 'approve' | 'reject' | 'amend';
  response: string;
  amended_content?: any;
  comment?: string;
}

// Features:
// - Pending requests queue display
// - Request context viewer (task details, artifacts)
// - Action buttons (Approve/Reject/Amend)
// - Comment/amendment input fields
// - Bulk approval functionality
// - Request history display
```

**API Integration**:
- `GET /hitl/pending` - Fetch pending requests
- `GET /hitl/{request_id}` - Request details
- `GET /hitl/{request_id}/context` - Full context
- `POST /hitl/{request_id}/respond` - Submit decision

### 3. **ArtifactViewer Component**

**Purpose**: Context artifact display and download
**Location**: `frontend/src/components/ArtifactViewer.tsx`

```typescript
interface ArtifactViewerProps {
  projectId: string;
  artifactId?: string;
}

interface Artifact {
  id: string;
  project_id: string;
  source_agent: string;
  artifact_type: 'spec' | 'plan' | 'code' | 'log';
  content: any;
  metadata?: any;
}

// Features:
// - Artifact browser with type filtering
// - Content viewer with syntax highlighting
// - Download individual artifacts
// - Generate and download project ZIP
// - Artifact versioning display
```

**API Integration**:
- `GET /context/project/{project_id}/artifacts` - List artifacts
- `GET /context/artifacts/{artifact_id}` - Artifact content
- `POST /artifacts/{project_id}/generate` - Generate ZIP
- `GET /artifacts/{project_id}/download` - Download ZIP

### 4. **AgentStatus Component**

**Purpose**: Real-time agent monitoring
**Location**: `frontend/src/components/AgentStatus.tsx`

```typescript
interface AgentStatusProps {
  agentType?: string;
  compact?: boolean;
}

interface AgentStatus {
  agent_type: string;
  status: 'idle' | 'working' | 'error';
  current_task_id?: string;
  last_activity: string;
}

// Features:
// - Live agent status indicators
// - Current task display
// - Status history timeline
// - Agent reset functionality (admin)
// - Performance metrics display
```

**API Integration**:
- `GET /agents/status` - All agent status
- `GET /agents/status/{agent_type}` - Specific agent
- `GET /agents/status-history/{agent_type}` - History
- `POST /agents/status/{agent_type}/reset` - Reset agent

---

## WebSocket Event Mapping

### Current vs Required Events

**Existing Events** (Generic):
```typescript
interface WebSocketMessage {
  type: string;
  data?: any;
  agent_name?: string;
  content?: string;
  timestamp: string;
}
```

**Required Events** (Backend-Specific):
```typescript
// Agent status updates
{
  event_type: "agent_status_change",
  agent_type: "analyst",
  data: {
    status: "working",
    current_task_id: "uuid",
    last_activity: "ISO 8601"
  }
}

// HITL request notifications
{
  event_type: "hitl_request",
  project_id: "uuid",
  data: {
    request_id: "uuid",
    question: "Please review the plan...",
    timestamp: "ISO 8601"
  }
}

// Workflow progress updates
{
  event_type: "workflow_event",
  project_id: "uuid",
  data: {
    event: "project_completed",
    message: "Project has completed successfully",
    completed_at: "ISO 8601",
    artifacts_generating: true
  }
}

// Artifact creation notifications
{
  event_type: "artifact_created",
  project_id: "uuid",
  data: {
    message: "Project artifacts are ready for download",
    download_available: true,
    generated_at: "ISO 8601"
  }
}
```

---

## Configuration Updates Required

### 1. **package.json Updates**
```json
{
  "name": "bmad-frontend",
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start",
    "backend:dev": "cd ../backend && python -m uvicorn app.main:app --reload --port 8000",
    "full:dev": "concurrently \"npm run backend:dev\" \"npm run dev\""
  },
  "dependencies": {
    // Remove CopilotKit dependencies (not needed)
    // Add if missing: axios, react-query, date-fns
  }
}
```

### 2. **Environment Configuration**
```bash
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000
NEXT_PUBLIC_API_V1_PREFIX=/api/v1
```

### 3. **next.config.mjs Updates**
```javascript
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}
```

---

## Testing Strategy

### **Component Testing** (Vitest + React Testing Library)
```typescript
// Tests required for new components
// frontend/src/__tests__/ProjectDashboard.test.tsx
// frontend/src/__tests__/HitlApprovalPanel.test.tsx
// frontend/src/__tests__/ArtifactViewer.test.tsx
// frontend/src/__tests__/AgentStatus.test.tsx

describe('ProjectDashboard', () => {
  it('creates new project with valid product idea', async () => {
    // Test project creation flow
  })

  it('displays real-time project status updates', async () => {
    // Test WebSocket integration
  })
})
```

### **Integration Testing**
```typescript
// End-to-end user workflows
// 1. Create project → Monitor progress → Approve HITL → Download artifacts
// 2. WebSocket connection recovery and reconnection
// 3. API error handling and user feedback
```

---

## Success Metrics

### **Functional Requirements**
- ✅ Real-time chat interface operational with backend WebSocket
- ✅ Project dashboard shows live agent status and task progress
- ✅ HITL approval interface handles all action types correctly
- ✅ Context artifacts display and download properly
- ✅ Real-time events update UI without page refresh

### **Technical Requirements**
- ✅ All 67 backend API endpoints properly integrated
- ✅ WebSocket connection stable with reconnection handling
- ✅ Type safety maintained throughout (no `any` types)
- ✅ Component tests achieve >80% coverage
- ✅ Performance: <200ms API response times, <100ms WebSocket latency

### **User Experience Requirements**
- ✅ Responsive design works on desktop (1440px), tablet (768px), mobile (375px)
- ✅ Error handling provides clear user feedback
- ✅ Loading states prevent user confusion
- ✅ Keyboard navigation for accessibility compliance

---

## Risk Mitigation

### **High Risk**
1. **WebSocket Integration Complexity**
   - **Mitigation**: Start with simple event handling, add complexity incrementally
   - **Fallback**: Polling-based updates if WebSocket proves unstable

2. **API Response Schema Changes**
   - **Mitigation**: Use TypeScript strict mode, comprehensive type checking
   - **Fallback**: Runtime validation with Zod schemas

### **Medium Risk**
1. **Component Integration Complexity**
   - **Mitigation**: Incremental component replacement, extensive testing
   - **Fallback**: Gradual migration allowing rollback to existing components

2. **Real-time Performance**
   - **Mitigation**: WebSocket connection pooling, event batching
   - **Fallback**: Reduce real-time update frequency if needed

---

## Timeline Estimate

**Total Duration**: 10 days
- **Phase 1** (Foundation): 2 days
- **Phase 2** (Backend Integration): 3 days
- **Phase 3** (Component Development): 3 days
- **Phase 4** (Real-time Integration): 2 days

**Resource Requirements**:
- 1 Frontend Developer (primary)
- 0.5 Backend Developer (integration support)
- 0.25 QA Engineer (testing support)

---

## Conclusion

The existing v0-botarmy-poc frontend provides an **exceptional foundation** with production-ready components, comprehensive UI library, and solid architecture patterns. The primary work involves:

1. **API Integration** (40% of effort) - Connecting to 67 backend endpoints
2. **New Component Development** (35% of effort) - 4 critical missing components
3. **WebSocket Event Mapping** (15% of effort) - Real-time backend integration
4. **Configuration & Testing** (10% of effort) - Setup and validation

This plan leverages the existing assets maximally while ensuring full Task 7 compliance and seamless backend integration. The modular approach allows for incremental development and testing, minimizing risk while delivering comprehensive functionality.

**Ready to proceed with implementation when authorized.** 🏗️