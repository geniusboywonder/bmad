"use client";

import { useCopilotChat } from "@copilotkit/react-core";
import { Bot, User, Expand, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/stores/app-store';
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import ChatInput from './chat-input';
import { websocketService } from "@/lib/websocket/websocket-service";
import { AGENT_DEFINITIONS } from "@/lib/agents/agent-definitions";

const CustomCopilotChat: React.FC = () => {
  const { conversation, addMessage, agentFilter, setAgentFilter } = useAppStore();
  const { isLoading } = useCopilotChat();
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  const handleSendMessage = async (content: string) => {
    addMessage({ type: 'user', agent: 'User', content });
    websocketService.startProject(content);
  };

  const filteredMessages = useMemo(() => {
    if (!agentFilter) return conversation;
    return conversation.filter(
      (msg) => msg.agent === agentFilter || msg.type === 'user' || msg.type === 'system'
    );
  }, [conversation, agentFilter]);

  const memoizedMessages = useMemo(() => {
    return filteredMessages.map((msg, index) => {
      const isUser = msg.type === 'user';
      return (
        <div key={index} className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
          <div className={cn('max-w-[80%] rounded-lg px-4 py-3 shadow-sm', isUser ? 'bg-primary text-primary-foreground' : 'bg-card border')}>
            <div className="flex items-center gap-2 mb-2">
              {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              <span className="text-xs font-medium">{msg.agent}</span>
            </div>
            <div className="text-sm leading-relaxed">{msg.content}</div>
          </div>
        </div>
      );
    });
  }, [filteredMessages]);

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
        <ChatInput onSend={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default CustomCopilotChat;
