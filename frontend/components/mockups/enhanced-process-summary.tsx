"use client"

import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { getStatusBadgeClasses, getAgentBadgeClasses } from "@/lib/utils/badge-utils"

// Stage colors now managed centrally in @/lib/utils/badge-utils
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
  Download,
  Zap,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useProcessStore } from "@/lib/stores/process-store"
import { useConversationStore } from "@/lib/stores/conversation-store"
import { useArtifactScaffoldingStore } from "@/lib/stores/artifact-scaffolding-store"
import { useHITLStore } from "@/lib/stores/hitl-store"
import { useAgentStore } from "@/lib/stores/agent-store"

// --- Role-based Icon Mapping ---
// OLD COLORS (keep for rollback): text-analyst, text-architect, text-developer, text-tester, text-deployer
// FINAL TEST COLORS: text-slate-500, text-pink-500, text-lime-600, text-sky-500, text-rose-600
const getRoleIcon = (agent: string, sizeAndColor = "w-6 h-6") => {
  const agentLower = agent.toLowerCase()
  if (agentLower.includes('analyst')) return <ClipboardCheck className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-slate-500`} />
  if (agentLower.includes('architect')) return <DraftingCompass className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-pink-500`} />
  if (agentLower.includes('developer')) return <Construction className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-lime-600`} />
  if (agentLower.includes('tester')) return <TestTube2 className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-sky-500`} />
  if (agentLower.includes('deployer')) return <Rocket className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-rose-600`} />
  return <User className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-muted-foreground`} /> // Default
}

// --- Status Overlay Icon ---
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

// Badge color functions are now imported from @/lib/utils/badge-utils

const getStatusColor = (status: string) => {
  switch (status) {
    case 'done': return 'bg-tester'
    case 'wip': return 'bg-analyst' 
    case 'queued': return 'bg-muted'
    case 'waiting': return 'bg-amber'
    default: return 'bg-muted'
  }
}

const stageIcons = {
  done: <CheckCircle className="w-8 h-8 text-tester" />, // STATUS color (keep as-is)
  wip: <Loader className="w-8 h-8 text-analyst animate-spin" />, // STATUS color (keep as-is) 
  queued: <Circle className="w-8 h-8 text-muted" />, // STATUS color (keep as-is)
}

// Generate stages data from SDLC.yaml structure instead of hardcoded demo data
const generateStagesFromSDLC = (processStages: any[], currentProject: any) => {
  // If no real data available, show SDLC stages but empty artifacts until project is initialized
  if (!processStages || processStages.length === 0) {
    // Show the SDLC stages with artifacts from sdlc.yaml
    if (!currentProject) {
      return [
        { 
          id: "analyze", 
          name: "Analyze", 
          status: "queued", 
          agent: "Analyst", 
          tasks: "0/3",
          artifacts: [
            {
              name: "Analysis Execution Plan",
              status: "queued",
              role: "Analyst",
              task: "Create Analysis Execution Plan",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Create Analysis Execution Plan - Analyst"
              }
            },
            {
              name: "Business Requirements Document (BRD)",
              status: "queued",
              role: "Analyst",
              task: "Create Business Requirements Document",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Create Business Requirements Document - Analyst"
              }
            },
            {
              name: "Functional Requirements Specification (FRS)",
              status: "queued",
              role: "Analyst",
              task: "Create Functional Requirements Specification",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Create Functional Requirements Specification - Analyst"
              }
            }
          ]
        },
        { 
          id: "design", 
          name: "Design", 
          status: "queued", 
          agent: "Architect", 
          tasks: "0/2",
          artifacts: [
            {
              name: "System Architecture Document",
              status: "queued",
              role: "Architect",
              task: "Create System Architecture Document",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Create System Architecture Document - Architect"
              }
            },
            {
              name: "Technical Design Specification",
              status: "queued",
              role: "Architect",
              task: "Create Technical Design Specification",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Create Technical Design Specification - Architect"
              }
            }
          ]
        },
        { 
          id: "build", 
          name: "Build", 
          status: "queued", 
          agent: "Developer", 
          tasks: "0/2",
          artifacts: [
            {
              name: "Source Code",
              status: "queued",
              role: "Developer",
              task: "Develop Source Code",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Develop Source Code - Developer"
              }
            },
            {
              name: "Unit Test Cases",
              status: "queued",
              role: "Developer",
              task: "Create Unit Test Cases",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Create Unit Test Cases - Developer"
              }
            }
          ]
        },
        { 
          id: "validate", 
          name: "Validate", 
          status: "queued", 
          agent: "Tester", 
          tasks: "0/2",
          artifacts: [
            {
              name: "Test Plan",
              status: "queued",
              role: "Tester",
              task: "Create Test Plan",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Create Test Plan - Tester"
              }
            },
            {
              name: "Test Cases and Results",
              status: "queued",
              role: "Tester",
              task: "Execute Test Cases and Generate Results",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Execute Test Cases and Generate Results - Tester"
              }
            }
          ]
        },
        { 
          id: "launch", 
          name: "Launch", 
          status: "queued", 
          agent: "Deployer", 
          tasks: "0/2",
          artifacts: [
            {
              name: "Deployment Plan",
              status: "queued",
              role: "Deployer",
              task: "Create Deployment Plan",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Create Deployment Plan - Deployer"
              }
            },
            {
              name: "Release Notes",
              status: "queued",
              role: "Deployer",
              task: "Create Release Notes",
              subtasks: { completed: 0, total: 1 },
              tasks_detail: {
                previous: "",
                current: "",
                next: "Create Release Notes - Deployer"
              }
            }
          ]
        }
      ];
    }
    return [];
  }
  
  // If real process store data is available, use it
  return processStages.map(stage => ({
    id: stage.id,
    name: stage.name,
    status: stage.status || "pending",
    agent: stage.agent || "Unknown",
    tasks: `${stage.tasks?.filter((t: any) => t.status === 'completed').length || 0}/${stage.tasks?.length || 0}`,
    artifacts: stage.artifacts?.map((artifact: any) => ({
      name: artifact.name,
      status: artifact.status || "pending",
      role: artifact.role || stage.agent,
      task: artifact.task || artifact.name,
      subtasks: { 
        completed: artifact.subtasks?.completed || 0, 
        total: artifact.subtasks?.total || 1 
      },
      tasks_detail: artifact.tasks_detail || {
        previous: "",
        current: "",
        next: `${artifact.task || artifact.name} - ${artifact.role || stage.agent}`
      }
    })) || []
  }))
}

const designTasks = [
  { icon: <Database className="w-4 h-4" />, name: "Database schema", status: "wip" },
  { icon: <FileCode className="w-4 h-4" />, name: "API routes", status: "queued" },
  { icon: <Component className="w-4 h-4" />, name: "React components", status: "queued" },
  { icon: <Lock className="w-4 h-4" />, name: "Auth flow", status: "queued" },
]

const parallelDevOpsTask = {
  icon: <Server className="w-4 h-4" />,
  name: "DevOps",
  description: "Setting up environments",
  tasks: "2/3",
}

export function EnhancedProcessSummaryMockup() {
  const processStages = useProcessStore((state) => state.stages)
  const { artifacts } = useArtifactScaffoldingStore()
  const currentProject = useConversationStore((state) => state.currentProject)
  const { requests, addRequest, navigateToRequest, getRequestsByAgent } = useHITLStore()
  const { setAgentFilter } = useAgentStore()
  const [selectedStage, setSelectedStage] = useState("analyze") // Default to analyze stage (first SDLC stage)
  const [expandedArtifacts, setExpandedArtifacts] = useState<string[]>(["Analysis Execution Plan"]) // Default expand first execution plan
  const [isClient, setIsClient] = useState(false)

  React.useEffect(() => {
    setIsClient(true)
  }, [])

  // Generate stages data from real process store data or use SDLC default structure
  const stagesData = generateStagesFromSDLC(processStages, currentProject)
  const currentStage = stagesData.find(stage => stage.id === selectedStage)

  const getArtifactHITLRequests = (artifactName: string) => {
    if (!isClient || !currentStage) return []
    
    // Find the artifact to get its responsible agent
    const artifact = currentStage.artifacts.find(a => a.name === artifactName)
    if (!artifact || !artifact.role) return []
    
    // Get pending HITL requests for the agent responsible for this artifact
    return getRequestsByAgent(artifact.role).filter(req => req.status === 'pending')
  }

  const handleHITLClick = (artifactName: string) => {
    if (!currentStage) return
    
    // Find the artifact to get its responsible agent
    const artifact = currentStage.artifacts.find(a => a.name === artifactName)
    if (!artifact || !artifact.role) return
    
    // Get pending HITL requests for this agent
    const agentHITLRequests = getRequestsByAgent(artifact.role).filter(req => req.status === 'pending')
    if (agentHITLRequests.length > 0) {
      // Set agent filter first, then navigate with proper synchronization
      setAgentFilter(artifact.role)
      
      // Use setTimeout to ensure agent filter state is updated before navigation
      setTimeout(() => {
        navigateToRequest(agentHITLRequests[0].id)
      }, 50)
    } else {
      // Create a new HITL request if none exists
      const nextTask = artifact.tasks_detail?.next || `Approve ${artifactName}`
      addRequest({
        agentName: artifact.role,
        decision: `${nextTask} - Please review and approve the ${artifactName} artifact.`,
        context: {
          artifactName,
          stage: currentStage.name,
          status: artifact.status,
          subtasks: artifact.subtasks,
          nextTask
        },
        priority: 'medium'
      })
      
      // Navigate to the newly created request with proper timing
      setTimeout(() => {
        const newRequests = getRequestsByAgent(artifact.role).filter(req => req.status === 'pending')
        if (newRequests.length > 0) {
          // Set agent filter first
          setAgentFilter(artifact.role)
          // Then navigate after another short delay
          setTimeout(() => {
            navigateToRequest(newRequests[newRequests.length - 1].id)
          }, 50)
        }
      }, 100)
    }
  }
  
  const progressPercentage = currentStage ? (parseInt(currentStage.tasks.split('/')[0]) / parseInt(currentStage.tasks.split('/')[1])) * 100 : 0
  
  // Get real artifacts from store for current stage
  const stageArtifacts = Object.values(artifacts).filter(
    (artifact) => currentStage && artifact.stage.toLowerCase() === currentStage.name.toLowerCase()
  )
  
  // Calculate artifact summary status
  const getArtifactSummaryStatus = (artifacts: any[]) => {
    const hasWip = artifacts.some(a => a.status === 'wip')
    const hasQueued = artifacts.some(a => a.status === 'queued')
    const hasPlanned = artifacts.some(a => a.status === 'planned')
    const allDone = artifacts.every(a => a.status === 'done')
    
    if (allDone) return 'done'
    if (hasWip) return 'wip'
    if (hasQueued) return 'queued'
    if (hasPlanned) return 'planned'
    return 'queued'
  }
  
  // Calculate completed artifacts count
  const getCompletedArtifactsCount = (artifacts: any[]) => {
    return artifacts.filter(a => a.status === 'done').length
  }
  
  const artifactSummaryStatus = currentStage ? getArtifactSummaryStatus(currentStage.artifacts) : 'queued'
  const completedArtifacts = currentStage ? getCompletedArtifactsCount(currentStage.artifacts) : 0
  const totalArtifacts = currentStage ? currentStage.artifacts.length : 0

  const toggleArtifact = (artifactName: string, event?: React.MouseEvent) => {
    // Check if click originated from a HITL badge
    if (event && (event.target as HTMLElement).closest('.hitl-badge')) {
      return; // Don't toggle if HITL badge was clicked
    }
    setExpandedArtifacts(prev => 
      prev.includes(artifactName) 
        ? prev.filter(name => name !== artifactName)
        : [...prev, artifactName]
    )
  }

  const handleDownload = (artifactName: string, status: string, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent artifact expansion/collapse
    
    // Create downloadable content
    const content = `Artifact: ${artifactName}
Status: ${status}
Generated: ${new Date().toISOString()}
Stage: ${currentStage?.name}

Downloading artifact content from ${artifact.role} agent.
Generated via SDLC workflow orchestration.`

    // Create and trigger download
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${artifactName.replace(/\s+/g, '_').toLowerCase()}_${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Handle empty state when no project is initialized
  if (!stagesData || stagesData.length === 0) {
    return (
      <Card className="h-full flex flex-col">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-bold">Process Summary</CardTitle>
          <CardDescription className="text-sm">No project initialized</CardDescription>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col items-center justify-center space-y-4 text-center">
          <div className="text-muted-foreground">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-secondary flex items-center justify-center">
              <Zap className="w-8 h-8 text-muted-foreground/50" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Ready to Start</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Click "Start New Project" to initialize your BotArmy workflow with AI-powered agents.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-bold">Process Summary</CardTitle>
        <CardDescription className="text-sm">Building Hello World page in React</CardDescription>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col space-y-4">
        {/* Enhanced Stage Icons with Connecting Lines */}
        <div className="relative flex items-center justify-between gap-1 px-2">
          {/* Background connecting line */}
          <div className="absolute top-[28px] left-8 right-8 h-0.5 bg-gradient-to-r from-border via-teal/30 to-border -z-10"></div>
          
          {stagesData.map((stage, index) => (
            <React.Fragment key={stage.id}>
              <button
                onClick={() => setSelectedStage(stage.id)}
                className={cn(
                  "relative flex flex-col items-center space-y-1 p-2 rounded-lg transition-all flex-1 z-10",
                  selectedStage === stage.id 
                    ? "bg-teal ring-2 ring-teal/60 text-white shadow-lg" 
                    : "hover:bg-secondary hover:shadow-sm"
                )}
              >
                <div className="relative w-full flex justify-center">
                  <div className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center border-2 border-background shadow-sm",
                    selectedStage === stage.id
                      ? "bg-teal border-teal/50"
                      : stage.status === "done" && "bg-tester/10 border-tester/20",
                    selectedStage === stage.id
                      ? "bg-teal border-teal/50"
                      : stage.status === "wip" && "bg-analyst/10 border-analyst/20", 
                    selectedStage === stage.id
                      ? "bg-teal border-teal/50"
                      : stage.status === "queued" && "bg-secondary border-border"
                  )}>
                    {selectedStage === stage.id 
                      ? getRoleIcon(stage.agent, "w-6 h-6 text-white") 
                      : getRoleIcon(stage.agent, "w-6 h-6")
                    }
                    {/* Enhanced Status overlay */}
                    <div className={cn(
                      "absolute -top-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center border-2 border-white shadow-sm",
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
              {index < stagesData.length - 1 && (
                <div className="flex flex-col items-center z-20">
                  <ChevronRight className={cn(
                    "w-4 h-4 flex-shrink-0 transition-colors",
                    index < stagesData.findIndex(s => s.id === selectedStage) ? "text-teal" : "text-muted-foreground"
                  )} />
                  {/* Progress indicator line segment */}
                  <div className={cn(
                    "absolute top-[28px] w-8 h-0.5 transition-colors",
                    index < stagesData.findIndex(s => s.id === selectedStage) ? "bg-teal" : "bg-border"
                  )}></div>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Always Expanded Detailed View */}
        <div className="border rounded-lg p-3 flex-1">
          {currentStage && (
            <div className="space-y-3">
              {/* Stage Summary */}
              <div className="space-y-2 pb-3 border-b">
                <div className="flex items-center space-x-2">
                  <h3 className="font-semibold">{currentStage.name} Stage</h3>
                  <Badge variant="muted" size="sm" className={getStatusBadgeClasses(currentStage.status)}>
                    {currentStage.status.toUpperCase()}
                  </Badge>
                  <Badge variant="muted" size="sm" className={getAgentBadgeClasses(currentStage.agent)}>
                    {getRoleIcon(currentStage.agent, "w-2.5 h-2.5 mr-0.5")}
                    {currentStage.agent}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">Task Progress: {currentStage.tasks}</span>
                  <span className="text-muted-foreground">{Math.round(progressPercentage)}%</span>
                </div>
                <Progress value={progressPercentage} className="h-2" />
              </div>

              {/* Artifacts Section - Separated */}
              <div className="pt-3">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold border-l-4 border-teal pl-2">Artifact Summary</h3>
                      <Badge variant="muted" size="sm" className={getStatusBadgeClasses(artifactSummaryStatus)}>
                        {artifactSummaryStatus.toUpperCase()}
                      </Badge>
                    </div>
                    <span className="text-sm">{completedArtifacts}/{totalArtifacts}</span>
                  </div>
                  <div className="space-y-1 bg-secondary rounded-lg p-3 border">
                    {currentStage.artifacts.map((artifact) => (
                      <div key={artifact.name} className="bg-card border border-border rounded p-3 shadow-sm">
                        <div className="w-full flex items-center justify-between">
                          <button 
                            onClick={(e) => toggleArtifact(artifact.name, e)}
                            className="flex items-center space-x-2 flex-1 text-left hover:bg-secondary/50 rounded p-1 -m-1 transition-colors"
                          >
                            <div className={cn(
                              "w-3 h-3 rounded-full flex items-center justify-center",
                              getStatusColor(artifact.status)
                            )}>
                              {getStatusIcon(artifact.status, "w-2 h-2")}
                            </div>
                            <span className="text-sm font-medium text-foreground">{artifact.name}</span>
                            {(() => {
                              const hitlRequests = getArtifactHITLRequests(artifact.name)
                              const hasHITL = hitlRequests.length > 0
                              
                              return hasHITL ? (
                                <Badge
                                  variant="destructive"
                                  size="sm"
                                  className="animate-pulse cursor-pointer hitl-badge"
                                  onClick={() => handleHITLClick(artifact.name)}
                                  title="Click to resolve HITL request"
                                >
                                  <AlertTriangle className="w-3 h-3 mr-1" />
                                  HITL ({hitlRequests.length})
                                </Badge>
                              ) : (
                                <Badge variant="muted" size="sm" className={getStatusBadgeClasses(artifact.status === 'wip' && artifact.tasks_detail?.next?.includes('HITL') ? 'waiting' : artifact.status)}>
                                  {(artifact.status === 'wip' && artifact.tasks_detail?.next?.includes('HITL') ? 'waiting' : artifact.status).toUpperCase()}
                                </Badge>
                              )
                            })()}
                            <span className="text-sm text-muted-foreground">
                              {artifact.subtasks.completed}/{artifact.subtasks.total}
                            </span>
                          </button>
                          
                          <div className="flex items-center space-x-1 flex-shrink-0">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 hover:bg-secondary"
                              onClick={(e) => handleDownload(artifact.name, artifact.status, e)}
                              disabled={artifact.status === 'planned'}
                              title={artifact.status === 'planned' ? 'Download unavailable - artifact not created yet' : `Download ${artifact.name}`}
                            >
                              <Download className={cn(
                                "w-3 h-3",
                                artifact.status === 'planned' ? "text-muted-foreground/50" : "text-muted-foreground hover:text-foreground"
                              )} />
                            </Button>
                            
                            <button
                              onClick={() => toggleArtifact(artifact.name)}
                              className="flex items-center justify-center w-6 h-6 hover:bg-secondary/50 rounded transition-colors"
                            >
                              <ChevronDown 
                                className={cn(
                                  "w-4 h-4 transition-transform text-muted-foreground",
                                  expandedArtifacts.includes(artifact.name) && "rotate-180"
                                )} 
                              />
                            </button>
                          </div>
                        </div>
                        
                        {expandedArtifacts.includes(artifact.name) && artifact.status !== 'done' && (
                          <div className="mt-3 space-y-2">
                            {/* Progress bar for expanded view */}
                            <div className="px-2">
                              <Progress 
                                value={(artifact.subtasks.completed / artifact.subtasks.total) * 100} 
                                className="h-2" 
                              />
                            </div>
                            
                            {/* Task details with tags */}
                            <div className="pl-5 border-l-2 border-border space-y-2 text-xs">
                              {artifact.tasks_detail?.previous && (
                                <div className="flex items-center space-x-1.5">
                                  <span className="text-muted-foreground">{artifact.tasks_detail.previous.split(' - ')[0]}</span>
                                  <Badge variant="outline" className="text-tester border-tester/20 text-[10px] px-1 py-0.5 h-4">
                                    DONE
                                  </Badge>
                                  <Badge variant="outline" className={`${getAgentBadgeClasses("Analyst")} text-[10px] px-1 py-0.5 h-4`}>
                                    {getRoleIcon("Analyst", "w-2.5 h-2.5 mr-0.5")}
                                    Analyst
                                  </Badge>
                                </div>
                              )}
                              {artifact.tasks_detail?.current && (
                                <div className="flex items-center space-x-1.5">
                                  <span className="text-foreground">{artifact.tasks_detail.current.split(' - ')[0]}</span>
                                  <Badge variant="outline" className="text-analyst border-analyst/20 text-[10px] px-1 py-0.5 h-4">
                                    WIP
                                  </Badge>
                                  <Badge variant="outline" className={`${getAgentBadgeClasses("PM")} text-[10px] px-1 py-0.5 h-4`}>
                                    {getRoleIcon("PM", "w-2.5 h-2.5 mr-0.5")}
                                    PM
                                  </Badge>
                                </div>
                              )}
                              {artifact.tasks_detail?.next && (
                                <div className="flex items-center space-x-1.5">
                                  <span className="text-muted-foreground">{artifact.tasks_detail.next.split(' - ')[0]}</span>
                                  <Badge variant="outline" className="text-amber border-amber/20 text-[10px] px-1 py-0.5 h-4">
                                    QUEUED
                                  </Badge>
                                  <Badge 
                                    variant="outline" 
                                    className={`${getAgentBadgeClasses(artifact.role)} text-[10px] px-1 py-0.5 h-4`}
                                  >
                                    {getRoleIcon(artifact.role, "w-2.5 h-2.5 mr-0.5")}
                                    {artifact.role}
                                  </Badge>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
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