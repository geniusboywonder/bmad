"use client";

import React from 'react';
import { Bot, User, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AGENT_DEFINITIONS } from '@/lib/agents/agent-definitions';
import { Button } from '@/components/ui/button';

// Local Role enum since it's not exported from lib/types
enum Role {
  User = 'User',
  Assistant = 'Assistant'
}

// Local timestamp formatting function
const formatTimestamp = (timestamp: Date | string): string => {
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

interface Message {
  id?: string;
  type?: 'user' | 'agent' | 'system';
  sender?: string;
  content: string | React.ReactNode;
  timestamp: Date | string;
  role?: Role;
  collapsed?: boolean;
}

interface MessageComponentProps {
  message: Message;
  isExpanded?: boolean;
  onToggleCollapse?: (id: string) => void;
}

const getRoleIcon = (agentName: string, role: Role) => {
  const agent = AGENT_DEFINITIONS.find(a => a.name === agentName);
  if (agent) {
    const Icon = agent.icon;
    return <Icon className="w-4 h-4" />;
  }
  return role === Role.User ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />;
};

const MessageComponent: React.FC<MessageComponentProps> = ({ 
  message, 
  isExpanded = false, 
  onToggleCollapse 
}) => {
  const getMessageIcon = () => {
    if (message.type === 'user' || message.role === Role.User) {
      return <User className="w-4 h-4" />;
    }
    if (message.type === 'system') {
      return <Bot className="w-4 h-4" />;
    }
    if (message.sender) {
      return getRoleIcon(message.sender, message.role || Role.Assistant);
    }
    return <Bot className="w-4 h-4" />;
  };

  const getMessageColors = () => {
    if (message.type === 'user' || message.role === Role.User) {
      return "bg-primary/10 border-primary/20 text-primary";
    }
    if (message.type === 'system') {
      return "bg-system/10 border-system/20 text-system";
    }
    return "bg-secondary border-border text-foreground";
  };

  const getSenderName = () => {
    if (message.sender) return message.sender;
    if (message.type === 'user' || message.role === Role.User) return 'User';
    if (message.type === 'system') return 'System';
    return 'Assistant';
  };

  const formatMessageTimestamp = (timestamp: Date | string) => {
    if (timestamp instanceof Date) {
      return formatTimestamp(timestamp);
    }
    if (typeof timestamp === 'string') {
      return formatTimestamp(new Date(timestamp));
    }
    return formatTimestamp(new Date());
  };

  return (
    <div className={cn(
      "p-3 rounded-lg border mb-2",
      getMessageColors(),
      isExpanded ? "mx-8" : "mx-4"
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getMessageIcon()}
          <span className="font-semibold text-sm">{getSenderName()}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-muted-foreground">
            {formatMessageTimestamp(message.timestamp)}
          </span>
          {onToggleCollapse && message.id && (
            <Button 
              size="icon" 
              variant="ghost" 
              className="h-6 w-6" 
              onClick={() => onToggleCollapse(message.id!)}
            >
              <ChevronDown 
                className={cn(
                  "w-4 h-4 transition-transform", 
                  !message.collapsed && "rotate-180"
                )} 
              />
            </Button>
          )}
        </div>
      </div>
      {(!message.collapsed || message.collapsed === undefined) && (
        <div className="pt-2 pl-6 text-sm whitespace-pre-wrap text-current">
          {message.content}
        </div>
      )}
    </div>
  );
};

export default MessageComponent;