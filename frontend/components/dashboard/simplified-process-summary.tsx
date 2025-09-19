"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { ChevronRight, CheckCircle, Loader, Clock, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { useProcessStore, ProcessStage } from "@/lib/stores/process-store"
import { useConversationStore } from "@/lib/stores/conversation-store"
import { Skeleton } from "@/components/ui/skeleton"

// Fallback data that matches the current process structure
const fallbackStages: ProcessStage[] = [
  {
    id: "analyze",
    name: "Plan",
    status: "done",
    agentName: "Analyst",
    tasks: [],
    artifacts: [],
    hitlRequired: false
  },
  {
    id: "design", 
    name: "Design",
    status: "wip",
    agentName: "Architect",
    tasks: [],
    artifacts: [],
    hitlRequired: false
  },
  {
    id: "build",
    name: "Build", 
    status: "queued",
    agentName: "Developer",
    tasks: [],
    artifacts: [],
    hitlRequired: false
  },
  {
    id: "test",
    name: "Test",
    status: "queued", 
    agentName: "Tester",
    tasks: [],
    artifacts: [],
    hitlRequired: false
  },
  {
    id: "deploy",
    name: "Deploy",
    status: "queued",
    agentName: "Deployer", 
    tasks: [],
    artifacts: [],
    hitlRequired: false
  }
]

interface SimplifiedProcessSummaryProps {
    showSkeleton?: boolean
}

export function SimplifiedProcessSummary({ 
    showSkeleton = false 
}: SimplifiedProcessSummaryProps) {
    const processStages = useProcessStore((state) => state.stages)
    
    // Use real data if available, otherwise use fallback for demonstration
    const stages = processStages.length > 0 ? processStages : fallbackStages

    const renderSkeletons = () => (
        <div className="flex items-center justify-center gap-2">
            {[...Array(5)].map((_, i) => (
                <div key={`skeleton-${i}`} className="flex items-center">
                    <div className="w-24 h-16 border border-border bg-card shadow-sm rounded">
                        <div className="p-2 h-full flex items-center justify-center">
                            <Skeleton className="h-4 w-16" />
                        </div>
                    </div>
                    {i < 4 && <ChevronRight key={`arrow-${i}`} className="w-4 h-4 text-muted-foreground mx-2" />}
                </div>
            ))}
        </div>
    )

    return (
        <Card className="border border-border bg-card text-card-foreground shadow-sm">
            <CardHeader className="pb-3">
                <CardTitle className="text-lg">Process Summary</CardTitle>
                <CardDescription>
                    Building a Hello World page in React
                </CardDescription>
            </CardHeader>
            <CardContent className="pb-4">
                {showSkeleton || stages.length === 0 ? (
                    renderSkeletons()
                ) : (
                    <div className="flex items-center justify-center gap-2">
                        {stages.map((stage, index) => (
                            <div key={`stage-${stage.id}-${index}`} className="flex items-center">
                                <div className="w-24 h-16 border border-border bg-card shadow-sm rounded">
                                    <div className="p-2 h-full flex items-center justify-center">
                                        <span className="text-sm font-medium text-center">{stage.name}</span>
                                    </div>
                                </div>
                                {index < stages.length - 1 && (
                                    <ChevronRight key={`stage-arrow-${stage.id}-${index}`} className="w-4 h-4 text-muted-foreground mx-2" />
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}