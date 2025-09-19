"use client"

import { useAgentStore } from "@/lib/stores/agent-store"
import { MainLayout } from "@/components/main-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts"
import { TrendingUp, TrendingDown, Activity, Users, CheckCircle, Clock } from "lucide-react"

// Mock data for charts that require historical data
const taskTrendData = [
  { time: "00:00", tasks: 45 },
  { time: "04:00", tasks: 32 },
  { time: "08:00", tasks: 78 },
  { time: "12:00", tasks: 95 },
  { time: "16:00", tasks: 87 },
  { time: "20:00", tasks: 62 },
]

export default function AnalyticsPage() {
  const { agents } = useAgentStore();

  const totalTasks = agents.reduce((sum, agent) => sum + (agent.tasksCompleted || 0), 0);
  const totalSuccessRate = agents.length > 0 ? agents.reduce((sum, agent) => sum + (agent.successRate || 0), 0) / agents.length : 0;
  const activeAgents = agents.filter(agent => agent.status === 'active' || agent.status === 'working').length;
  const totalAgents = agents.length;

  const agentPerformanceData = agents.map(agent => ({
    agent: agent.name,
    completed: agent.tasksCompleted || 0,
    success: Math.round((agent.tasksCompleted || 0) * (agent.successRate || 0) / 100),
  }));

  return (
    <MainLayout>
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Analytics</h1>
            <p className="text-muted-foreground">Monitor system performance and agent metrics</p>
          </div>
          <Select defaultValue="24h">
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select time range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last Hour</SelectItem>
              <SelectItem value="24h">Last 24 Hours</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
              <SelectItem value="30d">Last 30 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalTasks}</div>
              <div className="flex items-center text-xs text-muted-foreground">
                Live data
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalSuccessRate.toFixed(1)}%</div>
              <div className="flex items-center text-xs text-muted-foreground">
                Live data
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activeAgents}/{totalAgents}</div>
              <div className="flex items-center text-xs text-muted-foreground">
                Live data
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">2.4s</div>
              <div className="flex items-center text-xs text-muted-foreground">
                Mock data
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Task Trend Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Task Trend (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={taskTrendData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="time" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "6px",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="tasks"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    dot={{ fill: "hsl(var(--primary))", strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Agent Performance Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Agent Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={agentPerformanceData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="agent" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "6px",
                    }}
                  />
                  <Bar dataKey="completed" fill="hsl(var(--primary))" />
                  <Bar dataKey="success" fill="hsl(var(--chart-2))" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Agent Status Details */}
        <Card>
          <CardHeader>
            <CardTitle>Agent Status Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agentPerformanceData.map((agent) => (
                <div key={agent.agent} className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <h4 className="font-medium">{agent.agent}</h4>
                    <p className="text-sm text-muted-foreground">{agent.completed} tasks completed</p>
                  </div>
                  <div className="text-right">
                    <Badge variant={agent.success === agent.completed ? "default" : "secondary"}>
                      {agent.completed > 0 ? Math.round((agent.success / agent.completed) * 100) : 0}% success
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
