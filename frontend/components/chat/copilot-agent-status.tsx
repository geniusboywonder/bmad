"use client";

import { useAgentStore } from "@/lib/stores/agent-store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot, ClipboardCheck, DraftingCompass, Construction, TestTube2, Rocket } from "lucide-react";
import { getStatusBadgeClasses, getAgentBadgeClasses } from "@/lib/utils/badge-utils";
import { cn } from "@/lib/utils";

const getAgentIcon = (agentName: string) => {
  const agentLower = agentName.toLowerCase();
  if (agentLower.includes('analyst')) return <ClipboardCheck className="w-4 h-4" />;
  if (agentLower.includes('architect')) return <DraftingCompass className="w-4 h-4" />;
  if (agentLower.includes('developer')) return <Construction className="w-4 h-4" />;
  if (agentLower.includes('tester')) return <TestTube2 className="w-4 h-4" />;
  if (agentLower.includes('deployer')) return <Rocket className="w-4 h-4" />;
  return <Bot className="w-4 h-4" />;
};

export const CopilotAgentStatus = () => {
  const { agents } = useAgentStore();

  if (agents.length === 0) {
    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                <Bot className="w-5 h-5" />
                <span>Agent Status</span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <p className="text-muted-foreground">No agents active.</p>
            </CardContent>
        </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Bot className="w-5 h-5" />
          <span>Agent Status</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2">
          {agents.map((agent) => {
            // Status-based colors matching mockup
            const getStatusColor = (status: string) => {
              const statusLower = status.toLowerCase();
              if (['working', 'active', 'busy'].includes(statusLower)) {
                return 'bg-green-500/20 border-green-500/40 text-green-300';
              } else if (['waiting', 'pending'].includes(statusLower)) {
                return 'bg-yellow-500/20 border-yellow-500/40 text-yellow-300';
              } else if (['error', 'failed'].includes(statusLower)) {
                return 'bg-red-500/20 border-red-500/40 text-red-300';
              }
              return 'bg-muted/20 border-muted/40 text-muted-foreground';
            };

            return (
              <div key={agent.name} className={cn(
                "flex flex-col items-center gap-2 p-3 rounded-lg border text-center",
                getStatusColor(agent.status)
              )}>
                <div className="flex-shrink-0">
                  {getAgentIcon(agent.name)}
                </div>
                <div className="min-w-0 w-full">
                  <div className="font-medium text-xs truncate">{agent.name}</div>
                  <div className="text-xs opacity-80 truncate capitalize">{agent.status}</div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};
