"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, AlertCircle, Loader, User, Clock, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Task } from "@/lib/types"

const statusConfig = {
    done: { icon: CheckCircle, color: "text-green-500", label: "Done" },
    wip: { icon: Loader, color: "text-blue-500 animate-spin", label: "In Progress" },
    todo: { icon: Clock, color: "text-gray-500", label: "To Do" },
    queued: { icon: AlertCircle, color: "text-gray-500", label: "Queued" },
    error: { icon: AlertTriangle, color: "text-red-500", label: "Error" },
    blocked: { icon: AlertTriangle, color: "text-orange-500", label: "Blocked" },
}

export function TasksList({ tasks = [] }: { tasks?: Task[] }) {
  return (
    <Card>
        <CardHeader>
            <CardTitle>Tasks</CardTitle>
            <CardDescription>
                A chronological list of tasks performed in this stage.
            </CardDescription>
        </CardHeader>
        <CardContent>
            <div className="space-y-4">
                {tasks && tasks.length > 0 ? (
                    tasks.map((task) => {
                        const statusConfigEntry = statusConfig[task.status as keyof typeof statusConfig]
                        if (!statusConfigEntry) {
                            console.error('Unknown task status:', task.status)
                            return null
                        }
                        const StatusIcon = statusConfigEntry.icon
                        
                        return (
                            <div key={task.id} className={cn(
                                "flex items-start gap-4 p-3 rounded-lg border",
                                task.status === 'blocked' && "border-orange-500 bg-orange-50",
                                task.status === 'error' && "border-red-500 bg-red-50"
                            )}>
                                <StatusIcon className={cn("w-5 h-5 mt-1", statusConfigEntry.color)} />
                                <div className="flex-1">
                                    <p className="font-medium">{task.name}</p>
                                    {task.description && (
                                        <p className="text-sm text-muted-foreground mt-1">{task.description}</p>
                                    )}
                                    <div className="text-sm text-muted-foreground flex items-center gap-4 mt-2">
                                        <div className="flex items-center gap-1">
                                            <User className="w-3 h-3" />
                                            <span>{task.assignedTo}</span>
                                        </div>
                                        {task.progress !== undefined && (
                                            <span>Progress: {task.progress}%</span>
                                        )}
                                        {task.priority && (
                                            <Badge variant={
                                                task.priority === 'urgent' ? 'destructive' :
                                                task.priority === 'high' ? 'default' :
                                                'secondary'
                                            }>
                                                {task.priority}
                                            </Badge>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )
                    })
                ) : (
                    <div className="text-center text-muted-foreground py-8">
                        <p>No tasks for this stage yet.</p>
                    </div>
                )}
            </div>
        </CardContent>
    </Card>
  )
}