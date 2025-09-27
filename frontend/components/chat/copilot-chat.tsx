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
import { getAgentBadgeClasses, getStatusBadgeClasses } from '@/lib/utils/badge-utils';

interface CopilotChatProps {
  projectId?: string;
}

const CustomCopilotChat: React.FC<CopilotChatProps> = ({ projectId }) => {
  const { conversation, addMessage, agentFilter, setAgentFilter } = useAppStore();
  const { requests } = useHITLStore();
  const isLoading = false; // Temporarily disable CopilotKit
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  const handleSendMessage = async (content: string) => {
    addMessage({ type: 'user', agent: 'User', content });

    // Create a task through API to trigger HITL workflow
    if (projectId) {
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
        } else {
          console.error('❌ Failed to create task:', response.status, response.statusText);
          addMessage({
            type: 'system',
            agent: 'System',
            content: `Error: Failed to create task (${response.status})`
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
      const isUser = msg.type === 'user';
      const isHITLRequest = msg.type === 'hitl_request';

      // For HITL request messages, find the matching HITL request from store
      const hitlRequest = isHITLRequest && msg.approvalId ?
        requests.find(req => req.context?.approvalId === msg.approvalId) : null;

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
                      'pending'
                    )
                  )}
                >
                  {msg.hitlStatus.toUpperCase()}
                </Badge>
              )}
            </div>
            <div className="text-sm leading-relaxed">{msg.content}</div>

            {/* Show HITL approval component only for pending HITL request messages */}
            {isHITLRequest && hitlRequest && msg.hitlStatus === 'pending' && (
              <InlineHITLApproval
                request={hitlRequest}
                className="mt-3"
              />
            )}
          </div>
        </div>
      );
    });
  }, [filteredMessages, requests]);

  return (
    <div className={cn(
      "flex flex-col transition-all duration-300 rounded-lg border bg-card h-full",
      isExpanded && "fixed inset-4 z-50 shadow-2xl"
    )}>
      <div className="px-6 py-4 border-b">
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

      <div className="px-6 py-4 border-b bg-gradient-to-r from-card/50 to-card">
        <div className="flex items-center gap-4">
          {AGENT_DEFINITIONS.map((agent) => {
            const isSelected = agentFilter === agent.name;
            return (
              <button
                key={agent.name}
                onClick={() => setAgentFilter(isSelected ? null : agent.name)}
                className={cn(
                  "flex flex-col items-center p-2 rounded-lg transition-all duration-200 group hover:scale-105",
                  isSelected ? "bg-primary/10 ring-2 ring-primary/20" : "hover:bg-secondary/50"
                )}
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
                    isSelected ? getAgentBadgeClasses(agent.name) : "text-muted-foreground border-muted-foreground/20"
                  )}
                >
                  {agent.name}
                </Badge>
              </button>
            );
          })}
        </div>
      </div>
      
      <div className="flex-grow overflow-hidden">
        <ScrollArea className="h-full">
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
        </ScrollArea>
      </div>

      <div className="border-t bg-gradient-to-r from-card/30 to-card/50">
        <ChatInput onSend={handleSendMessage} isLoading={isLoading} hasActiveHITL={false} />
      </div>
    </div>
  );
};

export default CustomCopilotChat;
