"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Play, Pause } from "lucide-react"
import { cn } from "@/lib/utils"

// This interface represents a role from the process configuration, enriched with dynamic state.
export interface DynamicRole {
  name: string
  description: string
  status: "idle" | "working" | "completed" | "error" | "paused"
  currentTask?: string
  progress_current?: number
  progress_total?: number
}

interface DynamicRoleCardProps {
  role: DynamicRole
}

export function DynamicRoleCard({ role }: DynamicRoleCardProps) {
  const getStatusInfo = (status: DynamicRole['status']) => {
    switch (status) {
      case 'working':
        return { text: 'Working', color: 'bg-green-500', textColor: 'text-white' };
      case 'idle':
        return { text: 'Idle', color: 'bg-gray-400', textColor: 'text-white' };
      case 'paused':
        return { text: 'Paused', color: 'bg-yellow-500', textColor: 'text-white' };
      case 'error':
        return { text: 'Error', color: 'bg-red-500', textColor: 'text-white' };
      case 'completed':
        return { text: 'Completed', color: 'bg-blue-500', textColor: 'text-white' };
      default:
        return { text: 'Unknown', color: 'bg-gray-300', textColor: 'text-gray-800' };
    }
  };

  const statusInfo = getStatusInfo(role.status);

  const handlePauseResume = () => {
    // This functionality will need to be connected to the backend WebSocket service.
    // For now, it's a placeholder.
    console.log(`Pause/Resume clicked for role: ${role.name}`);
  };

  return (
    <Card className="h-full border">
      <CardContent className="p-2 flex flex-col justify-between h-full space-y-1">
        <div className="flex items-center justify-between">
          <span className="font-bold text-sm truncate" title={role.name}>
            {role.name}
          </span>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={handlePauseResume}
          >
            {role.status === 'paused' ? (
              <Play className="h-4 w-4" />
            ) : (
              <Pause className="h-4 w-4" />
            )}
          </Button>
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground overflow-hidden">
          <Badge className={cn("py-0 px-2 text-xs", statusInfo.color, statusInfo.textColor)}>
            {statusInfo.text}
          </Badge>
          <span className="truncate" title={role.currentTask || 'No active task'}>
            {role.currentTask || 'Idle'}
          </span>
        </div>

        <div className="text-xs font-medium text-muted-foreground">
          {role.progress_current !== undefined && role.progress_total !== undefined ? (
            <span>
              Task: {role.progress_current}/{role.progress_total}
            </span>
          ) : (
            <span>&nbsp;</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function DynamicRoleCardSkeleton() {
    return (
      <Card className="h-full border">
        <CardContent className="p-2 flex flex-col justify-between h-full space-y-1">
          <div className="flex items-center justify-between">
            <div className="h-4 bg-muted rounded w-1/2 animate-pulse" />
            <div className="h-6 w-6 bg-muted rounded animate-pulse" />
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-12 bg-muted rounded-full animate-pulse" />
            <div className="h-3 w-3/4 bg-muted rounded animate-pulse" />
          </div>
          <div className="h-3 w-1/4 bg-muted rounded animate-pulse" />
        </CardContent>
      </Card>
    );
  }
