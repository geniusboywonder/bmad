"use client";

import { useCopilotChat, useCopilotReadable } from "@copilotkit/react-core";
import { Role, TextMessage } from "@copilotkit/runtime-client-gql";
import { Bot, User, Expand, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AGENT_DEFINITIONS } from '@/lib/agents/agent-definitions';
import { useAgentStore } from '@/lib/stores/agent-store';
import { useConversationStore } from '@/lib/stores/conversation-store';
import { useHITLStore } from '@/lib/stores/hitl-store';
import React, { useState, useEffect, useMemo, useRef, useLayoutEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import ChatInput from './chat-input';
import { HITLApprovalComponent } from '../hitl/hitl-approval';

// Local Role enum for internal use
enum LocalRole {
  User = 'User',
  Assistant = 'Assistant'
}

// Local timestamp formatting function
const formatTimestamp = (timestamp: Date | string): string => {
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const CustomCopilotChat: React.FC = () => {
  const { agent, agentFilter, setAgentFilter } = useAgentStore();
  const { messages, addMessage, clearMessages } = useConversationStore();
  const { activeRequest, resolveRequest } = useHITLStore();

  // CopilotKit integration for working LLM chat
  const {
    visibleMessages,
    appendMessage,
    setMessages,
    deleteMessage,
    reloadMessages,
    stopGeneration,
    isLoading: copilotIsLoading,
  } = useCopilotChat({
    id: "botarmy-chat"
  });

  // Safety check for store hydration issues
  if (!setAgentFilter) {
    console.warn('setAgentFilter function not available, store may not be hydrated');
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <div className="text-center">
          <div className="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
          <p>Loading chat interface...</p>
        </div>
      </div>
    );
  }

  const [isExpanded, setIsExpanded] = useState(false);
  const [forceShowHITL, setForceShowHITL] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useLayoutEffect(() => {
    if (activeRequest && setAgentFilter) {
      setAgentFilter(activeRequest.agentName);
      setForceShowHITL(true);
    } else {
      setForceShowHITL(false);
    }
  }, [activeRequest, setAgentFilter]);

  useEffect(() => {
    if (forceShowHITL && agentFilter && activeRequest && agentFilter === activeRequest.agentName) {
      const timer = setTimeout(() => {
        setForceShowHITL(false);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [forceShowHITL, agentFilter, activeRequest]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [visibleMessages, copilotIsLoading]);

  const handleSendMessage = async (content: string) => {
    // Use CopilotKit to send the message
    await appendMessage(new TextMessage({
      content: content,
      role: Role.User,
    }));
  };

  // Convert CopilotKit messages to our format for filtering
  const convertedMessages = useMemo(() => {
    return visibleMessages.map((msg, index) => ({
      id: msg.id || `msg-${index}`,
      role: msg.role === Role.User ? LocalRole.User : LocalRole.Assistant,
      content: msg.content,
      agent: msg.role === Role.User ? 'User' : 'BotArmy Assistant',
      timestamp: new Date(),
    }));
  }, [visibleMessages]);

  const filteredMessages = useMemo(() => {
    if (!agentFilter) return convertedMessages;
    return convertedMessages.filter(
      (msg) =>
        msg.agent === agentFilter ||
        msg.agent === 'User' ||
        msg.role === LocalRole.User
    );
  }, [convertedMessages, agentFilter]);

  const shouldShowHITL = useMemo(() => {
    if (!isClient) return false;
    if (forceShowHITL && activeRequest) return true;
    return activeRequest && agentFilter && activeRequest.agentName === agentFilter;
  }, [activeRequest, isClient, agentFilter, forceShowHITL]);

  return (
    <div className={cn(
      "flex flex-col transition-all duration-300 rounded-lg border border-border bg-card",
      isExpanded 
        ? "fixed inset-4 z-50 h-auto max-h-[calc(100vh-2rem)] shadow-2xl" 
        : "h-full"
    )}>
      {/* Header matching Process Summary style */}
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">BotArmy Chat</h2>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => {
                setMessages([]);
                clearMessages && clearMessages();
              }}
              title="Clear all chat messages"
            >
              Clear Chat
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setIsExpanded(!isExpanded)}
              title={isExpanded ? "Collapse chat" : "Expand chat"}
            >
              <Expand className={cn("w-4 h-4", isExpanded && "rotate-180")} />
            </Button>
          </div>
        </div>
      </div>
      
      {/* Agent Bar matching Process Summary connected icons */}
      <div className="px-6 py-4 border-b border-border">
        <div className="flex items-center justify-between">
          {AGENT_DEFINITIONS.map((agent, index) => {
            const isSelected = agentFilter === agent.name;
            const isLast = index === AGENT_DEFINITIONS.length - 1;
            
            // Get agent colors matching the Process Summary style
            const getAgentColor = (agentName: string) => {
              switch (agentName) {
                case 'Analyst': return 'text-slate-500';
                case 'Architect': return 'text-pink-500';
                case 'Developer': return 'text-lime-600';
                case 'Tester': return 'text-sky-500';
                case 'Deployer': return 'text-rose-600';
                default: return 'text-muted-foreground';
              }
            };
            
            return (
              <div key={agent.name} className="flex items-center">
                <button
                  onClick={() => setAgentFilter && setAgentFilter(agentFilter === agent.name ? '' : agent.name)}
                  className={cn(
                    "relative flex flex-col items-center p-2 rounded-lg transition-all group",
                    isSelected ? "bg-primary/10" : "hover:bg-secondary/50"
                  )}
                >
                  {/* Status indicator circle */}
                  <div className={cn(
                    "w-12 h-12 rounded-full border-2 flex items-center justify-center mb-2 transition-all",
                    isSelected 
                      ? "border-primary bg-primary text-white" 
                      : "border-border bg-card hover:border-primary/50"
                  )}>
                    <agent.icon className={cn(
                      "w-6 h-6 transition-colors",
                      isSelected ? "text-white" : getAgentColor(agent.name)
                    )} />
                  </div>
                  
                  {/* Agent name */}
                  <div className={cn(
                    "text-xs font-medium text-center",
                    isSelected ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                  )}>
                    {agent.name}
                  </div>
                  
                  {/* Status */}
                  <div className="text-xs text-muted-foreground">
                    {agent.status === 'idle' ? 'Idle' : agent.status}
                  </div>
                </button>
                
                {/* Connector line */}
                {!isLast && (
                  <div className="w-4 h-px bg-border mx-1" />
                )}
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Chat Messages Area */}
      <div className="flex-grow overflow-hidden">
        <div className="flex flex-col h-full">
          <ScrollArea className="flex-grow h-0">
            <div className="p-6 space-y-4">
              {filteredMessages.length === 0 && !copilotIsLoading && (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Bot className="w-12 h-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">
                    Hello! I'm your BotArmy assistant.
                  </h3>
                  <p className="text-muted-foreground text-sm">
                    How can I help you today? Describe your project or ask me anything!
                  </p>
                </div>
              )}
              
              {filteredMessages.map((message, index) => {
                const isUser = message.role === LocalRole.User;
                const isSystem = message.agent === 'System';
                
                return (
                  <div 
                    key={`${message.id || index}`}
                    className={cn(
                      "flex w-full",
                      isUser ? "justify-end" : "justify-start"
                    )}
                  >
                    <div 
                      className={cn(
                        "max-w-[80%] rounded-lg px-4 py-3 shadow-sm",
                        isUser 
                          ? "bg-primary text-primary-foreground ml-12" 
                          : isSystem
                          ? "bg-muted text-muted-foreground border border-border"
                          : "bg-card border border-border text-foreground mr-12"
                      )}
                    >
                      {/* Message header with agent name and timestamp */}
                      {!isUser && (
                        <div className="flex items-center gap-2 mb-2">
                          <div className="flex items-center gap-1">
                            {isSystem ? (
                              <div className="w-2 h-2 rounded-full bg-muted-foreground" />
                            ) : (
                              <Bot className="w-4 h-4 text-muted-foreground" />
                            )}
                            <span className="text-xs font-medium text-muted-foreground">
                              {message.agent || 'Assistant'}
                            </span>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {formatTimestamp(message.timestamp || new Date())}
                          </span>
                        </div>
                      )}
                      
                      {/* Message content */}
                      <div className={cn(
                        "text-sm leading-relaxed",
                        isUser && "text-primary-foreground"
                      )}>
                        {message.content}
                      </div>
                      
                      {/* User message timestamp */}
                      {isUser && (
                        <div className="text-xs text-primary-foreground/70 mt-2 text-right">
                          {formatTimestamp(message.timestamp || new Date())}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              
              {/* Active HITL Request */}
              {shouldShowHITL && (
                <div className={cn(
                  "mb-4",
                  isExpanded ? "px-8" : "px-4"
                )}>
                  <div className="p-4 rounded-lg border bg-amber-50 border-amber-200 ml-auto max-w-[95%]">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        {getRoleIcon(activeRequest.agentName, LocalRole.Assistant)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-semibold text-sm">
                            {activeRequest.agentName}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {formatTimestamp(new Date(activeRequest.timestamp))}
                          </div>
                        </div>
                        <div className="text-sm text-foreground/90 prose prose-sm max-w-none">
                          <div className="space-y-3">
                            <div>🤖 {activeRequest.agentName} is requesting human approval</div>
                            <HITLApprovalComponent
                              agentName={activeRequest.agentName}
                              decision={activeRequest.decision}
                              context={activeRequest.context}
                              priority={activeRequest.priority}
                              onApprove={() => {
                                resolveRequest(activeRequest.id, 'approved', 'Approved from chat');
                              }}
                              onReject={() => {
                                resolveRequest(activeRequest.id, 'rejected', 'Rejected from chat');
                              }}
                              onModify={(feedback) => {
                                resolveRequest(activeRequest.id, 'modified', feedback);
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {copilotIsLoading && (
                <div className="flex justify-start">
                  <div className="max-w-[80%] rounded-lg px-4 py-3 bg-card border border-border text-foreground mr-12">
                    <div className="flex items-center gap-2 mb-2">
                      <Bot className="w-4 h-4 text-muted-foreground" />
                      <span className="text-xs font-medium text-muted-foreground">
                        BotArmy Assistant
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Thinking...
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} className="h-1" />
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="border-t border-border">
        <ChatInput onSend={handleSendMessage} isLoading={copilotIsLoading} hasActiveHITL={!!activeRequest} />
      </div>
    </div>
  );
};

export default CustomCopilotChat;

// Helper to get agent icon
const getRoleIcon = (agentName: string, role: LocalRole) => {
  const agent = AGENT_DEFINITIONS.find(a => a.name === agentName);
  if (agent) {
    const Icon = agent.icon;
    return <Icon className="w-5 h-5" />;
  }
  return role === LocalRole.User ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />;
};