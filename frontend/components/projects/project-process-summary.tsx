"use client"

import React, { useState, useMemo, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { getStatusBadgeClasses, getAgentBadgeClasses } from "@/lib/utils/badge-utils"
import { Skeleton } from "@/components/ui/skeleton"
import { useProjectArtifacts } from "@/hooks/use-project-artifacts"
import { workflowsService, type WorkflowDeliverablesResponse } from "@/lib/services/api"
import { cn } from "@/lib/utils"

import {
  CheckCircle,
  Loader,
  Circle,
  ChevronRight,
  ChevronDown,
  AlertTriangle,
  User,
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

interface ProjectProcessSummaryProps {
  projectId: string;
  className?: string;
}

// Role-based Icon Mapping
const getRoleIcon = (agent: string, sizeAndColor = "w-6 h-6") => {
  const agentLower = (agent || '').toLowerCase()
  if (agentLower.includes('analyst')) return <ClipboardCheck className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-slate-500`} />
  if (agentLower.includes('architect')) return <DraftingCompass className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-pink-500`} />
  if (agentLower.includes('developer')) return <Construction className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-lime-600`} />
  if (agentLower.includes('tester')) return <TestTube2 className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-sky-500`} />
  if (agentLower.includes('deployer')) return <Rocket className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-rose-600`} />
  return <User className={sizeAndColor.includes('text-white') ? sizeAndColor : `${sizeAndColor} text-muted-foreground`} />
}

// Status Overlay Icon
const getStatusIcon = (status: string, size = "w-3 h-3") => {
  switch (status) {
    case 'completed':
    case 'done':
      return <CheckCircle className={`${size} text-white`} />
    case 'in_progress':
    case 'wip':
      return <Play className={`${size} text-white`} />
    case 'pending':
    case 'queued':
      return <Clock className={`${size} text-white`} />
    case 'failed':
    case 'waiting':
      return <AlertTriangle className={`${size} text-white`} />
    default:
      return <Circle className={`${size} text-white`} />
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
    case 'done':
      return 'bg-tester'
    case 'in_progress':
    case 'wip':
      return 'bg-analyst'
    case 'pending':
    case 'queued':
      return 'bg-muted'
    case 'failed':
    case 'waiting':
      return 'bg-amber'
    default:
      return 'bg-muted'
  }
}

// SDLC Stages with artifacts structure - now uses dynamic workflow deliverables
const generateSDLCStages = (artifacts: any[], workflowDeliverables: WorkflowDeliverablesResponse | null = null) => {
  // Create default SDLC stages
  const defaultStages = [
    {
      id: "analyze",
      name: "Analyze",
      status: "queued",
      agent: "Analyst",
      artifacts: []
    },
    {
      id: "design",
      name: "Design",
      status: "queued",
      agent: "Architect",
      artifacts: []
    },
    {
      id: "build",
      name: "Build",
      status: "queued",
      agent: "Developer",
      artifacts: []
    },
    {
      id: "validate",
      name: "Validate",
      status: "queued",
      agent: "Tester",
      artifacts: []
    },
    {
      id: "launch",
      name: "Launch",
      status: "queued",
      agent: "Deployer",
      artifacts: []
    }
  ];

  // Map artifacts to stages based on name patterns or agent
  const stagesWithArtifacts = defaultStages.map(stage => {
    // Get expected deliverables for this stage from workflow definition
    const expectedDeliverables = workflowDeliverables?.deliverables[stage.id as keyof typeof workflowDeliverables.deliverables] || [];

    // Match actual artifacts to this stage
    const actualArtifacts = artifacts.filter(artifact => {
      const name = (artifact.name || '').toLowerCase();
      const agent = (artifact.agent || '').toLowerCase();

      // Match by stage name or agent type
      // ANALYZE stage: includes plans, briefs, requirements, PRDs
      if (stage.id === "analyze" && (
        name.includes('requirement') ||
        name.includes('analysis') ||
        name.includes('brief') ||
        name.includes('prd') ||
        name.includes('plan') ||
        name.includes('product') ||
        agent.includes('analyst') ||
        agent.includes('pm')
      )) {
        return true;
      }
      // DESIGN stage: includes architecture, specs, design docs
      if (stage.id === "design" && (
        name.includes('design') ||
        name.includes('architecture') ||
        name.includes('spec') ||
        name.includes('ux') ||
        name.includes('frontend-spec') ||
        name.includes('fullstack') ||
        agent.includes('architect') ||
        agent.includes('ux')
      )) {
        return true;
      }
      // BUILD stage: includes code, implementation
      if (stage.id === "build" && (
        name.includes('code') ||
        name.includes('implementation') ||
        name.includes('story') ||
        agent.includes('developer') ||
        agent.includes('coder') ||
        agent.includes('scrum')
      )) {
        return true;
      }
      // VALIDATE stage: includes tests, validation
      if (stage.id === "validate" && (
        name.includes('test') ||
        name.includes('validation') ||
        name.includes('qa') ||
        agent.includes('tester')
      )) {
        return true;
      }
      // LAUNCH stage: includes deployment, release
      if (stage.id === "launch" && (
        name.includes('deploy') ||
        name.includes('release') ||
        name.includes('launch') ||
        agent.includes('deployer')
      )) {
        return true;
      }

      return false;
    });

    // Merge expected deliverables with actual artifacts
    const stageArtifacts = expectedDeliverables.map(expected => {
      // Find matching actual artifact
      const actual = actualArtifacts.find(artifact =>
        artifact.name.toLowerCase().includes(expected.name.toLowerCase()) ||
        expected.name.toLowerCase().includes(artifact.name.toLowerCase())
      );

      return {
        name: expected.name,
        status: actual?.status || 'pending',
        role: actual?.agent || expected.agent,
        task: `Create ${expected.name}`,
        description: expected.description,
        subtasks: {
          completed: actual?.status === 'completed' ? 1 : 0,
          total: 1
        },
        tasks_detail: {
          previous: "",
          current: actual?.status === 'in_progress' ? `Create ${expected.name}` : "",
          next: !actual || actual.status === 'pending' ? `Create ${expected.name}` : ""
        }
      };
    });

    // Determine stage status based on artifacts
    let stageStatus = "queued";
    if (stageArtifacts.length > 0) {
      const hasCompleted = stageArtifacts.some(a => a.status === 'completed');
      const hasInProgress = stageArtifacts.some(a => a.status === 'in_progress');
      const allCompleted = stageArtifacts.every(a => a.status === 'completed');

      if (allCompleted) {
        stageStatus = "done";
      } else if (hasInProgress) {
        stageStatus = "wip";
      } else if (hasCompleted) {
        stageStatus = "wip";
      }
    }

    return {
      ...stage,
      status: stageStatus,
      artifacts: stageArtifacts,
      tasks: `${stageArtifacts.filter(a => a.status === 'completed').length}/${stageArtifacts.length || 1}`
    };
  });

  return stagesWithArtifacts;
};

export function ProjectProcessSummary({ projectId, className }: ProjectProcessSummaryProps) {
  const { artifacts, loading: artifactsLoading, error: artifactsError, progress: artifactProgress } = useProjectArtifacts(projectId);
  const [selectedStage, setSelectedStage] = useState("analyze");
  const [expandedArtifacts, setExpandedArtifacts] = useState<string[]>([]);
  const [workflowDeliverables, setWorkflowDeliverables] = useState<WorkflowDeliverablesResponse | null>(null);

  // Fetch workflow deliverables on mount
  useEffect(() => {
    const fetchWorkflowDeliverables = async () => {
      try {
        // TODO: Get workflow_id from project data - for now defaulting to 'greenfield-fullstack'
        const response = await workflowsService.getWorkflowDeliverables('greenfield-fullstack');
        if (response.success && response.data) {
          setWorkflowDeliverables(response.data);
        }
      } catch (error) {
        console.error('[ProcessSummary] Failed to fetch workflow deliverables:', error);
      }
    };

    fetchWorkflowDeliverables();
  }, []);

  // Generate stages data from artifacts and workflow deliverables
  const stagesData = useMemo(() => {
    return generateSDLCStages(artifacts, workflowDeliverables);
  }, [artifacts, workflowDeliverables]);

  const currentStage = stagesData.find(stage => stage.id === selectedStage);
  const progressPercentage = currentStage ? (parseInt(currentStage.tasks.split('/')[0]) / parseInt(currentStage.tasks.split('/')[1])) * 100 : 0;

  // Calculate artifact summary status
  const getArtifactSummaryStatus = (artifacts: any[]) => {
    if (artifacts.length === 0) return 'queued';
    const hasWip = artifacts.some(a => a.status === 'in_progress');
    const hasQueued = artifacts.some(a => a.status === 'pending');
    const allDone = artifacts.every(a => a.status === 'completed');

    if (allDone) return 'done';
    if (hasWip) return 'wip';
    if (hasQueued) return 'queued';
    return 'queued';
  };

  const getCompletedArtifactsCount = (artifacts: any[]) => {
    return artifacts.filter(a => a.status === 'completed').length;
  };

  const artifactSummaryStatus = currentStage ? getArtifactSummaryStatus(currentStage.artifacts) : 'queued';
  const completedArtifacts = currentStage ? getCompletedArtifactsCount(currentStage.artifacts) : 0;
  const totalArtifacts = currentStage ? currentStage.artifacts.length : 0;

  const toggleArtifact = (artifactName: string, event?: React.MouseEvent) => {
    if (event && (event.target as HTMLElement).closest('.hitl-badge')) {
      return;
    }
    setExpandedArtifacts(prev =>
      prev.includes(artifactName)
        ? prev.filter(name => name !== artifactName)
        : [...prev, artifactName]
    );
  };

  const handleDownload = (artifactName: string, status: string, e: React.MouseEvent) => {
    e.stopPropagation();

    const content = `Artifact: ${artifactName}
Status: ${status}
Generated: ${new Date().toISOString()}
Stage: ${currentStage?.name}

Project ID: ${projectId}
Downloaded from BotArmy workflow orchestration.`;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifactName.replace(/\s+/g, '_').toLowerCase()}_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (artifactsLoading) {
    return (
      <Card className={cn("h-full flex flex-col", className)}>
        <CardHeader className="pb-2">
          <div className="space-y-2">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-3 w-24" />
          </div>
        </CardHeader>
        <CardContent className="flex-1 space-y-4">
          <Skeleton className="h-16 w-full" />
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (artifactsError) {
    return (
      <Card className={cn("h-full flex flex-col border-red-200", className)}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-red-600">Error Loading Workflow</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-500">
            Unable to load workflow progress: {artifactsError}
          </p>
        </CardContent>
      </Card>
    );
  }

  // Handle empty state when no artifacts
  if (!stagesData || stagesData.length === 0 || artifacts.length === 0) {
    return (
      <Card className={cn("h-full flex flex-col", className)}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-bold">Process Summary</CardTitle>
          <CardDescription className="text-sm">No workflow initialized</CardDescription>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col items-center justify-center space-y-4 text-center">
          <div className="text-muted-foreground">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-secondary flex items-center justify-center">
              <Zap className="w-8 h-8 text-muted-foreground/50" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Ready to Start</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Start a workflow to see process stages and artifacts appear here.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-bold">Process Summary</CardTitle>
        <CardDescription className="text-sm">SDLC Workflow Progress</CardDescription>
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
                  <Badge variant="outline" size="sm" className={getStatusBadgeClasses(currentStage.status)}>
                    {(currentStage.status || 'UNKNOWN').toUpperCase()}
                  </Badge>
                  <Badge variant="outline" size="sm" className={getAgentBadgeClasses(currentStage.agent)}>
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

              {/* Artifacts Section */}
              <div className="pt-3">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold border-l-4 border-teal pl-2">Artifact Summary</h3>
                      <Badge variant="outline" size="sm" className={getStatusBadgeClasses(artifactSummaryStatus)}>
                        {(artifactSummaryStatus || 'UNKNOWN').toUpperCase()}
                      </Badge>
                    </div>
                    <span className="text-sm">{completedArtifacts}/{totalArtifacts}</span>
                  </div>
                  {currentStage.artifacts.length > 0 ? (
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
                              <Badge variant="outline" size="sm" className={getStatusBadgeClasses(artifact.status)}>
                                {(artifact.status || 'UNKNOWN').toUpperCase()}
                              </Badge>
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
                                disabled={artifact.status === 'pending'}
                                title={artifact.status === 'pending' ? 'Download unavailable - artifact not created yet' : `Download ${artifact.name}`}
                              >
                                <Download className={cn(
                                  "w-3 h-3",
                                  artifact.status === 'pending' ? "text-muted-foreground/50" : "text-muted-foreground hover:text-foreground"
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

                          {expandedArtifacts.includes(artifact.name) && artifact.status !== 'completed' && (
                            <div className="mt-3 space-y-2">
                              <div className="px-2">
                                <Progress
                                  value={(artifact.subtasks.completed / artifact.subtasks.total) * 100}
                                  className="h-2"
                                />
                              </div>

                              <div className="pl-5 border-l-2 border-border space-y-2 text-xs">
                                {artifact.tasks_detail?.current && (
                                  <div className="flex items-center space-x-1.5">
                                    <span className="text-foreground">{artifact.tasks_detail.current}</span>
                                    <Badge variant="outline" className="text-analyst border-analyst/20 text-[10px] px-1 py-0.5 h-4">
                                      WIP
                                    </Badge>
                                    <Badge variant="outline" className={`${getAgentBadgeClasses(artifact.role)} text-[10px] px-1 py-0.5 h-4`}>
                                      {getRoleIcon(artifact.role, "w-2.5 h-2.5 mr-0.5")}
                                      {artifact.role}
                                    </Badge>
                                  </div>
                                )}
                                {artifact.tasks_detail?.next && (
                                  <div className="flex items-center space-x-1.5">
                                    <span className="text-muted-foreground">{artifact.tasks_detail.next}</span>
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
                  ) : (
                    <div className="text-center py-4 text-muted-foreground">
                      <p className="text-sm">No artifacts in this stage yet</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}