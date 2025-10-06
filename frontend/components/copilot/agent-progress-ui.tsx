/**
 * Generative UI Components for Agent Progress Tracking
 *
 * Uses CopilotKit's Generative UI to render dynamic agent state and progress.
 */

"use client";

import { useCoAgent } from "@copilotkit/react-core";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Circle, Clock, AlertCircle } from "lucide-react";

interface AgentTask {
  id: string;
  description: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  progress: number;
}

interface AgentState {
  agent_name: string;
  current_task?: string;
  tasks: AgentTask[];
  overall_progress: number;
  status: "idle" | "working" | "completed" | "error";
}

/**
 * Agent Progress Card - Renders agent state with real-time updates
 */
export function AgentProgressCard({ agentName }: { agentName: string }) {
  const { state, setState } = useCoAgent<AgentState>({
    name: agentName,
    initialState: {
      agent_name: agentName,
      tasks: [],
      overall_progress: 0,
      status: "idle"
    }
  });

  const getStatusIcon = (status: AgentTask["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "in_progress":
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: AgentState["status"]) => {
    const variants = {
      idle: "secondary",
      working: "default",
      completed: "success",
      error: "destructive"
    };
    return variants[status] || "secondary";
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="capitalize">{state.agent_name} Agent</CardTitle>
          <Badge variant={getStatusBadge(state.status) as any}>
            {state.status}
          </Badge>
        </div>
        {state.current_task && (
          <CardDescription>{state.current_task}</CardDescription>
        )}
      </CardHeader>

      <CardContent>
        {/* Overall Progress */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-muted-foreground">Overall Progress</span>
            <span className="font-medium">{state.overall_progress}%</span>
          </div>
          <Progress value={state.overall_progress} className="h-2" />
        </div>

        {/* Task List */}
        <div className="space-y-2">
          {state.tasks.map((task) => (
            <div key={task.id} className="flex items-center gap-2 p-2 rounded-md bg-muted/50">
              {getStatusIcon(task.status)}
              <div className="flex-1">
                <p className="text-sm font-medium">{task.description}</p>
                {task.status === "in_progress" && (
                  <Progress value={task.progress} className="h-1 mt-1" />
                )}
              </div>
              {task.status === "in_progress" && (
                <span className="text-xs text-muted-foreground">{task.progress}%</span>
              )}
            </div>
          ))}
        </div>

        {state.tasks.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">
            No tasks yet. Agent is ready to work.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Multi-Agent Dashboard - Shows all agents' progress
 */
export function MultiAgentDashboard() {
  const agents = ["analyst", "architect", "coder"];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {agents.map((agent) => (
        <AgentProgressCard key={agent} agentName={agent} />
      ))}
    </div>
  );
}
