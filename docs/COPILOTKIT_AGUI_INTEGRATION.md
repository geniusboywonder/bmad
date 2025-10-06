# CopilotKit + AG-UI Integration Guide

## Overview

BMAD now integrates CopilotKit with Google ADK agents via the AG-UI protocol, enabling:
- **Real-time shared state** between backend ADK agents and frontend React components
- **Generative UI** for dynamic agent progress visualization
- **Bidirectional communication** via AG-UI GraphQL protocol
- **Enterprise controls** maintained through BMAD's HITL safety system

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│                                                              │
│  ┌──────────────────┐    ┌─────────────────────────────┐   │
│  │  CopilotKit      │    │   Generative UI Components  │   │
│  │  - CopilotSidebar│    │   - AgentProgressCard       │   │
│  │  - useCoAgent    │◄───┤   - MultiAgentDashboard     │   │
│  └────────┬─────────┘    └─────────────────────────────┘   │
│           │                                                  │
└───────────┼──────────────────────────────────────────────────┘
            │ AG-UI Protocol (GraphQL)
            │ /api/copilotkit/analyst
            │ /api/copilotkit/architect
            │ /api/copilotkit/coder
            │
┌───────────▼──────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│                                                              │
│  ┌──────────────────┐    ┌─────────────────────────────┐   │
│  │  ag_ui_adk       │    │   Google ADK Agents         │   │
│  │  - ADKAgent      │◄───┤   - LlmAgent (analyst)      │   │
│  │  - EventTranslator│    │   - LlmAgent (architect)    │   │
│  └──────────────────┘    │   - LlmAgent (coder)        │   │
│                          └─────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  BMAD Enterprise Controls                            │  │
│  │  - HITLSafetyService (maintained)                    │  │
│  │  - BMADADKWrapper (optional enhancement)             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Backend Setup

### 1. Dependencies Installed

```bash
# Backend packages (already installed)
ag_ui_adk==0.3.1
ag-ui-protocol==0.1.7
google-adk==1.15.1
google-genai==1.40.0
```

### 2. AG-UI Runtime Created

**File:** `backend/app/copilot/adk_runtime.py`

```python
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents import LlmAgent

class BMADAGUIRuntime:
    """AG-UI Runtime for BMAD ADK agents."""

    async def create_analyst_agent(self) -> ADKAgent:
        analyst = LlmAgent(
            name="analyst",
            model=settings.llm_provider_model,
            instruction="Requirements analyst with shared state tracking"
        )

        return ADKAgent(
            adk_agent=analyst,
            app_name="bmad_analyst",
            session_timeout_seconds=3600
        )

    async def setup_fastapi_endpoints(self, app: FastAPI):
        # Register AG-UI protocol endpoints
        add_adk_fastapi_endpoint(app, analyst, path="/api/copilotkit/analyst")
        # ... more agents
```

### 3. FastAPI Integration

**File:** `backend/app/main.py`

```python
from app.copilot.adk_runtime import bmad_agui_runtime

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... startup cleanup ...

    # Register AG-UI endpoints
    await bmad_agui_runtime.setup_fastapi_endpoints(app)
    logger.info("✅ AG-UI protocol endpoints registered")

    yield
```

**Available Endpoints:**
- `POST /api/copilotkit/analyst` - Requirements analysis agent
- `POST /api/copilotkit/architect` - Technical architecture agent
- `POST /api/copilotkit/coder` - Software development agent

## Frontend Setup

### 1. CopilotKit Packages (Already Installed)

```json
{
  "@copilotkit/react-core": "^1.10.3",
  "@copilotkit/react-ui": "^1.10.3",
  "@copilotkit/runtime": "^1.10.3"
}
```

### 2. Shared State with `useCoAgent`

**File:** `frontend/components/copilot/agent-progress-ui.tsx`

```typescript
import { useCoAgent } from "@copilotkit/react-core";

interface AgentState {
  agent_name: string;
  tasks: AgentTask[];
  overall_progress: number;
  status: "idle" | "working" | "completed";
}

function AgentProgressCard({ agentName }: { agentName: string }) {
  // Bidirectional shared state with backend ADK agent
  const { state, setState } = useCoAgent<AgentState>({
    name: agentName,
    initialState: {
      agent_name: agentName,
      tasks: [],
      overall_progress: 0,
      status: "idle"
    }
  });

  return (
    <Card>
      <Progress value={state.overall_progress} />
      {/* Real-time updates from backend agent */}
    </Card>
  );
}
```

### 3. CopilotKit Provider Setup

**File:** `frontend/app/copilot-demo/page.tsx`

```typescript
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";

export default function Page() {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit/analyst"
      agent="analyst"
    >
      <MultiAgentDashboard />
      <CopilotSidebar />
    </CopilotKit>
  );
}
```

## Generative UI for Agent Progress

### Progress Tracking Components

```typescript
interface AgentTask {
  id: string;
  description: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  progress: number;
}

// Backend ADK agent updates state
agent_state.tasks.append({
  "id": "task_001",
  "description": "Analyzing requirements",
  "status": "in_progress",
  "progress": 45
})

// Frontend automatically re-renders with new state
```

### Multi-Agent Dashboard

Shows all agents' progress in real-time:
```typescript
function MultiAgentDashboard() {
  const agents = ["analyst", "architect", "coder"];

  return (
    <div className="grid grid-cols-3 gap-4">
      {agents.map(agent => (
        <AgentProgressCard key={agent} agentName={agent} />
      ))}
    </div>
  );
}
```

## Benefits of AG-UI Integration

### 1. **Simplified Architecture**
- ✅ No custom WebSocket management needed
- ✅ AG-UI protocol handles all communication
- ✅ Standardized agent-UI interaction

### 2. **Real-time Shared State**
- ✅ Backend agents update state → Frontend auto-renders
- ✅ Bidirectional: Frontend can update agent state
- ✅ Type-safe with TypeScript interfaces

### 3. **Generative UI**
- ✅ Dynamic component rendering based on agent state
- ✅ Custom progress visualizations
- ✅ Tool-based UI (render agent tool calls as UI)

### 4. **Enterprise Controls Maintained**
- ✅ HITL safety controls still apply
- ✅ Agent budget management preserved
- ✅ Audit trail and logging continue

## Migration from Current System

### Current BMAD Setup
- Custom WebSocket manager for real-time updates
- Manual state synchronization
- Agent status broadcasting via WebSocket events

### Enhanced with AG-UI
- **Keep existing:** WebSocket for system events (agent status, errors)
- **Add AG-UI for:** Agent-specific communication and shared state
- **Result:** Best of both worlds - system events + agent collaboration

### Hybrid Approach (Recommended)

```
System Events (WebSocket)          Agent Collaboration (AG-UI)
├── Agent status changes           ├── Agent task progress
├── HITL approval requests         ├── Shared state updates
├── Error broadcasts               ├── Generative UI rendering
└── Health monitoring              └── Tool-based interactions
```

## Next Steps

### Phase 1: Backend (Completed ✅)
- [x] Install ag_ui_adk dependencies
- [x] Create BMAD AG-UI Runtime
- [x] Register FastAPI endpoints

### Phase 2: Frontend ✅ **COMPLETE - October 2025**
- [x] Create AgentProgressCard component
- [x] Implement useCoAgent shared state
- [x] Integrate with existing chat UI
- [x] End-to-end testing with successful agent response

**Completion Evidence:**
- ✅ Demo page: `frontend/app/copilot-demo/page.tsx`
- ✅ Agent progress: `frontend/components/copilot/agent-progress-ui.tsx`
- ✅ API proxy: `frontend/app/api/copilotkit/[agent]/route.ts`
- ✅ Test message: "Can you help me analyze requirements for a simple TODO app?"
- ✅ Agent response: Comprehensive 7-category requirements analysis
- ✅ Network: POST /api/copilotkit → 200 OK in 11.7s
- ✅ Screenshot: `phase2-complete-agent-response-success.png`

### Phase 3: Dynamic Agent Switching ✅ **COMPLETE - October 2025**
- [x] Custom markdown tag renderer for HITL requests in CopilotSidebar
- [x] InlineHITLApproval component integration via custom tags
- [x] HITL store connection with custom markdown renderer
- [x] Dynamic agent selection (6 agents: analyst, architect, coder, tester, deployer, orchestrator)
- [x] Agent-specific runtime with dynamic prompts from markdown files
- [x] Fixed agent switching bugs (runtime mutation, path resolution)
- [x] Per-agent thread management with separate conversation history
- [x] Agent persona loading from backend markdown files

**Implementation Approach:**

**Frontend Custom Markdown Tag Renderer** (`frontend/app/copilot-demo/page.tsx`):
```typescript
const customMarkdownTagRenderers: ComponentsMap<{ "hitl-approval": { requestId: string } }> = {
  "hitl-approval": ({ requestId }) => {
    const request = requests.find(req => req.id === requestId);
    if (!request) return null;

    return <InlineHITLApproval request={request} className="my-3" />;
  }
};
```

**Agent Dynamic Runtime Configuration** (`frontend/components/client-provider.tsx`):
```typescript
function CopilotKitWrapper({ children }: { children: React.ReactNode }) {
  const { selectedAgent } = useAgent();

  // Each agent gets its own thread ID to maintain separate conversation history
  const threadId = useMemo(() => `agent-${selectedAgent}-thread`, [selectedAgent]);

  return (
    <CopilotKit
      key={threadId} // Force remount when thread changes to show only that agent's messages
      publicApiKey={process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY}
      runtimeUrl="/api/copilotkit"
      agent={selectedAgent}
      threadId={threadId}
    >
      {children}
    </CopilotKit>
  );
}
```

**Backend Runtime with Fresh Instance per Request** (`frontend/app/api/copilotkit/route.ts`):
```typescript
// Create agents factory to get fresh instances
function createAgents() {
  return {
    analyst: new HttpAgent({ url: `${BACKEND_BASE_URL}/api/copilotkit/analyst` }),
    architect: new HttpAgent({ url: `${BACKEND_BASE_URL}/api/copilotkit/architect` }),
    coder: new HttpAgent({ url: `${BACKEND_BASE_URL}/api/copilotkit/coder` }),
    orchestrator: new HttpAgent({ url: `${BACKEND_BASE_URL}/api/copilotkit/orchestrator` }),
    tester: new HttpAgent({ url: `${BACKEND_BASE_URL}/api/copilotkit/tester` }),
    deployer: new HttpAgent({ url: `${BACKEND_BASE_URL}/api/copilotkit/deployer` }),
  };
}

export const POST = async (req: NextRequest) => {
  // Create fresh runtime for each request to prevent agent list mutation
  const agents = createAgents();
  const runtime = new CopilotRuntime({ agents });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
```

**Agent Persona Loader Path Fix** (`backend/app/utils/agent_prompt_loader.py`):
```python
def __init__(self, agents_dir: str = None):
    if agents_dir is None:
        cwd = os.getcwd()

        # Check if we're already in backend directory
        if os.path.exists("app/agents"):
            agents_dir = "app/agents"  # Running from backend dir
        elif os.path.exists("backend/app/agents"):
            agents_dir = "backend/app/agents"  # Running from project root
        else:
            # Fallback to relative path from this file's location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            agents_dir = os.path.join(os.path.dirname(current_dir), "agents")
```

**Backend ADK Agent HITL Emission** (TODO):
When ADK agents need HITL approval, they should include the custom markdown tag in their response:
```python
# In backend/app/copilot/adk_runtime.py or agent logic
response = f"""I need to perform this task.

<hitl-approval requestId="{approval_id}">Execute task: {task_description}</hitl-approval>

I'll wait for your approval before proceeding.
"""
```

**Benefits:**
- ✅ No hardcoded agent names or prompts in frontend
- ✅ All 6 agents use dynamic prompts from `backend/app/agents/*.md`
- ✅ Agent switching works seamlessly with thread-based remounting
- ✅ HITL approval UI renders inline in chat messages
- ✅ InlineHITLApproval component shows approve/reject/modify buttons
- ✅ Separate conversation history per agent (via unique threadId)
- ✅ Fixed runtime mutation bug (fresh CopilotRuntime per request)
- ✅ Agent personas loaded correctly (Mary for analyst, James for coder, etc.)

**Known Limitations:**
- ⚠️ **Thread history not preserved in UI**: When switching agents, the chat UI resets and doesn't reload previous conversation history. This is a CopilotKit limitation - the thread history IS stored server-side, but the UI doesn't automatically reload it on remount.
  - **Workaround**: History is maintained in the backend and will be available via API queries if needed
  - **Future solution**: Build custom chat UI that queries and displays thread history per agent

### Phase 4: HITL Integration ✅ **COMPLETE - October 2025**
- [x] Backend mechanism for agents to emit HITL markdown tags
- [x] Custom markdown tag renderer for inline approval UI
- [x] Automatic HITL request creation when tags detected
- [x] InlineHITLApproval component integration in CopilotKit chat
- [x] Approve/reject/modify buttons with backend API connection

**Implementation Details:**

**Backend ADK HITL Instructions** (`backend/app/copilot/adk_runtime.py`):
```python
hitl_instructions = """

CRITICAL HITL INTEGRATION INSTRUCTIONS:
When you need human approval for any significant action (creating artifacts, making important decisions, executing code, deploying, etc.), you MUST include a custom markdown tag in your response:

<hitl-approval requestId="unique-id-{timestamp}">Brief description of what you want to do</hitl-approval>

This will render an inline approval component with approve/reject/modify buttons in the chat interface.
Always wait for approval before proceeding with the actual work."""

analyst = LlmAgent(
    name="analyst",
    model=LiteLlm(model=settings.analyst_agent_model),
    instruction=agent_prompt_loader.get_agent_prompt("analyst") + hitl_instructions
)
```

**Frontend Custom Markdown Tag Renderer** (`frontend/app/copilot-demo/page.tsx`):
```typescript
const customMarkdownTagRenderers: ComponentsMap<{ "hitl-approval": { requestId: string, children?: React.ReactNode } }> = {
  "hitl-approval": ({ requestId, children }) => {
    const { addRequest } = useHITLStore();

    // Find existing request by approvalId
    let request = requests.find(req => req.context?.approvalId === requestId);

    if (!request) {
      // Create HITL request from markdown tag
      const description = typeof children === 'string' ? children : 'Agent task requires approval';

      addRequest({
        agentName: selectedAgent,
        decision: description,
        context: {
          approvalId: requestId,  // For duplicate detection
          source: 'copilotkit',
          agentType: selectedAgent,
          requestData: { instructions: description }
        },
        priority: 'medium'
      });

      request = requests.find(req => req.context?.approvalId === requestId);
    }

    if (!request) return null;

    return <InlineHITLApproval request={request as any} className="my-3" />;
  }
};
```

**InlineHITLApproval Component** (`frontend/components/hitl/inline-hitl-approval.tsx`):
- Approve/Reject/Modify buttons with visual feedback
- Priority-based styling (low/medium/high/urgent)
- Agent badge integration with centralized styling
- Expandable response textarea for modifications
- Real-time status updates (pending → approved/rejected/modified)
- Integration with HITLStore for state management

**Benefits:**
- ✅ **Inline Approval UI**: HITL requests render directly in chat messages
- ✅ **No Context Switch**: Users stay in chat window to approve/reject
- ✅ **Agent-Driven Requests**: Agents decide when to request approval
- ✅ **Unified Experience**: Same approval UI across all 6 agents
- ✅ **Backend Integration**: Approval actions connect to existing HITL API
- ✅ **Duplicate Prevention**: approvalId prevents duplicate HITL messages

**Known Limitations:**
- ⚠️ **Real-time Updates**: WebSocket integration for approval status updates pending
- ⚠️ **Backend HITL API**: Approval actions call HITLStore but backend API integration needs testing

**Next Steps (Phase 5):**
- [ ] WebSocket real-time approval status updates
- [ ] Backend HITL API integration testing
- [ ] End-to-end workflow: agent request → approval → task execution

### Phase 5: Enhanced Features (Future)
- [ ] Custom chat UI with thread history loading
- [ ] Tool-based Generative UI for artifacts
- [ ] Multi-agent coordination dashboard
- [ ] Workflow visualization with shared state

## Testing

### Backend AG-UI Endpoints
```bash
# Test analyst agent endpoint
curl -X POST http://localhost:8000/api/copilotkit/analyst \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze requirements for a web app"}'
```

### Frontend Integration
```bash
cd frontend
npm run dev

# Visit http://localhost:3000/copilot-demo
```

## Resources

- [CopilotKit Docs](https://docs.copilotkit.ai)
- [AG-UI Protocol](https://docs.copilotkit.ai/adk)
- [Google ADK](https://google.github.io/adk-docs/)
- [CopilotKit + ADK Blog](https://www.copilotkit.ai/blog/build-a-frontend-for-your-adk-agents-with-ag-ui)

## Key Files Created

**Backend:**
- `backend/app/copilot/adk_runtime.py` - AG-UI runtime with ADK agents
- `backend/app/main.py` - FastAPI with AG-UI endpoints

**Frontend:**
- `frontend/components/copilot/agent-progress-ui.tsx` - Generative UI components
- `frontend/app/copilot-demo/page.tsx` - Demo integration page

**Documentation:**
- `docs/COPILOTKIT_AGUI_INTEGRATION.md` - This guide
