"use client"

import { useState } from "react"
import { MainLayout } from "@/components/main-layout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { getStatusBadgeClasses } from "@/lib/utils/badge-utils"
import { RefreshCw, Filter, Search } from "lucide-react"
import { useAgentStore } from "@/lib/stores/agent-store"
import { Progress } from "@/components/ui/progress"

type TaskStatus = "Queued" | "WIP" | "Waiting" | "Error" | "Done" | "Unknown";

const getStatusInfo = (status: TaskStatus) => {
  switch (status) {
    case "Done":
      return { text: 'Done', color: "bg-blue-500/20 text-blue-400 border-blue-500/30" };
    case "WIP":
      return { text: 'WIP', color: "bg-green-500/20 text-green-400 border-green-500/30" };
    case "Error":
      return { text: 'Error', color: "bg-red-500/20 text-red-400 border-red-500/30" };
    case "Waiting":
      return { text: 'Waiting', color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" };
    case "Queued":
      return { text: 'Queued', color: "bg-gray-500/20 text-gray-400 border-gray-500/30" };
    default:
      return { text: 'Unknown', color: "bg-gray-500/20 text-gray-400 border-gray-500/30" };
  }
}

const sdlcTasks = [
  { name: "Analyst", description: "Analyzing project brief and creating requirements." },
  { name: "Architect", description: "Designing technical architecture." },
  { name: "Developer", description: "Writing application code." },
  { name: "Tester", description: "Creating a test plan." },
  { name: "Deployer", description: "Generating deployment script." },
];

export default function TasksPage() {
  const { agents } = useAgentStore()
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("All")

  const agentMap = new Map(agents.map(agent => [agent.name, agent]));

  const tasks = sdlcTasks.map((task, index) => {
    const agent = agentMap.get(task.name);
    let status: TaskStatus = "Queued";
    let progress = 0;
    if (agent) {
      switch (agent.status) {
        case "active":
        case "working":
          status = "WIP";
          progress = agent.progress_current && agent.progress_total ? (agent.progress_current / agent.progress_total) * 100 : 50;
          break;
        case "paused":
          status = "Waiting";
          break;
        case "error":
          status = "Error";
          break;
        case "completed":
          status = "Done";
          progress = 100;
          break;
        case "idle":
        default:
          status = "Queued";
          break;
      }
    }

    return {
      id: index,
      name: task.name,
      description: task.description,
      status: status,
      agent: agent || null,
      progress: progress,
      startTime: agent?.lastActivity || new Date(),
    };
  });

  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      task.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === "All" || task.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <MainLayout>
      <div className="p-6">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Tasks</h1>
            <p className="text-muted-foreground">Monitor and track all agent tasks in real-time</p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search tasks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-background border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="All">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="in-progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-background border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="All">All Statuses</option>
            <option value="Queued">Queued</option>
            <option value="WIP">WIP</option>
            <option value="Waiting">Waiting</option>
            <option value="Done">Done</option>
            <option value="Error">Error</option>
          </select>
        </div>

        {/* Tasks Table */}
        <div className="border border-border rounded-lg overflow-hidden mb-4">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted/50 border-b border-border">
                <tr>
                  <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground">Task</th>
                  <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground w-[120px]">Status</th>
                  <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground w-[200px]">Progress</th>
                  <th className="text-left py-3 px-4 font-medium text-sm text-muted-foreground">Last Update</th>
                </tr>
              </thead>
              <tbody>
                {filteredTasks.map((task, index) => {
                  const statusInfo = getStatusInfo(task.status);
                  return (
                    <tr
                      key={task.id}
                      className={`border-b border-border hover:bg-muted/30 transition-colors ${
                        index === filteredTasks.length - 1 ? "border-b-0" : ""
                      }`}
                    >
                      <td className="py-3 px-4">
                        <div className="font-medium text-foreground">{task.name}</div>
                        <div className="text-sm text-muted-foreground">{task.description}</div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="muted" size="sm" className={`${statusInfo.color} font-medium`}>
                          {statusInfo.text}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        <Progress value={task.progress} className="h-2" />
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-muted-foreground text-sm">{new Date(task.startTime).toLocaleString()}</span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Results Summary */}
        <div className="text-sm text-muted-foreground">
          Showing {filteredTasks.length} of {tasks.length} tasks
        </div>
      </div>
    </MainLayout>
  )
}
