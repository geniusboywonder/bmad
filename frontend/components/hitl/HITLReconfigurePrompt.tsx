
"use client";

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

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

  const handleContinue = () => {
    onContinue({ newLimit: limit, newStatus: isEnabled });
  };

  return (
    <div className="p-4 border rounded-lg bg-muted/50 my-4">
      <p className="font-semibold text-amber-600">Agent Action Limit Reached</p>
      <p className="text-sm text-muted-foreground mb-4">
        The agent has used its allocated actions. Please reconfigure and continue, or stop the current operation.
      </p>
      <div className="flex flex-col sm:flex-row sm:items-center sm:gap-4 gap-y-4">
        <div className="flex items-center gap-2">
          <Label htmlFor="hitl-limit">Set Counter:</Label>
          <Input
            id="hitl-limit"
            type="number"
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value, 10) || 0)}
            className="w-20"
          />
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="hitl-toggle">Toggle HITL:</Label>
          <Switch
            id="hitl-toggle"
            checked={isEnabled}
            onCheckedChange={setIsEnabled}
          />
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <Button onClick={handleContinue}>Continue</Button>
          <Button onClick={onStop} variant="destructive">
            Stop
          </Button>
        </div>
      </div>
    </div>
  );
};
