"use client";

// import { useCopilotChat } from "@copilotkit/react-core";
import { Bot, User, Expand, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/stores/app-store';
import { useHITLStore } from '@/lib/stores/hitl-store';
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import ChatInput from './chat-input';
import { websocketService } from "@/lib/services/websocket/websocket-service";
import { AGENT_DEFINITIONS } from "@/lib/agents/agent-definitions";
import { InlineHITLApproval } from '@/components/hitl/inline-hitl-approval';

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

      // For system messages that mention "Task created", show HITL request (pending or resolved)
      // This approach works because task creation and HITL request creation happen simultaneously
      const isTaskCreatedMessage = msg.type === 'system' && msg.content.includes('Task created:');
      const hitlRequest = isTaskCreatedMessage ?
        requests.find(req => req.status === 'pending') || requests[requests.length - 1] : null;

      return (
        <div key={index} className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
          <div className={cn('max-w-[80%] rounded-lg px-4 py-3 shadow-sm', isUser ? 'bg-primary text-primary-foreground' : 'bg-card border')}>
            <div className="flex items-center gap-2 mb-2">
              {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              <span className="text-xs font-medium">{msg.agent}</span>
            </div>
            <div className="text-sm leading-relaxed">{msg.content}</div>

            {/* Show HITL approval component if there's a matching request */}
            {hitlRequest && (
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

      <div className="px-6 py-4 border-b">
        <div className="flex items-center gap-4">
          {AGENT_DEFINITIONS.map((agent) => {
            const isSelected = agentFilter === agent.name;
            return (
              <button
                key={agent.name}
                onClick={() => setAgentFilter(isSelected ? null : agent.name)}
                className={cn(
                  "flex flex-col items-center p-2 rounded-lg transition-all group",
                  isSelected ? "bg-primary/10" : "hover:bg-secondary/50"
                )}
              >
                <div className={cn("w-12 h-12 rounded-full border-2 flex items-center justify-center mb-2 transition-all", isSelected ? "border-primary bg-primary/10" : "border-border")}>
                  <agent.icon className={cn("w-6 h-6", isSelected ? "text-primary" : "text-muted-foreground")} />
                </div>
                <div className={cn("text-xs font-medium", isSelected ? "text-primary" : "text-muted-foreground")}>
                  {agent.name}
                </div>
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

      <div className="border-t">
        <ChatInput onSend={handleSendMessage} isLoading={isLoading} hasActiveHITL={false} />
      </div>
    </div>
  );
};

export default CustomCopilotChat;
