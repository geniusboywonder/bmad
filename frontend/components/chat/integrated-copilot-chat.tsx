"use client";

import React, { useEffect, useMemo } from "react";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCoAgent } from "@copilotkit/react-core";
import { useAppStore } from "@/lib/stores/app-store";
import { useHITLStore } from "@/lib/stores/hitl-store";
import { AgentProgressCard } from "@/components/copilot/agent-progress-ui";
import { InlineHITLApproval } from "@/components/hitl/inline-hitl-approval";
import { AGENT_DEFINITIONS } from "@/lib/agents/agent-definitions";
import "@copilotkit/react-ui/styles.css";

interface IntegratedCopilotChatProps {
  projectId?: string;
  agentName?: string;
}

/**
 * Integrated CopilotKit Chat
 *
 * Combines:
 * - CopilotKit's chat UI and agent communication
 * - BMAD's HITL approval system
 * - Agent progress tracking with useCoAgent
 * - Custom message rendering for HITL requests
 */
export function IntegratedCopilotChat({
  projectId,
  agentName = "analyst"
}: IntegratedCopilotChatProps) {
  const { addMessage } = useAppStore();
  const { requests } = useHITLStore();

  // Sync agent state with CopilotKit using useCoAgent
  const { state: agentState, setState: setAgentState } = useCoAgent({
    name: agentName,
    initialState: {
      agent_name: agentName,
      tasks: [],
      overall_progress: 0,
      status: "idle" as const,
      current_task: undefined
    }
  });

  // Initialize HITL messages from persisted store
  useEffect(() => {
    if (!projectId) return;

    const projectRequests = requests.filter(req =>
      req.status === 'pending' &&
      (!req.context?.projectId || req.context.projectId === projectId)
    );

    for (const request of projectRequests) {
      const approvalId = request.context?.approvalId;
      if (!approvalId) continue;

      console.log(`[IntegratedCopilotChat] HITL request detected: ${approvalId}`);

      // Store in BMAD's app store for tracking
      const taskInstructions = request.context?.requestData?.instructions || "Execute task";
      addMessage({
        type: "hitl_request",
        agent: `${request.agentName} Agent`,
        content: `🚨 **HITL Approval Required**\n\n${taskInstructions}`,
        urgency: (request.context?.estimatedCost && request.context.estimatedCost > 5) ? "high" : "medium",
        requestId: approvalId,
        taskId: request.context?.taskId,
        approvalId: approvalId,
        hitlStatus: "pending"
      });
    }
  }, [projectId, requests]);

  // Custom message renderer for HITL approvals
  const makeSystemMessage = (message: any) => {
    // Check if this is a HITL request by looking for approval context
    const hitlRequest = requests.find(req =>
      req.context?.approvalId &&
      message.content?.includes(req.context.approvalId)
    );

    if (hitlRequest && hitlRequest.status === 'pending') {
      return (
        <div className="space-y-2">
          <div className="text-sm text-muted-foreground">{message.content}</div>
          <InlineHITLApproval
            request={hitlRequest}
            className="mt-3"
          />
        </div>
      );
    }

    return message.content;
  };

  return (
    <div className="h-full flex flex-col">
      {/* Agent Progress Card - Shows task breakdown */}
      <div className="p-4 border-b bg-card/50">
        <AgentProgressCard agentName={agentName} />
      </div>

      {/* CopilotKit Sidebar - Main chat interface */}
      <div className="flex-1 min-h-0">
        <CopilotSidebar
          defaultOpen={true}
          clickOutsideToClose={false}
          labels={{
            title: `BMAD ${agentName.charAt(0).toUpperCase() + agentName.slice(1)} Agent`,
            initial: `I'm your ${agentName} agent. How can I help you today?`,
          }}
          onSubmitMessage={(message) => {
            console.log('[IntegratedCopilotChat] User message:', message);

            // Update agent state
            setAgentState({
              ...agentState,
              status: "working",
              current_task: typeof message === 'string' ? message : message.content
            });

            // Store in BMAD app store
            addMessage({
              type: 'user',
              agent: 'User',
              content: typeof message === 'string' ? message : message.content
            });
          }}
          makeSystemMessage={makeSystemMessage}
          instructions={`You are the BMAD ${agentName} agent. Respond helpfully and concisely to user requests.`}
        />
      </div>
    </div>
  );
}
