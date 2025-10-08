/**
 * CopilotKit + AG-UI Integration Demo (Refactored)
 *
 * Shows how to connect CopilotKit frontend to a backend that uses a
 * session governor for HITL, with UI interactions handled by native
 * CopilotKit client-side actions.
 */

"use client";

import dynamic from "next/dynamic";
import { useState, useEffect } from "react";
import { useAgent } from "@/lib/context/agent-context";
import { useCopilotAction } from "@copilotkit/react-core";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Settings, AlertTriangle, ToggleLeft, ToggleRight } from "lucide-react";
import { Toaster, toast } from "sonner";
import { HITLReconfigurePrompt } from "@/components/hitl/HITLReconfigurePrompt";
import { websocketManager } from "@/lib/services/websocket/enhanced-websocket-client";
import { PolicyViolationEvent, AgentType } from "@/lib/services/api/types";
import { useAppStore } from "@/lib/stores/app-store";
import "@copilotkit/react-ui/styles.css";

// Dynamically import CopilotSidebar and AgentState
const CopilotSidebar = dynamic(
  () => import("@copilotkit/react-ui").then((mod) => ({ default: mod.CopilotSidebar })),
  {
    ssr: false,
    loading: () => <div className="fixed right-4 bottom-4 w-12 h-12 bg-primary rounded-full animate-pulse" />
  }
);

// TODO: Replace with AgentState once its package is confirmed.
// const AgentState = dynamic(
//   () => import("@copilotkit/react-ui").then((mod) => ({ default: mod.AgentState })),
//   { ssr: false }
// );

export default function CopilotDemoPage() {
  const [isClient, setIsClient] = useState(false);
  const { selectedAgent, setSelectedAgent } = useAgent();
  const policyGuidance = useAppStore((state) => state.policyGuidance);
  const setPolicyGuidance = useAppStore((state) => state.setPolicyGuidance);
  const [hitlPromptData, setHitlPromptData] = useState<{ settings: any; projectId: string | null } | null>(null);

  // Available agents
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

  useEffect(() => {
    if (!isClient) return;

    const handlePolicyViolation = (event: PolicyViolationEvent) => {
      const { reason_code, message, current_phase, allowed_agents } = event.data;
      
      const allowedAgentsString = allowed_agents.join(', ');
      const toastMessage = `
        **Policy Violation**
        ${message}
        **Current Phase:** ${current_phase}
        **Allowed Agents:** ${allowedAgentsString}
      `;

      toast.error("Action Blocked", {
        description: toastMessage,
        duration: 10000,
      });
    };

    const handleLimitReached = (event: any) => {
      console.log("HITL limit reached event received:", event);
      toast.warning("HITL Limit Reached", {
        description: "Auto-approval limit reached. Manual approval is now required for agent actions.",
        duration: 8000,
      });
      setHitlPromptData({
        settings: event.data.current_settings,
        projectId: event.project_id,
      });
    };

    const wsClient = websocketManager.getGlobalConnection();
    const unsubscribePolicy = wsClient.on('policy_violation', handlePolicyViolation);
    const unsubscribeLimit = wsClient.on('hitl_counter_limit_reached', handleLimitReached);


    return () => {
      unsubscribePolicy();
      unsubscribeLimit();
    };
  }, [isClient]);

  return (
    <div className="min-h-screen flex flex-col">
      <Toaster />
      {/* HITLAlertsBar is removed. Toasts will be handled by the Toaster in the root layout. */}
      
        <div className="container mx-auto p-6 flex-1">
          <div className="mb-6">
            <h1 className="text-3xl font-bold mb-2">
              BMAD AI Agent Dashboard
            </h1>
            <p className="text-muted-foreground">
              Real-time agent progress with CopilotKit + AG-UI protocol and HITL controls
            </p>

            {policyGuidance && (
              <div className="mt-4 border border-destructive/40 bg-destructive/10 rounded-lg p-4" data-testid="policy-guidance">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 mt-0.5 text-destructive" />
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-3">
                      <span className="text-sm uppercase tracking-wide text-destructive font-semibold">
                        {policyGuidance.status === "denied" ? "Policy Blocked" : "Needs Clarification"}
                      </span>
                      <Badge variant="secondary">
                        Phase: {policyGuidance.currentPhase ?? "unknown"}
                      </Badge>
                    </div>
                    <p className="text-sm text-destructive">
                      {policyGuidance.message}
                    </p>
                    {policyGuidance.allowedAgents.length > 0 && (
                      <div className="text-xs text-muted-foreground">
                        Allowed agents this phase:{" "}
                        <span className="font-medium text-foreground">
                          {policyGuidance.allowedAgents.map((agent) => agent.charAt(0).toUpperCase() + agent.slice(1)).join(", ")}
                        </span>
                      </div>
                    )}
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setPolicyGuidance(null)}
                    className="text-xs"
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            )}

            {/* --- HITL Reconfiguration Prompt --- */}
            {hitlPromptData && (
              <div className="my-4 p-4 border-dashed border-2 border-amber-500 rounded-lg bg-amber-500/10">
                 <HITLReconfigurePrompt
                  initialLimit={hitlPromptData.settings.limit}
                  initialStatus={hitlPromptData.settings.enabled}
                  onContinue={async (response) => {
                    if (!hitlPromptData.projectId) {
                      toast.error("Error: Project ID is missing.");
                      setHitlPromptData(null);
                      return;
                    }
                    try {
                      const apiResponse = await fetch(`/api/v1/hitl/settings/${hitlPromptData.projectId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(response),
                      });
                      if (!apiResponse.ok) {
                        throw new Error("Failed to update HITL settings.");
                      }
                      toast.success("HITL settings updated. Auto-approvals are active again.");
                    } catch (error) {
                      toast.error("Error updating HITL settings.");
                      console.error(error);
                    } finally {
                      setHitlPromptData(null);
                    }
                  }}
                  onStop={() => {
                    console.log("Stop action chosen.");
                    setHitlPromptData(null);
                  }}
                />
              </div>
            )}

          {/* Agent Selector */}
          {isClient && (
            <div className="mt-4">
              <label className="text-sm font-medium mb-2 block">Select Agent:</label>
              <div className="flex gap-2 flex-wrap">
                {availableAgents.map((agent) => (
                  <button
                    key={agent.name}
                    onClick={() => setSelectedAgent(agent.name)}
                    className={`px-3 py-2 rounded-lg text-sm transition-all border ${
                      selectedAgent === agent.name
                        ? 'bg-primary text-primary-foreground shadow-md border-primary'
                        : 'bg-muted hover:bg-muted/80 border-transparent'
                    } ${
                      policyGuidance && policyGuidance.allowedAgents.length > 0 && !policyGuidance.allowedAgents.includes(agent.name as AgentType)
                        ? 'opacity-50 cursor-not-allowed border-destructive/60'
                        : ''
                    }`}
                    title={agent.description}
                    disabled={
                      !!policyGuidance &&
                      policyGuidance.allowedAgents.length > 0 &&
                      !policyGuidance.allowedAgents.includes(agent.name as AgentType)
                    }
                  >
                    {agent.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="mt-6 p-4 border rounded-lg bg-muted/50">
            <h2 className="text-xl font-semibold mb-2">AG-UI Integration Status</h2>
            <ul className="space-y-2 text-sm">
              <li>✅ CopilotKit Provider: Using global configuration</li>
              <li>✅ Runtime URL: /api/copilotkit</li>
              <li>✅ Selected Agent: {selectedAgent}</li>
              <li>✅ LLM: OpenAI GPT-4 Turbo via LiteLLM</li>
              <li>✅ **NEW**: HITL logic is now backend-driven via Session Governor.</li>
              <li>✅ **NEW**: Interactive prompts are handled by `useCopilotKitAction`.</li>
              <li>✅ **DEPRECATED**: Frontend counter, `useHITLStore`, `HITLAlertsBar`.</li>
            </ul>
          </div>

          {/* Agent Progress Card is replaced by AgentState */}
          {/* {isClient && (
            <div className="mt-6 p-4 border rounded-lg">
              <AgentState />
            </div>
          )} */}

          {isClient && (
            <div data-testid="chat-section">
              <CopilotSidebar
                labels={{
                  title: `BMAD ${selectedAgent.charAt(0).toUpperCase() + selectedAgent.slice(1)} Agent`,
                  initial: `I'm your ${selectedAgent} agent. How can I help you today?`
                }}
                instructions={`You are the BMAD ${selectedAgent} agent. Your full instructions are loaded from the backend. HITL (Human-in-the-Loop) is managed by the backend. When you reach your action limit, you will be instructed to call the 'reconfigureHITL' function to ask the user for guidance.`}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
