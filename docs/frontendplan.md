# BMAD Frontend Integration Plan

## Executive Summary

This plan details the integration of the BMAD frontend with the production-ready backend system. The backend provides 81 endpoints across 13 service groups with comprehensive HITL safety controls, real-time WebSocket communication, and enterprise-grade multi-agent orchestration.

## Current State Analysis

### Frontend Architecture Status

**✅ Strengths:**
- **Modern Stack**: Next.js 15.5.2 with App Router, React 19, TypeScript 5
- **UI Framework**: Complete shadcn/ui + Radix UI component system
- **State Management**: Zustand stores with persistence and error handling
- **WebSocket Foundation**: Basic WebSocket service implementation
- **Design System**: Comprehensive theme system with light/dark mode support

**⚠️ Gaps Identified:**

1. **API Integration Layer Missing**
   - No service layer for backend API communication
   - WebSocket service hardcoded to localhost:8000
   - No TypeScript types matching backend Pydantic models

2. **HITL Integration Incomplete**
   - HITL store exists but doesn't integrate with backend HITL safety endpoints
   - No approval workflow UI components
   - Missing budget control and emergency stop interfaces

3. **Real-time Event Handling Mismatch**
   - WebSocket service expects different message structure than backend provides
   - No handling of backend-specific event types (project-scoped, safety alerts)

4. **State Management Misalignment**
   - Frontend stores don't match backend data models
   - No integration with backend project lifecycle management
   - Missing artifact and audit trail integration

## Backend Integration Requirements

### API Endpoints to Integrate (81 Total)

**High Priority Endpoints:**
- **Projects** (6 endpoints): Core project lifecycle management
- **HITL Safety** (10 endpoints): Mandatory agent approval workflows
- **HITL Management** (12 endpoints): Human oversight interfaces
- **Agent Management** (4 endpoints): Real-time agent status
- **Health Monitoring** (5 endpoints): System status validation

**Medium Priority Endpoints:**
- **ADK Integration** (26 endpoints): Agent Development Kit functionality
- **Workflow Management** (17 endpoints): Workflow orchestration
- **Artifacts** (5 endpoints): Project deliverable generation

**Lower Priority Endpoints:**
- **Audit Trail** (4 endpoints): Event logging and compliance
- **WebSocket Events**: Real-time project-scoped broadcasting

### WebSocket Event Integration

**Backend Event Types:**
```typescript
// Project-scoped events: ws://localhost:8000/ws/{project_id}
interface BackendWebSocketEvents {
  agent_status: { agent_type: string; status: string; task: string }
  task_progress: { task_id: string; progress: number; phase: string }
  hitl_request: { request_id: string; type: string; priority: string }
  safety_alert: { type: 'budget_exceeded' | 'emergency_stop'; details: any }
  artifact_ready: { artifact_id: string; type: string; download_url: string }
}
```

## Architecture Design

### Service Layer Architecture

**API Service Layer (New)**
```typescript
// services/api/
├── client.ts              # Axios client with error handling
├── types.ts              # Backend Pydantic model types
├── projects.service.ts    # Project lifecycle operations
├── hitl.service.ts       # HITL approval workflows
├── agents.service.ts     # Agent status and management
├── artifacts.service.ts  # Artifact generation/download
└── health.service.ts     # System health monitoring
```

**Enhanced WebSocket Service**
```typescript
// lib/websocket/
├── websocket-client.ts     # Enhanced WebSocket client
├── event-handlers.ts      # Backend event type handlers
├── project-events.ts      # Project-scoped event management
└── safety-events.ts       # HITL safety event handlers
```

**State Management Enhancement**
```typescript
// lib/stores/
├── project-store.ts       # Project lifecycle state
├── hitl-store.ts         # Enhanced HITL workflow state
├── agent-store.ts        # Real-time agent status
├── artifact-store.ts     # Project artifacts
└── system-store.ts       # Health and system status
```

### Component Architecture

**Core Application Components**
```typescript
// components/core/
├── project-dashboard/     # Main project overview
├── hitl-approval/        # HITL approval interfaces
├── agent-monitor/        # Real-time agent status
├── safety-controls/      # Emergency stop and budget controls
└── artifact-manager/     # Project deliverable management
```

**Integration Components**
```typescript
// components/integration/
├── api-provider.tsx      # API client context provider
├── websocket-provider.tsx # Enhanced WebSocket provider
├── error-boundary.tsx    # Enhanced error handling
└── loading-states.tsx    # Consistent loading patterns
```

## Implementation Phases

### Phase 1: Foundation Integration (2-3 weeks)

**Sprint 1.1: API Service Layer (1 week)**
- Create TypeScript types from backend Pydantic models
- Implement API client with error handling and retry logic
- Build core service classes (projects, health, agents)
- Add comprehensive error boundary and loading states

**Sprint 1.2: WebSocket Enhancement (1 week)**
- Enhance WebSocket service for backend event types
- Implement project-scoped connection management
- Add safety event handling and emergency stop integration
- Create real-time event debugging and monitoring

**Sprint 1.3: State Management Alignment (1 week)**
- Refactor existing stores to match backend data models
- Implement project lifecycle state management
- Add real-time agent status synchronization
- Create artifact and audit trail state management

### Phase 2: Core Feature Integration (3-4 weeks)

**Sprint 2.1: Project Management UI (1 week)**
- Build project dashboard with real-time status
- Implement project creation and lifecycle management
- Add project status monitoring and phase tracking
- Integrate project completion workflows

**Sprint 2.2: HITL Approval System (1.5 weeks)**
- Create HITL approval interface components
- Implement agent execution approval workflows
- Build budget control and monitoring interfaces
- Add emergency stop and safety control UI

**Sprint 2.3: Agent Monitoring (1 week)**
- Build real-time agent status dashboard
- Implement agent performance monitoring
- Add agent handoff and task transition UI
- Create agent error handling and recovery interfaces

**Sprint 2.4: Artifact Management (0.5 weeks)**
- Implement artifact generation and download UI
- Build ZIP package creation and management
- Add artifact preview and validation interfaces

### Phase 3: Advanced Features (2-3 weeks)

**Sprint 3.1: Workflow Orchestration (1.5 weeks)**
- Build workflow execution monitoring
- Implement BMAD Core template integration
- Add workflow state visualization
- Create workflow error recovery interfaces

**Sprint 3.2: System Administration (1 week)**
- Build system health monitoring dashboard
- Implement audit trail and compliance interfaces
- Add system configuration and feature flag management
- Create performance monitoring and analytics

**Sprint 3.3: Testing and Optimization (0.5 weeks)**
- Comprehensive integration testing
- Performance optimization and caching
- Error handling and edge case validation
- Security validation and penetration testing

## Critical Implementation Details

### API Client Configuration

**Base Configuration**
```typescript
// services/api/client.ts
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 500) {
      // Handle backend errors gracefully
      console.error('Backend error:', error.response.data);
    }
    return Promise.reject(error);
  }
);
```

**Environment Configuration**
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_ENVIRONMENT=development
```

### WebSocket Integration

**Enhanced WebSocket Client**
```typescript
// lib/websocket/websocket-client.ts
class EnhancedWebSocketClient {
  private projectId?: string;

  connect(projectId?: string) {
    const wsUrl = projectId
      ? `${WS_BASE_URL}/${projectId}`
      : WS_BASE_URL;

    this.ws = new WebSocket(wsUrl);
    this.setupEventHandlers();
  }

  private handleBackendEvent(event: BackendWebSocketEvent) {
    switch (event.type) {
      case 'agent_status':
        agentStore.updateStatus(event.data);
        break;
      case 'hitl_request':
        hitlStore.addRequest(event.data);
        break;
      case 'safety_alert':
        systemStore.triggerSafetyAlert(event.data);
        break;
    }
  }
}
```

### Type Safety Implementation

**Backend Model Types**
```typescript
// services/api/types.ts
export interface Project {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'completed' | 'paused' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface HITLRequest {
  id: string;
  project_id: string;
  task_id: string;
  agent_type: string;
  request_type: 'PRE_EXECUTION' | 'RESPONSE_APPROVAL';
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  estimated_tokens: number;
  estimated_cost: number;
  expires_at: string;
}

export interface AgentStatus {
  agent_type: string;
  status: 'idle' | 'working' | 'waiting' | 'error';
  current_task?: string;
  performance_metrics?: {
    tasks_completed: number;
    avg_response_time: number;
    success_rate: number;
  };
}
```

### Error Handling Strategy

**API Error Handling**
```typescript
// services/api/error-handler.ts
export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export const handleAPIError = (error: any): APIError => {
  if (error.response) {
    return new APIError(
      error.response.status,
      error.response.data?.message || 'API Error',
      error.response.data
    );
  }
  return new APIError(0, 'Network Error', error);
};
```

**React Error Boundary Enhancement**
```typescript
// components/integration/api-error-boundary.tsx
export class APIErrorBoundary extends Component {
  handleAPIError = (error: APIError) => {
    switch (error.status) {
      case 500:
        // Backend error - show retry option
        break;
      case 429:
        // Rate limit - show wait message
        break;
      case 503:
        // Service unavailable - show maintenance message
        break;
    }
  };
}
```

## Testing Strategy

### Unit Testing Requirements

**Component Testing**
```typescript
// __tests__/components/hitl-approval.test.tsx
describe('HITL Approval Component', () => {
  it('should display pending approval requests', async () => {
    const mockRequests = createMockHITLRequests();
    render(<HITLApproval requests={mockRequests} />);

    expect(screen.getByText('Pending Approvals')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /approve/i })).toHaveLength(2);
  });

  it('should handle approval submission', async () => {
    const mockApprove = jest.fn();
    const user = userEvent.setup();

    render(<HITLApproval onApprove={mockApprove} />);

    await user.click(screen.getByRole('button', { name: /approve/i }));
    expect(mockApprove).toHaveBeenCalledWith(expect.any(String));
  });
});
```

**API Service Testing**
```typescript
// __tests__/services/projects.service.test.ts
describe('Projects Service', () => {
  beforeEach(() => {
    nock('http://localhost:8000')
      .get('/api/v1/projects')
      .reply(200, mockProjectsResponse);
  });

  it('should fetch projects successfully', async () => {
    const projects = await projectsService.getProjects();
    expect(projects).toHaveLength(3);
    expect(projects[0]).toMatchObject({
      id: expect.any(String),
      name: expect.any(String),
      status: expect.any(String),
    });
  });
});
```

### Integration Testing Requirements

**WebSocket Integration Tests**
```typescript
// __tests__/integration/websocket.test.ts
describe('WebSocket Integration', () => {
  let mockServer: WS;

  beforeEach(() => {
    mockServer = new WS('ws://localhost:8000/ws/test-project');
  });

  it('should handle agent status updates', async () => {
    const { result } = renderHook(() => useAgentStore());

    act(() => {
      mockServer.send(JSON.stringify({
        type: 'agent_status',
        data: { agent_type: 'analyst', status: 'working' }
      }));
    });

    await waitFor(() => {
      expect(result.current.agents.analyst.status).toBe('working');
    });
  });
});
```

**End-to-End Testing**
```typescript
// __tests__/e2e/project-lifecycle.test.ts
describe('Project Lifecycle E2E', () => {
  it('should complete full project workflow', async () => {
    // 1. Create project
    await page.goto('/projects');
    await page.click('[data-testid="create-project"]');
    await page.fill('[data-testid="project-name"]', 'Test Project');
    await page.click('[data-testid="submit"]');

    // 2. Monitor agent status
    await expect(page.locator('[data-testid="agent-status"]')).toBeVisible();

    // 3. Handle HITL approval
    await expect(page.locator('[data-testid="hitl-request"]')).toBeVisible();
    await page.click('[data-testid="approve-button"]');

    // 4. Verify project completion
    await expect(page.locator('[data-testid="project-status"]')).toHaveText('completed');
  });
});
```

### Performance Testing

**Load Testing Requirements**
```typescript
// __tests__/performance/websocket-load.test.ts
describe('WebSocket Performance', () => {
  it('should handle 100 concurrent connections', async () => {
    const connections = Array(100).fill(null).map(() =>
      new WebSocket('ws://localhost:8000/ws/test-project')
    );

    await Promise.all(connections.map(ws =>
      new Promise(resolve => ws.onopen = resolve)
    ));

    // Verify all connections are stable
    expect(connections.every(ws => ws.readyState === WebSocket.OPEN)).toBe(true);
  });
});
```

## Security Considerations

### Authentication Integration
- Implement JWT token management for API requests
- Add secure storage for authentication tokens
- Handle token refresh and expiration gracefully

### Input Validation
- Validate all form inputs against backend schema
- Sanitize user inputs before API submission
- Implement CSP headers for XSS protection

### Error Information Exposure
- Never expose sensitive backend error details to users
- Log detailed errors for debugging without showing to UI
- Implement rate limiting on frontend API calls

## Performance Optimization

### Caching Strategy
```typescript
// lib/cache/api-cache.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        if (error.status === 404) return false;
        return failureCount < 3;
      },
    },
  },
});
```

### WebSocket Optimization
- Implement message batching for high-frequency updates
- Add connection pooling for multiple project monitoring
- Use WebSocket heartbeat for connection health monitoring

### Bundle Optimization
- Implement code splitting for admin interfaces
- Lazy load heavy components (charts, file uploaders)
- Optimize asset loading and caching strategies

## Migration Path

### Existing Code Preservation
1. **Maintain existing stores** during transition period
2. **Gradual component migration** from mock to real data
3. **Feature flag integration** for backend vs. mock modes
4. **Backward compatibility** for development workflows

### Development Workflow
1. **Environment configuration** for local backend integration
2. **Mock mode fallback** when backend is unavailable
3. **Development tools** for API debugging and monitoring
4. **Hot reload compatibility** with backend changes

## Success Metrics

### Technical Metrics
- **API Response Times**: <200ms for all status queries
- **WebSocket Latency**: <100ms for real-time events
- **Error Rate**: <1% for API calls under normal load
- **Test Coverage**: >85% for integration code

### User Experience Metrics
- **Page Load Time**: <2 seconds for all interfaces
- **Real-time Update Latency**: <500ms for status changes
- **HITL Approval Time**: <30 seconds for simple approvals
- **System Availability**: >99.5% uptime during business hours

## Conclusion

This integration plan provides a comprehensive roadmap for connecting the BMAD frontend with the production-ready backend system. The phased approach ensures gradual integration while maintaining development velocity and system stability.

The plan emphasizes type safety, error handling, and real-time communication to create a robust user experience that matches the enterprise-grade capabilities of the backend system.