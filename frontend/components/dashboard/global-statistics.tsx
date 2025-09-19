"use client"

import { useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"
import { CheckCircle, Loader, PauseCircle, XCircle } from "lucide-react"
import { useTaskStore } from "@/lib/stores/task-store"
import { Skeleton } from "@/components/ui/skeleton"

const statusMapping = {
    completed: { name: 'Done', color: '#22c55e', icon: CheckCircle },
    'in-progress': { name: 'In Progress', color: '#3b82f6', icon: Loader, className: "animate-spin" },
    pending: { name: 'Queued', color: '#6b7280', icon: PauseCircle },
    failed: { name: 'Error', color: '#ef4444', icon: XCircle },
}

export function GlobalStatistics() {
  const tasks = useTaskStore((state) => state.tasks)

  const stats = useMemo(() => {
    if (!tasks || tasks.length === 0) {
      return null
    }

    const statusBreakdown = Object.entries(statusMapping).map(([statusKey, statusInfo]) => ({
      name: statusInfo.name,
      value: tasks.filter(t => t.status === statusKey).length,
      color: statusInfo.color,
      icon: statusInfo.icon,
      className: statusInfo.className,
    }))

    return {
      totalTasks: tasks.length,
      statusBreakdown,
    }
  }, [tasks])

  if (!stats) {
    return (
      <Card>
        <CardHeader>
            <CardTitle>Global Statistics</CardTitle>
            <CardDescription>
                An overview of all tasks and system performance.
            </CardDescription>
        </CardHeader>
        <CardContent>
           <div className="space-y-4">
                <Skeleton className="h-8 w-1/2" />
                <div className="grid md:grid-cols-2 gap-4">
                    <Skeleton className="h-24 w-full" />
                    <Skeleton className="h-24 w-full" />
                    <Skeleton className="h-24 w-full" />
                    <Skeleton className="h-24 w-full" />
                </div>
           </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
        <CardHeader>
            <CardTitle>Global Statistics</CardTitle>
            <CardDescription>
                An overview of all tasks and system performance.
            </CardDescription>
        </CardHeader>
        <CardContent>
            <div className="grid md:grid-cols-2 gap-8">
                {/* Task Status Breakdown */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Task Status</h3>
                    <div className="grid grid-cols-2 gap-4">
                        {stats.statusBreakdown.map(s => {
                            const Icon = s.icon
                            return (
                                <Card key={s.name}>
                                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                        <CardTitle className="text-sm font-medium">{s.name}</CardTitle>
                                        <Icon className={`h-4 w-4 ${s.color} ${s.className || ''}`} />
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-2xl font-bold">{s.value}</div>
                                    </CardContent>
                                </Card>
                            )
                        })}
                    </div>
                </div>
                {/* Pie Chart */}
                <div className="flex flex-col items-center">
                     <h3 className="text-lg font-semibold mb-4">Task Distribution</h3>
                    <div style={{ width: '100%', height: 200 }}>
                        <ResponsiveContainer>
                            <PieChart>
                                <Pie
                                    data={stats.statusBreakdown}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {stats.statusBreakdown.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </CardContent>
    </Card>
  )
}
