"use client";

import React from 'react';
import { Bot, User, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { InlineHITLApproval } from '@/components/hitl/inline-hitl-approval';
import { useHITLStore } from '@/lib/stores/hitl-store';

interface ChatMessage {
  type: 'user' | 'agent' | 'system';
  agent: string;
  content: string | React.ReactNode;
  timestamp?: Date;
  requiresApproval?: boolean;
  estimatedCost?: number;
  estimatedTime?: string;
}

interface HITLChatMessageProps {
  message: ChatMessage;
  index: number;
}

export const HITLChatMessage: React.FC<HITLChatMessageProps> = ({
  message,
  index
}) => {
  const { requests, addRequest } = useHITLStore();
  const isUser = message.type === 'user';

  // Check if there's an existing HITL request for this message
  const relatedHITLRequest = requests.find(
    req => req.context?.messageIndex === index && req.agentName === message.agent
  );

  // Create HITL request if message requires approval and no request exists
  React.useEffect(() => {
    if (message.requiresApproval && !relatedHITLRequest && message.type === 'agent') {
      const priority = message.estimatedCost && message.estimatedCost > 10 ? 'high' :
                      message.estimatedTime && parseInt(message.estimatedTime) > 30 ? 'medium' : 'low';

      // Convert content to string if it's a React element
      const contentString = typeof message.content === 'string'
        ? message.content
        : `Agent ${message.agent} requires approval for action`;

      addRequest({
        agentName: message.agent,
        decision: contentString,
        context: {
          messageIndex: index,
          estimatedCost: message.estimatedCost,
          estimatedTime: message.estimatedTime,
          messageType: message.type
        },
        priority: priority as 'low' | 'medium' | 'high' | 'urgent'
      });
    }
  }, [message, index, relatedHITLRequest, addRequest]);

  return (
    <div className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn(
        'max-w-[80%] rounded-lg px-4 py-3 shadow-sm space-y-3',
        isUser
          ? 'bg-primary text-primary-foreground'
          : message.requiresApproval && relatedHITLRequest?.status === 'pending'
            ? 'bg-amber-50 border border-amber-200'
            : 'bg-card border'
      )}>
        {/* Message header */}
        <div className="flex items-center gap-2 mb-2">
          {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
          <span className="text-xs font-medium">{message.agent}</span>
          {message.requiresApproval && relatedHITLRequest?.status === 'pending' && (
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          )}
        </div>

        {/* Message content */}
        <div className="text-sm leading-relaxed">
          {message.content}
        </div>

        {/* HITL approval component */}
        {relatedHITLRequest && (
          <InlineHITLApproval
            request={{
              ...relatedHITLRequest,
              estimatedCost: message.estimatedCost,
              estimatedTime: message.estimatedTime
            }}
            className="mt-3"
          />
        )}
      </div>
    </div>
  );
};