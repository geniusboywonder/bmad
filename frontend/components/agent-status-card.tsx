"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { getStatusBadgeClasses } from "@/lib/utils/badge-utils"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { 
  Bot, 
  Play, 
  Pause, 
  Square, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Zap,
  Loader2
} from "lucide-react"
import { cn } from "@/lib/utils"

import { TypingIndicator } from "@/components/ui/typing-indicator"

export interface Agent {
  id: string
  name: string
  role: string
  status: "active" | "idle" | "working" | "error" | "offline" | "paused" | "completed"
  currentTask?: string
  lastActivity: Date | string
  tasksCompleted: number
  successRate: number
  progress?: number
  progress_stage?: string
  progress_current?: number
  progress_total?: number
  progress_estimated_time_remaining?: number
  is_thinking?: boolean
}

interface AgentStatusCardProps {
  agent: Agent
}

export function AgentStatusCard({ agent }: AgentStatusCardProps) {
  const getStatusInfo = (status: Agent['status']) => {
    switch (status) {
      case 'active':
      case 'working':
        return { text: 'WIP', color: 'bg-green-500', textColor: 'text-white' };
      case 'idle':
        return { text: 'Queued', color: 'bg-gray-400', textColor: 'text-white' };
      case 'paused':
        return { text: 'Waiting', color: 'bg-yellow-500', textColor: 'text-white' };
      case 'error':
        return { text: 'Error', color: 'bg-red-500', textColor: 'text-white' };
      case 'completed':
        return { text: 'Done', color: 'bg-blue-500', textColor: 'text-white' };
      default:
        return { text: 'Offline', color: 'bg-gray-300', textColor: 'text-gray-800' };
    }
  };

  const statusInfo = getStatusInfo(agent.status);

  const handlePauseResume = () => {
    const command = agent.status === 'paused' ? 'resume_agent' : 'pause_agent';
    // @ts-ignore
    websocketService.sendAgentCommand(agent.name, command);
    console.log(`${command} for agent:`, agent.name);
  };

  return (
    <Card className="h-full border">
      <CardContent className="p-2 flex flex-col justify-between h-full space-y-1">
        {/* Line 1: Agent Name and Play/Pause Button */}
        <div className="flex items-center justify-between">
          <span className="font-bold text-sm truncate" title={agent.name}>
            {agent.name}
          </span>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={handlePauseResume}
          >
            {agent.status === 'paused' ? (
              <Play className="h-4 w-4" />
            ) : (
              <Pause className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Line 2: Status and Task Description */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground overflow-hidden">
          <Badge variant="muted" size="sm" className={cn(statusInfo.color, statusInfo.textColor)}>
            {statusInfo.text}
          </Badge>
          <span className="truncate" title={agent.currentTask || 'No active task'}>
            {agent.currentTask || 'Idle'}
          </span>
        </div>

        {/* Line 3: Task Progress */}
        <div className="text-xs font-medium text-muted-foreground">
          {agent.progress_current !== undefined && agent.progress_total !== undefined ? (
            <span>
              Task: {agent.progress_current}/{agent.progress_total}
            </span>
          ) : (
            <span>&nbsp;</span> // Placeholder for alignment
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function AgentStatusCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <Avatar className="w-8 h-8">
              <div className="w-full h-full bg-muted rounded-full animate-pulse" />
            </Avatar>
            <div className="flex-1 min-w-0 space-y-1">
              <div className="h-4 bg-muted rounded w-3/4 animate-pulse" />
              <div className="h-3 bg-muted rounded w-1/2 animate-pulse" />
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between mb-3">
          <div className="h-5 bg-muted rounded w-1/4 animate-pulse" />
          <div className="h-3 bg-muted rounded w-1/4 animate-pulse" />
        </div>
        <div className="space-y-2">
          <div className="h-3 bg-muted rounded w-full animate-pulse" />
          <div className="h-3 bg-muted rounded w-5/6 animate-pulse" />
        </div>
      </CardContent>
    </Card>
  )
}