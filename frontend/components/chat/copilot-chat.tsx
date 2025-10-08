"use client";

// import { useCopilotChat } from "@copilotkit/react-core";
import { Bot, User, Expand, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/stores/app-store';
import { useHITLStore } from '@/lib/stores/hitl-store';
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import ChatInput from './chat-input';
import { websocketService } from "@/lib/services/websocket/websocket-service";
import { AGENT_DEFINITIONS } from "@/lib/agents/agent-definitions";
import { InlineHITLApproval } from '@/components/hitl/inline-hitl-approval';
import { HitlCounterAlert } from '@/components/hitl/hitl-counter-alert';
import { getAgentBadgeClasses, getStatusBadgeClasses } from '@/lib/utils/badge-utils';
import { buildPolicyGuidance } from '@/lib/utils/policy-utils';
import type { AgentType } from '@/lib/services/api/types';

interface CopilotChatProps {
  projectId?: string;
}

const CustomCopilotChat: React.FC<CopilotChatProps> = ({ projectId }) => {
  console.log('[CopilotChat] Component rendered with projectId:', projectId);
  const {
    conversation,
    addMessage,
    agentFilter,
    setAgentFilter,
    policyGuidance,
    setPolicyGuidance,
  } = useAppStore();
  const { requests } = useHITLStore();
  const loadHitlSettings = useHITLStore((state) => state.loadSettings);
  const isLoading = false; // Temporarily disable CopilotKit
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const policyInputDisabled = policyGuidance?.status === 'denied';
  const policyPlaceholder = policyGuidance
    ? policyGuidance.status === 'needs_clarification'
      ? `Clarify instructions for the ${policyGuidance.currentPhase ?? 'current'} phase before retrying...`
      : 'Select an allowed agent for this phase before continuing.'
    : undefined;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  useEffect(() => {
    if (projectId) {
      loadHitlSettings(projectId).catch((error) => {
        console.error('[CopilotChat] Failed to load HITL settings', error);
      });
    }
  }, [projectId, loadHitlSettings]);

  // Initialize HITL messages from persisted store on mount
  useEffect(() => {
    if (!projectId) return;

    // Get pending HITL requests for this project
    const projectRequests = requests.filter(req =>
      req.status === 'pending' &&
      (!req.context?.projectId || req.context.projectId === projectId)
    );

    // Check which ones don't have messages in conversation yet
    for (const request of projectRequests) {
      const approvalId = request.context?.approvalId;
      if (!approvalId) continue;

      // Check if message already exists
      const messageExists = conversation.some(msg => msg.approvalId === approvalId);
      if (!messageExists) {
        console.log(`[CopilotChat] Restoring HITL message for ${approvalId}`);
        const taskInstructions = request.context?.requestData?.instructions || "Execute task";
        addMessage({
          type: "hitl_request",
          agent: `${request.agentName} Agent`,
          content: `🚨 **HITL Approval Required**\n\nI need permission to: "${taskInstructions}"\n\n📊 **Estimated cost:** $${request.context?.estimatedCost?.toFixed(4) || '0.0150'}\n⏱️ **Estimated tokens:** ${request.context?.estimatedTokens || 100}\n\n⚠️ **Waiting for human approval before proceeding...**`,
          urgency: (request.context?.estimatedCost && request.context.estimatedCost > 5) ? "high" : "medium",
          requestId: approvalId,
          taskId: request.context?.taskId,
          approvalId: approvalId,
          hitlStatus: "pending"
        });
      }
    }
  }, [projectId]); // Only run when projectId changes

  const handleSendMessage = async (content: string) => {
    console.log('[CopilotChat] handleSendMessage called with projectId:', projectId, 'content:', content);
    addMessage({ type: 'user', agent: 'User', content });
    setPolicyGuidance(null);

    // Create a task through API to trigger HITL workflow
    if (projectId) {
      console.log('[CopilotChat] Creating task for project:', projectId);
      try {
        const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/tasks`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            agent_type: 'analyst', // Default to analyst for user requests
            instructions: content,
            context_ids: [], // No context for now
            estimated_tokens: 100 // Rough estimate
          }),
        });

        if (response.ok) {
          const result = await response.json();
          console.log('🎯 Task created successfully:', result);
          addMessage({
            type: 'system',
            agent: 'System',
            content: `Task created: ${result.task_id}. HITL approval required before execution.`
          });
          setPolicyGuidance(null);
        } else {
          let detailPayload: any = null;
          try {
            detailPayload = await response.json();
          } catch (err) {
            console.warn('[CopilotChat] Failed to parse policy error payload', err);
          }

          const guidance = buildPolicyGuidance(detailPayload, response.statusText);
          if (guidance) {
            setPolicyGuidance(guidance);
          }

          const errorMessage = guidance?.message || `Failed to create task (${response.status})`;

          console.error('❌ Failed to create task:', response.status, response.statusText, detailPayload);
          addMessage({
            type: 'system',
            agent: 'System',
            content: `Error: ${errorMessage}`
          });
        }
      } catch (error) {
        console.error('❌ Network error creating task:', error);
        addMessage({
          type: 'system',
          agent: 'System',
          content: `Error: Network error creating task`
        });
      }
    } else {
      // Fallback to WebSocket if no project ID
      websocketService.sendChatMessage(content, projectId);
      setPolicyGuidance(null);
    }
  };

  const filteredMessages = useMemo(() => {
    let messages = conversation;
    if (agentFilter) {
      messages = conversation.filter(
        (msg) => msg.agent === agentFilter || msg.type === 'user' || msg.type === 'system'
      );
    }

    // Filter out messages with React content to prevent CopilotKit errors
    return messages.filter(msg => typeof msg.content === 'string');
  }, [conversation, agentFilter]);

  const memoizedMessages = useMemo(() => {
    return filteredMessages.map((msg, index) => {
      if (msg.type === 'hitl_counter') {
        const metadata = msg.metadata || {};
        return (
          <div
            key={index}
            className="flex w-full justify-start"
            data-approval-id={msg.approvalId}
          >
            <div className="max-w-[80%] rounded-lg px-4 py-3 shadow-sm border bg-amber/5 border-amber/30 text-foreground">
              <div className="text-sm font-semibold mb-2 text-amber-700">
                HITL Counter Limit Reached
              </div>
              <HitlCounterAlert
                projectId={metadata.projectId || projectId}
                counterTotal={metadata.counterTotal ?? 0}
                counterRemaining={metadata.counterRemaining ?? 0}
                hitlEnabled={metadata.hitlEnabled ?? true}
                locked={metadata.locked ?? false}
              />
            </div>
          </div>
        );
      }

      const isUser = msg.type === 'user';
      const isHITLRequest = msg.type === 'hitl_request';

      // For HITL request messages, find the matching HITL request from store
      let hitlRequest = null;
      if (isHITLRequest && msg.approvalId) {
        hitlRequest = requests.find(req => req.context?.approvalId === msg.approvalId);

        // Debug logging for HITL request matching
        if (!hitlRequest) {
          console.log(`[CopilotChat] Could not find HITL request for approvalId: ${msg.approvalId}`);
          console.log(`[CopilotChat] Available requests:`, requests.map(r => ({
            id: r.id,
            approvalId: r.context?.approvalId,
            status: r.status
          })));
        } else {
          console.log(`[CopilotChat] Found HITL request:`, {
            id: hitlRequest.id,
            approvalId: hitlRequest.context?.approvalId,
            status: hitlRequest.status
          });
        }
      }

      return (
        <div
          key={index}
          className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}
          data-task-id={msg.taskId}
          data-request-id={msg.requestId}
          data-approval-id={msg.approvalId}
        >
          <div className={cn(
            'max-w-[80%] rounded-lg px-4 py-3 shadow-sm border transition-all duration-150',
            isUser
              ? 'bg-primary text-primary-foreground border-primary/20'
              : isHITLRequest
                ? 'bg-amber/5 border-amber/20 text-foreground'
                : 'bg-card border-border text-foreground'
          )}>
            <div className="flex items-center gap-2 mb-2">
              {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}

              {/* Agent Badge using centralized system */}
              <Badge
                variant="muted"
                size="sm"
                className={cn(
                  "text-[10px] px-1 py-0.5 h-4",
                  isUser ? "bg-primary-foreground/10 text-primary-foreground border-primary-foreground/20" :
                  getAgentBadgeClasses(msg.agent)
                )}
              >
                {msg.agent}
              </Badge>

              {msg.taskId && (
                <Badge variant="outline" size="sm" className="text-[10px] px-1 py-0.5 h-4 font-mono">
                  Task: {msg.taskId.slice(-8)}
                </Badge>
              )}

              {/* HITL Status Badge using centralized system */}
              {isHITLRequest && msg.hitlStatus && (
                <Badge
                  variant="muted"
                  size="sm"
                  className={cn(
                    "text-[10px] px-1 py-0.5 h-4 font-mono",
                    getStatusBadgeClasses(
                      msg.hitlStatus === 'approved' ? 'completed' :
                      msg.hitlStatus === 'rejected' ? 'error' :
                      msg.hitlStatus === 'modified' ? 'waiting' :
                      'pending'
                    )
                  )}
                >
                  {msg.hitlStatus === 'modified' ? 'REDIRECTED' : msg.hitlStatus.toUpperCase()}
                </Badge>
              )}
            </div>
            <div className="text-sm leading-relaxed">{msg.content}</div>

            {/* Show HITL approval component for HITL request messages */}
            {isHITLRequest && (
              msg.hitlStatus === 'pending' ? (
                hitlRequest ? (
                  <InlineHITLApproval
                    request={hitlRequest}
                    className="mt-3"
                  />
                ) : (
                  <div className="mt-3 p-3 bg-muted/50 border border-border rounded-lg text-sm text-muted-foreground">
                    ⚠️ This HITL request has expired or been resolved elsewhere.
                  </div>
                )
              ) : null
            )}
          </div>
        </div>
      );
    });
  }, [filteredMessages, requests]);

  return (
    <div className={cn(
      "flex flex-col transition-all duration-300 rounded-lg border bg-card",
      isExpanded ? "fixed inset-4 z-50 shadow-2xl" : "h-full"
    )}>
      <div className="px-6 py-4 border-b flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold">BotArmy Chat</h2>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setIsExpanded(!isExpanded)}>
            <Expand className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="px-6 py-4 border-b bg-gradient-to-r from-card/50 to-card flex-shrink-0">
        <div className="flex items-center gap-4 flex-wrap">
          {AGENT_DEFINITIONS.map((agent) => {
            const agentName = agent.name as AgentType;
            const isSelected = agentFilter === agent.name;
            const allowedAgents = policyGuidance?.allowedAgents ?? [];
            const isRestricted = policyGuidance && allowedAgents.length > 0 && !allowedAgents.includes(agentName);
            const badgeHighlight = policyGuidance && allowedAgents.includes(agentName);

            return (
              <button
                key={agent.name}
                onClick={() => {
                  if (isRestricted) {
                    return;
                  }
                  setAgentFilter(isSelected ? null : agent.name);
                }}
                className={cn(
                  "flex flex-col items-center p-2 rounded-lg transition-all duration-200 group hover:scale-105 border",
                  isSelected ? "bg-primary/10 ring-2 ring-primary/20 border-primary/60" : "hover:bg-secondary/50 border-transparent",
                  isRestricted && "opacity-50 cursor-not-allowed border-destructive/60",
                  badgeHighlight && !isSelected && "border-primary/40"
                )}
                disabled={isRestricted}
                title={
                  isRestricted
                    ? "Agent not available in current phase"
                    : agent.description
                }
              >
                <div className={cn(
                  "w-12 h-12 rounded-full border-2 flex items-center justify-center mb-2 transition-all duration-200",
                  isSelected
                    ? cn("border-2 shadow-md", getAgentBadgeClasses(agent.name).replace('bg-', 'border-').replace('/5', '/40'))
                    : "border-border hover:border-primary/30"
                )}>
                  <agent.icon className={cn(
                    "w-6 h-6 transition-colors duration-200",
                    isSelected
                      ? getAgentBadgeClasses(agent.name).split(' ').find(c => c.startsWith('text-')) || "text-primary"
                      : "text-muted-foreground group-hover:text-foreground"
                  )} />
                </div>
                <Badge
                  variant="muted"
                  size="sm"
                  className={cn(
                    "text-[10px] px-1 py-0.5 h-4",
                    isSelected
                      ? getAgentBadgeClasses(agent.name)
                      : badgeHighlight
                        ? "text-primary border-primary/50"
                        : "text-muted-foreground border-muted-foreground/20"
                  )}
                >
                  {agent.name}
                </Badge>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        <div className="p-6 space-y-4">
          {memoizedMessages}
          {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg px-4 py-3 bg-card border">
                  <div className="flex items-center gap-2 mb-2">
                    <Bot className="w-4 h-4" />
                    <span className="text-xs font-medium">BotArmy Assistant</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Thinking...
                  </div>
                </div>
              </div>
            )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t bg-gradient-to-r from-card/30 to-card/50 flex-shrink-0">
        <ChatInput
          onSend={handleSendMessage}
          isLoading={isLoading}
          hasActiveHITL={false}
          disabled={policyInputDisabled}
          placeholder={policyPlaceholder}
        />
        {policyGuidance && (
          <div className="px-6 py-2 text-xs text-muted-foreground border-t border-destructive/20 bg-destructive/5">
            {policyGuidance.message}
            {policyGuidance.allowedAgents.length > 0 && (
              <>
                {' '}
                Allowed agents:{' '}
                {policyGuidance.allowedAgents
                  .map((agent) => agent.charAt(0).toUpperCase() + agent.slice(1))
                  .join(', ')}
                .
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomCopilotChat;
