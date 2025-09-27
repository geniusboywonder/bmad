"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Edit3,
  Send,
  DollarSign,
  Timer
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useHITLStore } from '@/lib/stores/hitl-store';

interface HITLRequest {
  id: string;
  agentName: string;
  decision: string;
  context: any;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  timestamp: Date;
  status: 'pending' | 'approved' | 'rejected' | 'modified';
  response?: string;
  estimatedCost?: number;
  estimatedTime?: string;
}

interface InlineHITLApprovalProps {
  request: HITLRequest;
  className?: string;
}

const priorityConfig = {
  low: {
    color: 'bg-green-50 border-green-200 text-green-800',
    icon: CheckCircle,
    iconColor: 'text-green-600'
  },
  medium: {
    color: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    icon: Clock,
    iconColor: 'text-yellow-600'
  },
  high: {
    color: 'bg-orange-50 border-orange-200 text-orange-800',
    icon: AlertTriangle,
    iconColor: 'text-orange-600'
  },
  urgent: {
    color: 'bg-red-50 border-red-200 text-red-800',
    icon: AlertTriangle,
    iconColor: 'text-red-600'
  }
};

export const InlineHITLApproval: React.FC<InlineHITLApprovalProps> = ({
  request,
  className
}) => {
  const { resolveRequest } = useHITLStore();
  const [isExpanded, setIsExpanded] = useState(false);
  const [response, setResponse] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const config = priorityConfig[request.priority];
  const PriorityIcon = config.icon;

  // Extract user-friendly task description
  const getTaskDescription = () => {
    const context = request.context;

    // Try to get the original user instructions from request data
    if (context?.requestData?.instructions) {
      const instructions = context.requestData.instructions;
      const agentType = context?.agentType || request.agentName;

      // Create user-friendly description based on agent type and user request
      return `The ${agentType} agent wants to: "${instructions}"`;
    }

    // Fallback: create meaningful description from agent type
    const agentType = context?.agentType || request.agentName;

    // Agent-specific descriptions for what they typically do
    const agentActions = {
      'analyst': 'analyze requirements and create project specifications',
      'architect': 'design system architecture and technical specifications',
      'developer': 'write code and implement features',
      'tester': 'create and run tests to ensure quality',
      'deployer': 'deploy the application to production',
      'project_manager': 'coordinate project activities and manage timelines'
    };

    const action = agentActions[agentType?.toLowerCase()] || 'perform assigned tasks';
    return `The ${agentType} agent wants to: ${action}`;
  };

  // Get user-friendly status text
  const getStatusText = (status: string) => {
    switch (status) {
      case 'approved': return 'Request Approved';
      case 'rejected': return 'Request Rejected';
      case 'modified': return 'Request Modified';
      default: return 'Request Pending';
    }
  };

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      await resolveRequest(request.id, 'approved', response || 'Approved');
    } catch (error) {
      console.error('Failed to approve HITL request:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      const rejectionReason = response || 'Rejected without reason';
      await resolveRequest(request.id, 'rejected', rejectionReason);
    } catch (error) {
      console.error('Failed to reject HITL request:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleModify = async () => {
    if (!response.trim()) return;

    setIsSubmitting(true);
    try {
      await resolveRequest(request.id, 'modified', response);
      // Could trigger backend API call here for modifications
    } finally {
      setIsSubmitting(false);
    }
  };

  if (request.status !== 'pending') {
    // Show resolved status
    const statusConfig = {
      approved: { color: 'bg-green-50 border-green-200 text-green-800', icon: CheckCircle },
      rejected: { color: 'bg-red-50 border-red-200 text-red-800', icon: XCircle },
      modified: { color: 'bg-blue-50 border-blue-200 text-blue-800', icon: Edit3 }
    };

    const statusInfo = statusConfig[request.status];
    const StatusIcon = statusInfo.icon;

    return (
      <div className={cn('border rounded-lg p-3', statusInfo.color, className)}>
        <div className="flex items-center gap-2 mb-2">
          <StatusIcon className="w-4 h-4" />
          <span className="text-sm font-medium">
            {getStatusText(request.status)}
          </span>
          <Badge variant="outline" className="text-xs">
            {request.agentName}
          </Badge>
        </div>
        <p className="text-sm">{getTaskDescription()}</p>
        {request.response && (
          <div className="mt-2 pt-2 border-t border-current border-opacity-20">
            <p className="text-xs font-medium">Response:</p>
            <p className="text-sm">{request.response}</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={cn(
      'border rounded-lg p-4 transition-all duration-200 shadow-sm backdrop-blur-sm',
      config.color,
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <PriorityIcon className={cn('w-4 h-4', config.iconColor)} />
          <span className="text-sm font-medium">HITL Approval Required</span>

          {/* Agent Badge using centralized system */}
          <Badge
            variant="muted"
            size="sm"
            className={cn('text-[10px] px-1 py-0.5 h-4', getAgentBadgeClasses(request.agentName))}
          >
            {request.agentName}
          </Badge>

          {/* Priority Badge using centralized severity system */}
          <Badge
            variant="muted"
            size="sm"
            className={cn(
              'text-[10px] px-1 py-0.5 h-4 font-medium',
              request.priority === 'urgent' ? getStatusBadgeClasses('error') :
              request.priority === 'high' ? 'text-orange-600 border-orange-600/20' :
              request.priority === 'medium' ? getStatusBadgeClasses('pending') :
              getStatusBadgeClasses('completed')
            )}
          >
            {request.priority.toUpperCase()}
          </Badge>
        </div>
        <div className="text-xs text-current/70 font-mono">
          {new Date(request.timestamp).toLocaleTimeString()}
        </div>
      </div>

      {/* Task details */}
      <div className="mb-3">
        <p className="text-sm font-medium mb-1 opacity-90">Task Details:</p>
        <p className="text-sm bg-background/50 backdrop-blur-sm rounded px-3 py-2 border border-current/10">
          {getTaskDescription()}
        </p>
      </div>

      {/* Context information */}
      {(request.estimatedCost || request.estimatedTime) && (
        <div className="flex gap-4 mb-3">
          {request.estimatedCost && (
            <Badge variant="muted" size="sm" className="text-[10px] px-2 py-1 h-5 gap-1">
              <DollarSign className="w-3 h-3" />
              Est. Cost: ${request.estimatedCost}
            </Badge>
          )}
          {request.estimatedTime && (
            <Badge variant="muted" size="sm" className="text-[10px] px-2 py-1 h-5 gap-1">
              <Timer className="w-3 h-3" />
              Est. Time: {request.estimatedTime}
            </Badge>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2 mb-3">
        <Button
          size="sm"
          onClick={handleApprove}
          disabled={isSubmitting}
          className="bg-tester hover:bg-tester/90 text-white shadow-sm transition-all duration-150 hover:scale-105"
        >
          <CheckCircle className="w-3 h-3 mr-1" />
          Approve
        </Button>

        <Button
          size="sm"
          variant="destructive"
          onClick={handleReject}
          disabled={isSubmitting}
          className="shadow-sm transition-all duration-150 hover:scale-105"
        >
          <XCircle className="w-3 h-3 mr-1" />
          Reject
        </Button>

        <Button
          size="sm"
          variant="outline"
          onClick={() => setIsExpanded(!isExpanded)}
          className="border-current text-current hover:bg-current/10 shadow-sm transition-all duration-150 hover:scale-105"
        >
          <Edit3 className="w-3 h-3 mr-1" />
          {isExpanded ? 'Cancel' : 'Modify'}
        </Button>
      </div>

      {/* Expanded response area */}
      {isExpanded && (
        <div className="space-y-3 pt-3 border-t border-current/20 animate-in slide-in-from-top-2 duration-200">
          <label className="text-xs font-medium block opacity-90">
            Response / Modification Instructions:
          </label>
          <Textarea
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            placeholder="Provide feedback, modifications, or rejection reason..."
            className="min-h-[60px] text-sm bg-background/70 backdrop-blur-sm border-current/30 focus:border-current/50 transition-colors duration-150"
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={handleModify}
              disabled={!response.trim() || isSubmitting}
              className="bg-analyst hover:bg-analyst/90 text-white shadow-sm transition-all duration-150 hover:scale-105"
            >
              <Send className="w-3 h-3 mr-1" />
              Send Response
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};