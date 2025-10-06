/**
 * CopilotKit + AG-UI Integration Demo
 *
 * Shows how to connect CopilotKit frontend to AG-UI ADK backend
 * with BMAD HITL integration and agent progress tracking
 *
 * This page uses the global CopilotKit provider to avoid conflicts.
 */

"use client";

import dynamic from "next/dynamic";
import { useState, useEffect } from "react";
import { useHITLStore } from "@/lib/stores/hitl-store";
import { useAgent } from "@/lib/context/agent-context";
import { ComponentsMap } from "@copilotkit/react-ui";
import { HITLAlertsBar } from "@/components/hitl/hitl-alerts-bar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Settings, AlertTriangle, ToggleLeft, ToggleRight } from "lucide-react";
import "@copilotkit/react-ui/styles.css";

// Dynamically import CopilotSidebar and AgentProgressCard
const CopilotSidebar = dynamic(
  () => import("@copilotkit/react-ui").then((mod) => ({ default: mod.CopilotSidebar })),
  {
    ssr: false,
    loading: () => <div className="fixed right-4 bottom-4 w-12 h-12 bg-primary rounded-full animate-pulse" />
  }
);

const AgentProgressCard = dynamic(
  () => import("@/components/copilot/agent-progress-ui").then((mod) => ({ default: mod.AgentProgressCard })),
  { ssr: false }
);

const InlineHITLApproval = dynamic(
  () => import("@/components/hitl/inline-hitl-approval").then((mod) => ({ default: mod.InlineHITLApproval })),
  { ssr: false }
);

export default function CopilotDemoPage() {
  const [isClient, setIsClient] = useState(false);
  const { selectedAgent, setSelectedAgent } = useAgent();
  const { requests, addRequest } = useHITLStore();
  
  // HITL Configuration State
  const [hitlEnabled, setHitlEnabled] = useState(true);
  const [hitlCounter, setHitlCounter] = useState(10);
  const [currentCounter, setCurrentCounter] = useState(10);
  const [systemAlerts, setSystemAlerts] = useState<Array<{id: string, message: string, stage?: string}>>([]);
  const [expandedAlerts, setExpandedAlerts] = useState<string[]>([]);
  const [messageCount, setMessageCount] = useState(0);

  // Available agents (dynamically loaded from backend/app/agents/*.md)
  const availableAgents = [
    { name: "analyst", label: "Analyst", description: "Requirements analysis and documentation" },
    { name: "architect", label: "Architect", description: "System architecture and design" },
    { name: "coder", label: "Coder", description: "Code implementation" },
    { name: "tester", label: "Tester", description: "Quality assurance and testing" },
    { name: "deployer", label: "Deployer", description: "Deployment and DevOps" },
    { name: "orchestrator", label: "Orchestrator", description: "Workflow coordination" }
  ];

  useEffect(() => {
    setIsClient(true);
  }, []);

  // HITL threshold management
  const triggerHITLRequest = (reason: string = "HITL threshold reached") => {
    const requestId = `hitl-${Date.now()}-${Math.random()}`;
    addRequest({
      agentName: selectedAgent,
      decision: `${reason}. Agent: ${selectedAgent}`,
      context: {
        approvalId: requestId,
        source: 'threshold',
        agentType: selectedAgent,
        requestData: {
          instructions: `${selectedAgent} agent needs approval: ${reason}`
        }
      },
      priority: 'medium'
    });
    
    // Add system alert
    setSystemAlerts(prev => [...prev, {
      id: `alert-${Date.now()}`,
      message: `HITL approval required for ${selectedAgent} agent`,
      stage: selectedAgent
    }]);
  };

  // Handle message sending with HITL counter
  const handleMessageSend = () => {
    setMessageCount(prev => prev + 1);
    
    if (hitlEnabled && currentCounter > 0) {
      setCurrentCounter(prev => prev - 1);
    } else if (hitlEnabled && currentCounter <= 0) {
      triggerHITLRequest("HITL counter reached zero");
      setCurrentCounter(hitlCounter); // Reset counter
    }
  };

  // HITL Controls
  const resetCounter = () => {
    setCurrentCounter(hitlCounter);
  };

  const toggleHITL = () => {
    setHitlEnabled(!hitlEnabled);
    if (!hitlEnabled) {
      setCurrentCounter(hitlCounter); // Reset counter when enabling
    }
  };

  const updateCounterLimit = (newLimit: number) => {
    setHitlCounter(newLimit);
    setCurrentCounter(newLimit);
  };

  // Alert management
  const toggleExpanded = (id: string) => {
    setExpandedAlerts(prev => 
      prev.includes(id) 
        ? prev.filter(alertId => alertId !== id)
        : [...prev, id]
    );
  };

  const dismissAlert = (id: string) => {
    setSystemAlerts(prev => prev.filter(alert => alert.id !== id));
    setExpandedAlerts(prev => prev.filter(alertId => alertId !== id));
  };

  // Custom markdown tag renderer for HITL approvals
  const customMarkdownTagRenderers: ComponentsMap<{ "hitl-approval": { requestId: string, children?: React.ReactNode } }> = {
    "hitl-approval": ({ requestId, children }) => {
      // Find existing request by looking for matching approvalId in context
      let request = requests.find(req => req.context?.approvalId === requestId);

      if (!request) {
        // Create HITL request from markdown tag
        const description = typeof children === 'string' ? children : 'Agent task requires approval';

        addRequest({
          agentName: selectedAgent,
          decision: description,
          context: {
            approvalId: requestId,  // Use requestId as approvalId for duplicate detection
            source: 'copilotkit',
            agentType: selectedAgent,
            requestData: {
              instructions: description
            }
          },
          priority: 'medium'
        });

        // Get the newly created request
        request = requests.find(req => req.context?.approvalId === requestId);
        
        // Trigger message send handler for counter management
        handleMessageSend();
      }

      if (!request) return null;

      return (
        <InlineHITLApproval
          request={request as any}
          className="my-3"
        />
      );
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* HITL Alerts Bar */}
      <HITLAlertsBar
        systemAlerts={systemAlerts}
        expandedAlerts={expandedAlerts}
        toggleExpanded={toggleExpanded}
        dismissAlert={dismissAlert}
        isClient={isClient}
      />
      
      <div className="container mx-auto p-6 flex-1">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">
            BMAD AI Agent Dashboard
          </h1>
          <p className="text-muted-foreground">
            Real-time agent progress with CopilotKit + AG-UI protocol and HITL controls
          </p>

          {/* Agent Selector */}
          {isClient && (
            <div className="mt-4">
              <label className="text-sm font-medium mb-2 block">Select Agent:</label>
              <div className="flex gap-2 flex-wrap">
                {availableAgents.map((agent) => (
                  <button
                    key={agent.name}
                    onClick={() => setSelectedAgent(agent.name)}
                    className={`px-3 py-2 rounded-lg text-sm transition-all ${
                      selectedAgent === agent.name
                        ? 'bg-primary text-primary-foreground shadow-md'
                        : 'bg-muted hover:bg-muted/80'
                    }`}
                    title={agent.description}
                  >
                    {agent.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* HITL Controls */}
          {isClient && (
            <div className="mt-4 p-4 border rounded-lg bg-muted/30" data-testid="hitl-controls">
              <div className="flex items-center gap-4 mb-3">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  HITL Controls
                </h3>
                <Badge variant={hitlEnabled ? "default" : "secondary"}>
                  {hitlEnabled ? "Enabled" : "Disabled"}
                </Badge>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* HITL Toggle */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">HITL Status</label>
                  <Button
                    onClick={toggleHITL}
                    variant={hitlEnabled ? "default" : "outline"}
                    className="w-full justify-start"
                  >
                    {hitlEnabled ? <ToggleRight className="w-4 h-4 mr-2" /> : <ToggleLeft className="w-4 h-4 mr-2" />}
                    {hitlEnabled ? "Enabled" : "Disabled"}
                  </Button>
                </div>

                {/* Counter Settings */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Counter Limit</label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      value={hitlCounter}
                      onChange={(e) => updateCounterLimit(parseInt(e.target.value) || 10)}
                      min="1"
                      max="100"
                      className="flex-1"
                    />
                    <Button onClick={resetCounter} variant="outline" size="sm">
                      Reset
                    </Button>
                  </div>
                </div>

                {/* Current Status */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Current Status</label>
                  <div className="flex items-center gap-2">
                    <Badge variant={currentCounter > 0 ? "default" : "destructive"}>
                      {currentCounter} actions left
                    </Badge>
                    <Badge variant="outline">
                      {messageCount} messages sent
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Test Buttons */}
              <div className="mt-4 pt-3 border-t">
                <label className="text-sm font-medium mb-2 block">Test HITL Features:</label>
                <div className="flex gap-2 flex-wrap">
                  <Button
                    onClick={() => triggerHITLRequest("Manual test request")}
                    variant="outline"
                    size="sm"
                  >
                    <AlertTriangle className="w-4 h-4 mr-1" />
                    Trigger HITL Request
                  </Button>
                  <Button
                    onClick={() => setCurrentCounter(0)}
                    variant="outline"
                    size="sm"
                  >
                    Force Counter to Zero
                  </Button>
                  <Button
                    onClick={() => {
                      setMessageCount(0);
                      setCurrentCounter(hitlCounter);
                    }}
                    variant="outline"
                    size="sm"
                  >
                    Reset All Counters
                  </Button>
                </div>
              </div>
            </div>
          )}
      </div>

          <div className="mt-6 p-4 border rounded-lg bg-muted/50">
            <h2 className="text-xl font-semibold mb-2">AG-UI Integration Status</h2>
            <ul className="space-y-2 text-sm">
              <li>✅ CopilotKit Provider: Using global configuration</li>
              <li>✅ Runtime URL: /api/copilotkit (CopilotRuntime with HttpAgent for all 6 agents)</li>
              <li>✅ Selected Agent: {selectedAgent} (Dynamic prompts from backend/app/agents/{selectedAgent}.md)</li>
              <li>✅ LLM: OpenAI GPT-4 Turbo via LiteLLM</li>
              <li>✅ Public API Key: {process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY ? `Configured (${process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY.substring(0, 10)}...)` : "Missing"}</li>
              <li>{isClient ? "✅" : "⏳"} Client hydration: {isClient ? "Complete" : "Loading..."}</li>
              <li>✅ Phase 3: HITL approval rendering with custom markdown tags</li>
              <li>✅ Agent switching: Dynamic agent context enables real-time switching</li>
              <li>✅ HITL Integration: Counter-based approval system with alerts bar</li>
              <li>✅ HITL Status: {hitlEnabled ? `Enabled (${currentCounter}/${hitlCounter} actions left)` : "Disabled"}</li>
            </ul>

            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm">
              <strong>🔄 How it works:</strong><br/>
              CopilotKit Frontend → /api/copilotkit (CopilotRuntime + @ag-ui/client HttpAgent) → Backend AG-UI ADK (dynamic prompts) + LiteLLM → OpenAI GPT-4 Turbo
              <br/><br/>
              <strong>🛡️ HITL Flow:</strong><br/>
              Message Counter → HITL Threshold → Alert Bar → Navigate to Chat → Approve/Reject → Continue
            </div>
          </div>

          {/* Agent Progress Card - Shows task tracking */}
          {isClient && (
            <div className="mt-6 p-4 border rounded-lg">
              <AgentProgressCard agentName={selectedAgent} />
            </div>
          )}

          {/* CopilotKit Sidebar - Main chat interface */}
          {/* Note: Uses global CopilotKit provider from client-provider.tsx */}
          {/* Agent switching requires page navigation to /copilot-demo?agent=<name> */}
          {isClient && (
            <div data-testid="chat-section">
              <CopilotSidebar
                labels={{
                  title: `BMAD ${selectedAgent.charAt(0).toUpperCase() + selectedAgent.slice(1)} Agent`,
                  initial: `I'm your ${selectedAgent} agent. How can I help you today?`
                }}
                instructions={`You are the BMAD ${selectedAgent} agent. Your full instructions are loaded from backend/app/agents/${selectedAgent}.md.

IMPORTANT: When you need human approval (HITL), include a custom markdown tag in your response:
<hitl-approval requestId="unique-request-id">Brief description of what needs approval</hitl-approval>

This will render an inline approval component with approve/reject/modify buttons.

HITL Status: ${hitlEnabled ? `Enabled (${currentCounter}/${hitlCounter} actions remaining)` : 'Disabled'}
Message Count: ${messageCount} messages sent

To test HITL functionality:
1. Send messages to decrease the counter
2. When counter reaches 0, HITL approval will be required
3. Use the test buttons above to manually trigger HITL requests
4. Check the alerts bar at the top for pending approvals`}
                markdownTagRenderers={customMarkdownTagRenderers}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
