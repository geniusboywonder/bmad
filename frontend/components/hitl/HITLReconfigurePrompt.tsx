
"use client";

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle } from 'lucide-react';

interface HITLReconfigurePromptProps {
  initialLimit: number;
  initialStatus: boolean;
  onContinue: (response: { newLimit: number; newStatus: boolean }) => void;
  onStop: () => void;
}

export const HITLReconfigurePrompt = ({
  initialLimit,
  initialStatus,
  onContinue,
  onStop,
}: HITLReconfigurePromptProps) => {
  const [limit, setLimit] = useState(initialLimit);
  const [isEnabled, setIsEnabled] = useState(initialStatus);
  const [decision, setDecision] = useState<"approved" | "rejected" | null>(null);
  const isLocked = decision !== null;

  const handleApprove = async () => {
    if (isLocked) {
      return;
    }
    setDecision("approved");
    try {
      await Promise.resolve(onContinue({ newLimit: limit, newStatus: isEnabled }));
    } catch (error) {
      console.error("[HITLReconfigurePrompt] Failed to approve HITL settings", error);
      setDecision(null);
    }
  };

  const handleReject = async () => {
    if (isLocked) {
      return;
    }
    setDecision("rejected");
    try {
      await Promise.resolve(onStop());
    } catch (error) {
      console.error("[HITLReconfigurePrompt] Failed to reject HITL settings", error);
      setDecision(null);
    }
  };

  return (
    <div
      className="border rounded-lg bg-background shadow-sm overflow-hidden max-w-2xl focus:outline-none"
      data-hitl-prompt="current"
      tabIndex={-1}
    >
      {/* Header with Counter and HITL Toggle */}
      <div className="flex items-center justify-between gap-4 px-4 py-2 bg-muted/50 border-b">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-muted-foreground">Counter:</span>
          <Input
            type="number"
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value, 10) || 0)}
            disabled={isLocked}
            className="w-20 h-8"
          />
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-muted-foreground">Enable HITL:</span>
          <Switch
            checked={isEnabled}
            onCheckedChange={setIsEnabled}
            disabled={isLocked}
            className="data-[state=checked]:bg-primary"
          />
        </div>
      </div>

      {/* Task Heading with Badges */}
      <div className="px-4 py-3 space-y-2">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-orchestrator/10 text-orchestrator border-orchestrator/20">
            Agent
          </Badge>
          <Badge variant="destructive" className="gap-1">
            <AlertTriangle className="w-3 h-3" />
            HITL
          </Badge>
        </div>

        {/* Task Description (max 2 lines) */}
        <p className="text-sm text-foreground line-clamp-2">
          Agent action limit reached. Reconfigure HITL settings to continue or stop the current operation.
        </p>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 pt-2">
          {decision === null ? (
            <>
              <Button
                onClick={handleApprove}
                size="sm"
                className="bg-tester text-white hover:bg-tester/90"
              >
                Approve
              </Button>
              <Button
                onClick={handleReject}
                size="sm"
                variant="destructive"
              >
                Reject
              </Button>
            </>
          ) : decision === "approved" ? (
            <Button
              size="sm"
              className="bg-tester text-white"
              disabled
            >
              Approved
            </Button>
          ) : (
            <Button
              size="sm"
              variant="destructive"
              disabled
            >
              Rejected
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
