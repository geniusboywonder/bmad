/**
 * CopilotKit + AG-UI Integration Demo (Refactored)
 *
 * Shows how to connect CopilotKit frontend to a backend that uses a
 * session governor for HITL, with approvals handled via native
 * CopilotKit actions that launch interactive prompts.
 */

"use client";

import dynamic from "next/dynamic";
import { useState, useEffect, useRef, useCallback } from "react";
import { useAgent } from "@/lib/context/agent-context";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { HITLReconfigurePrompt } from "@/components/hitl/HITLReconfigurePrompt";
import { websocketManager } from "@/lib/services/websocket/enhanced-websocket-client";
import { PolicyViolationEvent, AgentType } from "@/lib/services/api/types";
import { useAppStore } from "@/lib/stores/app-store";
import { useHumanInTheLoop } from "@copilotkit/react-core";
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
  const { selectedAgent, setSelectedAgent, projectId, setProjectId } = useAgent();
  const policyGuidance = useAppStore((state) => state.policyGuidance);
  const setPolicyGuidance = useAppStore((state) => state.setPolicyGuidance);
  const chatSectionRef = useRef<HTMLDivElement | null>(null);

  // Demo project ID - in production, this would come from URL params or project store
  // This project should exist in your database for policy enforcement to work
  const DEMO_PROJECT_ID = "018f9fa8-b639-4858-812d-57f592324a35";

  // Available agents
  const availableAgents: Array<{ name: AgentType; label: string; description: string }> = [
    { name: "analyst", label: "Analyst", description: "Requirements analysis and documentation" },
    { name: "architect", label: "Architect", description: "System architecture and design" },
    { name: "coder", label: "Coder", description: "Code implementation" },
    { name: "tester", label: "Tester", description: "Quality assurance and testing" },
    { name: "deployer", label: "Deployer", description: "Deployment and DevOps" },
    { name: "orchestrator", label: "Orchestrator", description: "Workflow coordination" }
  ];

  useEffect(() => {
    setIsClient(true);
    // Set project ID for policy enforcement
    setProjectId(DEMO_PROJECT_ID);
  }, [setProjectId]);

  useEffect(() => {
    if (!isClient) return;

    const handlePolicyViolation = (event: PolicyViolationEvent) => {
      const { status, message, current_phase, allowed_agents } = event.data;

      // Update the application state to show the policy guidance UI.
      setPolicyGuidance({
        status: status as "denied",
        message: message,
        currentPhase: current_phase,
        allowedAgents: allowed_agents as AgentType[],
      });

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

    const wsClient = websocketManager.getGlobalConnection();
    const unsubscribePolicy = wsClient.on('policy_violation', handlePolicyViolation);

    return () => {
      unsubscribePolicy();
    };
  }, [isClient]);

  const focusHitlPrompt = useCallback(() => {
    requestAnimationFrame(() => {
      const promptElement = chatSectionRef.current?.querySelector("[data-hitl-prompt='current']") as HTMLElement | null;
      if (!promptElement) return;
      promptElement.scrollIntoView({ behavior: "smooth", block: "center" });
      if (typeof promptElement.focus === "function") {
        promptElement.focus();
      }
    });
  }, []);

  const reconfigureHITL = useHumanInTheLoop({
    name: "reconfigureHITL",
    description: "Prompt the user to adjust HITL settings when the auto-approval counter is exhausted.",
    parameters: [
      { name: "actionLimit", type: "number", description: "The current auto-approval limit." },
      { name: "isHitlEnabled", type: "boolean", description: "Whether HITL is enabled for the project." }
    ],
    handler: async () => {
      const agentLabel =
        availableAgents.find((agent) => agent.name === selectedAgent)?.label ??
        selectedAgent.charAt(0).toUpperCase() + selectedAgent.slice(1);
      toast.warning(`${agentLabel} requires your attention for a human-in-the-loop action.`, {
        duration: 6000,
        action: {
          label: "Review",
          onClick: focusHitlPrompt
        }
      });
    },
    render: ({ args, respond }) => (
      <HitlPromptRenderer
        initialLimit={args.actionLimit}
        initialStatus={args.isHitlEnabled}
        projectId={projectId ?? DEMO_PROJECT_ID}
        respond={respond}
        onFocus={focusHitlPrompt}
      />
    )
  });

  return (
    <>
      <Toaster />
      <div className="min-h-screen flex flex-col">
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
              <li>✅ **NEW**: HITL prompts use native CopilotKit actions.</li>
              <li>✅ **DEPRECATED**: Legacy markdown-based HITL approvals.</li>
            </ul>
          </div>

          {/* Agent Progress Card is replaced by AgentState */}
          {/* {isClient && (
            <div className="mt-6 p-4 border rounded-lg">
              <AgentState />
            </div>
          )} */}

          {isClient && (
            <div data-testid="chat-section" ref={chatSectionRef}>
              <CopilotSidebar
                labels={{
                  title: `BMAD ${selectedAgent.charAt(0).toUpperCase() + selectedAgent.slice(1)} Agent`,
                  initial: `I'm your ${selectedAgent} agent. How can I help you today?`
                }}
                instructions={`You are the BMAD ${selectedAgent} agent. Your full instructions are loaded from the backend. HITL (Human-in-the-Loop) is managed by the backend session governor. Whenever you need human approval—either because the auto-approval counter is exhausted or you judge a step requires sign-off—call the 'reconfigureHITL' tool. Use the current settings you know (default: actionLimit = 10, isHitlEnabled = true) unless the user tells you different values; the UI will let them adjust the exact numbers.`}
                actions={[reconfigureHITL]}
              />
            </div>
          )}
          </div>
        </div>
      </div>
    </>
  );
}

interface HitlPromptRendererProps {
  initialLimit: number;
  initialStatus: boolean;
  projectId: string;
  respond: (value: string) => void;
  onFocus: () => void;
}

function HitlPromptRenderer({
  initialLimit,
  initialStatus,
  projectId,
  respond,
  onFocus,
}: HitlPromptRendererProps) {
  useEffect(() => {
    onFocus();
  }, [onFocus]);

  return (
    <HITLReconfigurePrompt
      initialLimit={initialLimit}
      initialStatus={initialStatus}
      onContinue={({ newLimit, newStatus }) => {
        toast.success("HITL settings updated. Agent can continue.", { duration: 5000 });
        respond(
          JSON.stringify({
            newLimit,
            newStatus,
            stop: false,
            projectId,
          })
        );
      }}
      onStop={() => {
        toast.info("Agent paused. Adjust HITL settings before continuing.", { duration: 5000 });
        respond(
          JSON.stringify({
            newLimit: initialLimit,
            newStatus: false,
            stop: true,
            projectId,
          })
        );
      }}
    />
  );
}
