"use client";

import React, { useMemo, useState } from 'react';
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getAgentBadgeClasses, getStatusBadgeClasses } from "@/lib/utils/badge-utils";
import { AlertTriangle, Check, X, Edit3 } from "lucide-react";
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

export const InlineHITLApproval: React.FC<InlineHITLApprovalProps> = ({
  request,
  className
}) => {
  const { resolveRequest } = useHITLStore();
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const priorityStatus = request.priority === 'urgent' ? 'error' : request.priority === 'high' ? 'waiting' : request.priority === 'medium' ? 'wip' : 'planned';
  const isActionable = useMemo(() => request.id?.startsWith('hitl-') ?? false, [request.id]);
  const statusLabel = useMemo(() => {
    if (request.status === 'approved') return 'Approved';
    if (request.status === 'rejected') return 'Rejected';
    if (request.status === 'modified') return 'Modified';
    return 'Pending';
  }, [request.status]);

  const currentStatusBadge = useMemo(() => {
    if (request.status === 'approved') return getStatusBadgeClasses('done');
    if (request.status === 'rejected') return getStatusBadgeClasses('error');
    if (request.status === 'modified') return getStatusBadgeClasses('waiting');
    return getStatusBadgeClasses('wip');
  }, [request.status]);

  const hasDecision = request.status !== 'pending';

  const actionLabel = useMemo(() => {
    if (request.status === 'approved') return 'Continue';
    if (request.status === 'rejected') return 'Stop';
    if (request.status === 'modified') return 'Redirect';
    return null;
  }, [request.status]);

  const handleResolve = async (status: 'approved' | 'rejected' | 'modified', defaultResponse: string) => {
    if (!isActionable) {
      console.warn('[InlineHITLApproval] Attempted to resolve a request that is not yet actionable.', {
        requestId: request.id,
        approvalId: request.context?.approvalId
      });
      setError('Approval request is still synchronizing. Please wait a moment and try again.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      let responseMessage = defaultResponse;

      if (status === 'rejected' || status === 'modified') {
        const promptLabel = status === 'rejected'
          ? 'Provide a reason for rejecting this request:'
          : 'Describe the required modifications for the agent:';

        const userInput = window.prompt(promptLabel, defaultResponse);

        // If user cancels input, abort the action
        if (userInput === null) {
          setIsProcessing(false);
          return;
        }

        responseMessage = userInput.trim() === '' ? defaultResponse : userInput.trim();
      }

      await resolveRequest(request.id, status, responseMessage);
    } catch (err) {
      console.error('[InlineHITLApproval] Failed to resolve HITL request', err);
      setError('Action failed. Please try again or review the HITL dashboard.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApprove = () => handleResolve('approved', 'Request approved from inline HITL control.');
  const handleReject = () => handleResolve('rejected', 'Request rejected from inline HITL control.');
  const handleModify = () => handleResolve('modified', 'Please adjust the plan accordingly.');

  return (
    <span className={cn(
      "inline-flex flex-wrap items-center gap-2 p-2 border rounded-md",
      getAgentBadgeClasses('hitl'),
      className
    )}>
      <Badge variant="destructive" size="sm" className="gap-1">
        <AlertTriangle className="w-2.5 h-2.5" />
        HITL Approval Required
      </Badge>
      <Badge variant="muted" size="sm" className={getAgentBadgeClasses(request.agentName)}>
        {request.agentName}
      </Badge>
      <Badge variant="muted" size="sm" className={getStatusBadgeClasses(priorityStatus)}>
        {request.priority}
      </Badge>
      <Badge variant="outline" size="sm" className={currentStatusBadge}>
        {statusLabel}
      </Badge>
      <span className="text-muted-foreground text-xs">
        {new Date(request.timestamp).toLocaleTimeString()}
      </span>
      <span className="text-foreground text-sm">
        Task: {request.context?.requestData?.instructions}
      </span>
      {!hasDecision ? (
        <>
          <Button
            size="sm"
            className="bg-tester text-white hover:bg-tester/90"
            disabled={isProcessing || !isActionable}
            onClick={handleApprove}
          >
            <Check className="mr-1 h-3 w-3" />
            Approve
          </Button>
          <Button
            variant="destructive"
            size="sm"
            disabled={isProcessing || !isActionable}
            onClick={handleReject}
          >
            <X className="mr-1 h-3 w-3" />
            Reject
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="text-analyst border-analyst hover:bg-analyst/10"
            disabled={isProcessing || !isActionable}
            onClick={handleModify}
          >
            <Edit3 className="mr-1 h-3 w-3" />
            Modify
          </Button>
          {!isActionable && (
            <span className="text-xs text-muted-foreground">
              Syncing approval request…
            </span>
          )}
        </>
      ) : (
        <span className="text-xs font-medium text-foreground bg-muted px-2 py-1 rounded-md">
          Selected Action: {actionLabel}{request.response ? ` — ${request.response}` : ''}
        </span>
      )}
      {error ? (
        <span className="text-xs text-destructive">
          {error}
        </span>
      ) : null}
    </span>
  );
};
