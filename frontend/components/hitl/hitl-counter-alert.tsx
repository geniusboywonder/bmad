"use client";

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useHITLStore } from "@/lib/stores/hitl-store";

interface HitlCounterAlertProps {
  projectId?: string;
  counterTotal: number;
  counterRemaining: number;
  hitlEnabled: boolean;
  locked?: boolean;
}

export const HitlCounterAlert: React.FC<HitlCounterAlertProps> = ({
  projectId,
  counterTotal,
  counterRemaining,
  hitlEnabled,
  locked = false,
}) => {
  const {
    setHitlEnabled,
    continueAutoApprovals,
    stopAutoApprovals,
    updateCounterLimit,
  } = useHITLStore((state) => ({
    setHitlEnabled: state.setHitlEnabled,
    continueAutoApprovals: state.continueAutoApprovals,
    stopAutoApprovals: state.stopAutoApprovals,
    updateCounterLimit: state.updateCounterLimit,
  }));

  const settingsForProject = useHITLStore(
    (state) => (projectId ? state.settings[projectId] : undefined)
  );

  const effectiveEnabled = settingsForProject?.enabled ?? hitlEnabled;
  const effectiveTotal = settingsForProject?.counterTotal ?? counterTotal;
  const effectiveRemaining = settingsForProject?.counterRemaining ?? counterRemaining;
  const effectiveLocked = settingsForProject?.locked ?? locked;

  const [draftCounter, setDraftCounter] = useState<number>(effectiveTotal);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [localEnabled, setLocalEnabled] = useState<boolean>(effectiveEnabled);

  useEffect(() => {
    setDraftCounter(effectiveTotal);
  }, [effectiveTotal]);

  useEffect(() => {
    setLocalEnabled(effectiveEnabled);
  }, [effectiveEnabled]);

  const disabled = !projectId || isProcessing;

  const handleToggle = async (checked: boolean) => {
    if (!projectId) return;
    setLocalEnabled(checked);
    setIsProcessing(true);
    try {
      await setHitlEnabled(projectId, checked);
    } catch (error) {
      console.error("[HitlCounterAlert] Failed to toggle HITL", error);
      setLocalEnabled(effectiveEnabled);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleContinue = async () => {
    if (!projectId) return;
    setIsProcessing(true);
    try {
      await continueAutoApprovals(projectId, draftCounter);
    } catch (error) {
      console.error("[HitlCounterAlert] Failed to continue auto approvals", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStop = async () => {
    if (!projectId) return;
    setIsProcessing(true);
    try {
      await stopAutoApprovals(projectId);
    } catch (error) {
      console.error("[HitlCounterAlert] Failed to stop auto approvals", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCounterChange = (value: string) => {
    const parsed = parseInt(value, 10);
    if (!Number.isNaN(parsed) && parsed >= 0) {
      setDraftCounter(parsed);
    } else if (value === "") {
      setDraftCounter(0);
    }
  };

  const applyCounterUpdate = async () => {
    if (!projectId) return;
    setIsProcessing(true);
    try {
      await updateCounterLimit(projectId, draftCounter, true);
    } catch (error) {
      console.error("[HitlCounterAlert] Failed to update counter limit", error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="space-y-2">
        <Label className="text-sm font-medium">Set the HITL Counter</Label>
        <div className="flex items-center gap-3">
          <Input
            type="number"
            min={0}
            value={draftCounter}
            onChange={(event) => handleCounterChange(event.target.value)}
            disabled={disabled}
            className="w-24"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={applyCounterUpdate}
            disabled={disabled}
          >
            Apply
          </Button>
          <span className="text-xs text-muted-foreground">
            Remaining auto approvals: <strong>{effectiveRemaining}</strong>
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Label className="text-sm font-medium">Toggle HITL</Label>
        <Switch
          checked={localEnabled}
          onCheckedChange={handleToggle}
          disabled={disabled}
        />
        <span className="text-xs text-muted-foreground">
          {localEnabled ? "Yes" : "No"}
        </span>
      </div>

      {effectiveLocked && (
        <div className="text-xs text-muted-foreground">
          HITL auto approvals are paused until you continue or adjust the counter.
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <Button
          size="sm"
          onClick={handleContinue}
          disabled={disabled}
          className="bg-primary text-primary-foreground hover:bg-primary/90"
        >
          Continue
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={handleStop}
          disabled={disabled}
        >
          Stop
        </Button>
      </div>
    </div>
  );
};
