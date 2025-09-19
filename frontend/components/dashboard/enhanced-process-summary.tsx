"use client"

import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { getStatusBadgeClasses, getAgentBadgeClasses } from "@/lib/utils/badge-utils"
import { Progress } from "@/components/ui/progress"
import {
  CheckCircle,
  Loader,
  Circle,
  ChevronRight,
  ChevronDown,
  AlertCircle,
  AlertTriangle,
  User,
  Database,
  FileCode,
  Component,
  Lock,
  Server,
  ClipboardCheck,
  DraftingCompass,
  Construction,
  TestTube2,
  Rocket,
  Clock,
  Play,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useProcessStore } from "@/lib/stores/process-store"
import { useConversationStore } from "@/lib/stores/conversation-store"
import { useArtifactScaffoldingStore } from "@/lib/stores/artifact-scaffolding-store"
import { Skeleton } from "@/components/ui/skeleton"

// Role-based Icon Mapping
const getRoleIcon = (agent: string, sizeAndColor = "w-6 h-6") => {
  const agentLower = agent.toLowerCase()
  if (agentLower.includes('analyst')) return <ClipboardCheck className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-analyst`} />
  if (agentLower.includes('architect')) return <DraftingCompass className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-architect`} />
  if (agentLower.includes('developer')) return <Construction className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-developer`} />
  if (agentLower.includes('tester')) return <TestTube2 className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-tester`} />
  if (agentLower.includes('deployer')) return <Rocket className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-deployer`} />
  return <User className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-muted-foreground`} />
}

// Status Overlay Icon
const getStatusIcon = (status: string, size = "w-3 h-3") => {
  switch (status) {
    case 'done':
      return <CheckCircle className={`${size} text-white`} />
    case 'wip':
      return <Play className={`${size} text-white`} />
    case 'queued':
      return <Clock className={`${size} text-white`} />
    case 'waiting':
      return <AlertTriangle className={`${size} text-white`} />
    default:
      return <Circle className={`${size} text-white`} />
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'done': return 'bg-tester'
    case 'wip': return 'bg-analyst' 
    case 'queued': return 'bg-muted'
    case 'waiting': return 'bg-amber'
    default: return 'bg-muted'
  }
}

const fallbackStagesData = [
  { 
    id: "analyze", 
    name: "Plan", 
    status: "done", 
    agentName: "Analyst", 
    tasks: [
      { name: "Requirements Doc", status: "done", id: "req-1" },
      { name: "User Stories", status: "done", id: "req-2" },
      { name: "Acceptance Criteria", status: "done", id: "req-3" }
    ],
    hitlRequired: false
  },
  { 
    id: "design", 
    name: "Design", 
    status: "wip", 
    agentName: "Architect", 
    tasks: [
      { name: "Database Schema", status: "wip", id: "design-1" },
      { name: "API Specification", status: "queued", id: "design-2" },
      { name: "System Architecture", status: "queued", id: "design-3" }
    ],
    hitlRequired: true
  },
  { 
    id: "build", 
    name: "Build", 
    status: "queued", 
    agentName: "Developer", 
    tasks: [
      { name: "Frontend Components", status: "queued", id: "dev-1" },
      { name: "Backend API", status: "queued", id: "dev-2" },
      { name: "Database Setup", status: "queued", id: "dev-3" }
    ],
    hitlRequired: false
  },
  { 
    id: "test", 
    name: "Test", 
    status: "queued", 
    agentName: "Tester", 
    tasks: [
      { name: "Unit Tests", status: "queued", id: "test-1" },
      { name: "Integration Tests", status: "queued", id: "test-2" }
    ],
    hitlRequired: false
  },
  { 
    id: "deploy", 
    name: "Deploy", 
    status: "queued", 
    agentName: "Deployer", 
    tasks: [
      { name: "Production Config", status: "queued", id: "deploy-1" },
      { name: "CI/CD Pipeline", status: "queued", id: "deploy-2" }
    ],
    hitlRequired: false
  },
]

export function EnhancedProcessSummary() {
  const processStages = useProcessStore((state) => state.stages)
  const { artifacts } = useArtifactScaffoldingStore()
  const currentProject = useConversationStore((state) => state.currentProject)
  const [selectedStage, setSelectedStage] = useState("design")
  const [expandedTasks, setExpandedTasks] = useState<string[]>([])
  
  // Use real process stages if available, otherwise fallback to mockup data
  const stages = processStages.length > 0 ? processStages.map(stage => ({
    id: stage.id,
    name: stage.name,
    status: stage.status,
    agentName: stage.agentName,
    tasks: stage.tasks,
    hitlRequired: stage.hitlRequired
  })) : fallbackStagesData
  
  // Generate description based on current project
  const getDescription = () => {
    if (currentProject) {
      return `Building ${currentProject}`
    }
    return "Workflow progress overview"
  }
  
  const currentStage = stages.find(stage => stage.id === selectedStage) || stages[0]
  const completedTasks = currentStage ? currentStage.tasks.filter(t => t.status === 'done').length : 0
  const totalTasks = currentStage ? currentStage.tasks.length : 0
  const progressPercentage = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0

  const stageArtifacts = Object.values(artifacts).filter(
    (artifact) => currentStage && artifact.stage.toLowerCase() === currentStage.name.toLowerCase()
  );

  const toggleTask = (taskId: string) => {
    setExpandedTasks(prev => 
      prev.includes(taskId) 
        ? prev.filter(id => id !== taskId)
        : [...prev, taskId]
    )
  }

  const renderSkeletons = () => (
    <div className="flex items-center justify-between gap-2 px-2">
      {[...Array(5)].map((_, i) => (
        <React.Fragment key={`skeleton-${i}`}>
          <div className="flex flex-col items-center space-y-1 p-2 rounded-lg flex-1">
            <div className="w-12 h-12 rounded-full bg-secondary animate-pulse" />
            <Skeleton className="h-3 w-16" />
          </div>
          {i < 4 && <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />}
        </React.Fragment>
      ))}
    </div>
  )

  if (stages.length === 0) {
    return (
      <Card className="h-full flex flex-col">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-bold">Process Summary</CardTitle>
          <CardDescription className="text-sm">Workflow progress overview</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col space-y-4">
          {renderSkeletons()}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-bold">Process Summary</CardTitle>
        <CardDescription className="text-sm">{getDescription()}</CardDescription>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col space-y-4">
        {/* Compact Stage Icons */}
        <div className="flex items-center justify-between gap-1 px-2">
          {stages.map((stage, index) => (
            <React.Fragment key={stage.id}>
              <button
                onClick={() => setSelectedStage(stage.id)}
                className={cn(
                  "flex flex-col items-center space-y-1 p-2 rounded-lg transition-all flex-1",
                  selectedStage === stage.id 
                    ? "bg-teal ring-2 ring-teal/60 text-white" 
                    : "hover:bg-secondary"
                )}
              >
                <div className="relative w-full flex justify-center">
                  <div className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center",
                    selectedStage === stage.id
                      ? "bg-teal/80"
                      : stage.status === "done" && "bg-tester/10",
                    selectedStage === stage.id
                      ? "bg-teal/80"
                      : stage.status === "wip" && "bg-analyst/10", 
                    selectedStage === stage.id
                      ? "bg-teal/80"
                      : stage.status === "queued" && "bg-secondary"
                  )}>
                    {selectedStage === stage.id 
                      ? getRoleIcon(stage.agentName, "w-6 h-6 text-white") 
                      : getRoleIcon(stage.agentName, "w-6 h-6")
                    }
                    {/* Status overlay - top right */}
                    <div className={cn(
                      "absolute top-0 right-2 w-5 h-5 rounded-full flex items-center justify-center border-2 border-white",
                      getStatusColor(stage.status)
                    )}>
                      {getStatusIcon(stage.status, "w-3 h-3")}
                    </div>
                  </div>
                </div>
                <span className={cn(
                  "text-xs font-medium text-center",
                  selectedStage === stage.id ? "text-white" : "text-foreground"
                )}>{stage.name}</span>
              </button>
              {index < stages.length - 1 && (
                <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Always Expanded Detailed View */}
        <div className="border rounded-lg p-3 flex-1">
          {currentStage && (
            <div className="space-y-3">
              {/* Stage Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getRoleIcon(currentStage.agentName, "w-5 h-5")}
                  <h3 className="font-semibold">{currentStage.name} Stage</h3>
                  <Badge variant="muted" size="sm">
                    {currentStage.status.toUpperCase()}
                  </Badge>
                  {currentStage.hitlRequired && (
                    <Badge variant="destructive" size="sm">HITL</Badge>
                  )}
                </div>
              </div>

              {/* Task Summary */}
              <div className="space-y-2 pb-3 border-b">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">Progress: {completedTasks}/{totalTasks}</span>
                  <span className="text-muted-foreground">{Math.round(progressPercentage)}%</span>
                </div>
                <Progress value={progressPercentage} className="h-2" />
              </div>

              {/* Tasks Section */}
              <div className="pt-3">
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold border-l-4 border-teal pl-2">Stage Tasks</h4>
                  <div className="space-y-1 bg-secondary rounded-lg p-3 border">
                    {currentStage.tasks.map((task) => (
                      <div key={task.id} className="bg-card border border-border rounded p-3 shadow-sm">
                        <button 
                          onClick={() => toggleTask(task.id)}
                          className="w-full flex items-center justify-between text-left"
                        >
                          <div className="flex items-center space-x-2">
                            <div className={cn(
                              "w-3 h-3 rounded-full flex items-center justify-center",
                              getStatusColor(task.status)
                            )}>
                              {getStatusIcon(task.status, "w-2 h-2")}
                            </div>
                            <span className="text-sm font-medium text-foreground">{task.name}</span>
                            <Badge variant="muted" size="sm">
                              {task.status}
                            </Badge>
                          </div>
                          <ChevronDown 
                            className={cn(
                              "w-4 h-4 transition-transform text-muted-foreground",
                              expandedTasks.includes(task.id) && "rotate-180"
                            )} 
                          />
                        </button>
                        
                        {expandedTasks.includes(task.id) && (
                          <div className="mt-2 pl-5 border-l-2 border-border">
                            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                              {getRoleIcon(currentStage.agentName, "w-3 h-3")}
                              <span><strong>{currentStage.agentName}:</strong> {task.name}</span>
                              <div className={cn(
                                "w-2 h-2 rounded-full",
                                getStatusColor(task.status)
                              )} />
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Artifacts Section */}
              <div className="pt-3">
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold border-l-4 border-purple-500 pl-2">Stage Artifacts</h4>
                  <div className="space-y-1 bg-secondary rounded-lg p-3 border">
                    {stageArtifacts.length > 0 ? (
                      stageArtifacts.map((artifact) => (
                        <div key={artifact.id} className="bg-card border border-border rounded p-3 shadow-sm flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <FileCode className="w-4 h-4 text-purple-500" />
                            <span className="text-sm font-medium text-foreground">{artifact.name}</span>
                            <Badge variant="muted" size="sm" className={getStatusBadgeClasses(artifact.status)}>
                              {artifact.status.toUpperCase()}
                            </Badge>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={artifact.status !== 'completed'}
                            onClick={() => window.open(`/artifacts/${artifact.session_id}/${currentStage.name.toLowerCase()}/${artifact.name}`, '_blank')}
                          >
                            Download
                          </Button>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-muted-foreground p-3">No artifacts for this stage yet.</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}