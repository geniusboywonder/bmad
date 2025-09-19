"use client"

import { cn } from "@/lib/utils"
import { CheckCircle, Loader, XCircle, Clock } from "lucide-react"
import type { ProcessStage } from "@/lib/types"

interface ConfigurableStageProgressProps {
  stages: Pick<ProcessStage, 'id' | 'name' | 'status'>[];
  currentStageId: string;
}

const statusIcons = {
  done: <CheckCircle className="h-5 w-5 text-green-500" />,
  wip: <Loader className="h-5 w-5 animate-spin text-blue-500" />,
  queued: <Clock className="h-5 w-5 text-gray-400" />,
  error: <XCircle className="h-5 w-5 text-red-500" />,
  waiting: <Clock className="h-5 w-5 text-yellow-500" />,
};

export function ConfigurableStageProgress({ stages, currentStageId }: ConfigurableStageProgressProps) {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between">
        {stages.map((stage, index) => {
          const isCurrent = stage.id === currentStageId;
          const isCompleted = stage.status === 'done';
          const isWip = stage.status === 'wip';

          return (
            <div key={stage.id} className="flex items-center w-full">
              <div className="flex flex-col items-center">
                <div className={cn(
                  "flex items-center justify-center w-8 h-8 rounded-full border-2",
                  isCurrent ? "border-blue-500 bg-blue-100" : "border-gray-300",
                  isCompleted ? "border-green-500 bg-green-100" : ""
                )}>
                  {statusIcons[stage.status] || <Clock className="h-5 w-5 text-gray-400" />}
                </div>
                <p className={cn(
                  "text-xs mt-1 text-center",
                  isCurrent ? "font-bold text-blue-600" : "text-muted-foreground"
                )}>
                  {stage.name}
                </p>
              </div>

              {index < stages.length - 1 && (
                <div className={cn(
                  "flex-1 h-1",
                  isCompleted ? "bg-green-500" : "bg-gray-300"
                )} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
