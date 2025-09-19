"use client";

import React from 'react';
import { Button } from '@/components/ui/button';
import { Pause, Play, Square } from 'lucide-react';
import { useAgentStore } from '@/lib/stores/agent-store';

interface KillSwitchControlsProps {
  agentName: string;
}

export const KillSwitchControls: React.FC<KillSwitchControlsProps> = ({ agentName }) => {
  const { pauseAgent, resumeAgent, resetAgent, agents } = useAgentStore();
  const agent = agents.find(a => a.name === agentName);

  const handlePause = () => {
    if (agent && agent.status !== 'paused') {
      pauseAgent(agentName);
    }
  };

  const handleResume = () => {
    if (agent && agent.status === 'paused') {
      resumeAgent(agentName);
    }
  };

  const handleReset = () => {
    resetAgent(agentName);
  };

  return (
    <div className="flex items-center gap-1">
      {agent?.status !== 'paused' ? (
        <Button
          variant="ghost"
          size="icon"
          onClick={handlePause}
          title="Pause agent execution"
          className="h-5 w-5 p-0 hover:bg-muted"
        >
          <Pause className="w-3 h-3" />
        </Button>
      ) : (
        <Button
          variant="ghost"
          size="icon"
          onClick={handleResume}
          title="Resume agent execution"
          className="h-5 w-5 p-0 hover:bg-muted"
        >
          <Play className="w-3 h-3" />
        </Button>
      )}

      <Button
        variant="ghost"
        size="icon"
        onClick={handleReset}
        title="Stop and reset agent"
        className="h-5 w-5 p-0 hover:bg-destructive/10 hover:text-destructive"
      >
        <Square className="w-3 h-3" />
      </Button>
    </div>
  );
};
