"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Pause, Play, User, Bot } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { MainLayout } from "@/components/main-layout"

import { ArtifactsList } from "./artifacts-list"
import type { Artifact } from "@/lib/types"
import { TasksList } from "./tasks-list"
import type { Task } from "@/lib/types"
import { StageConfig } from "./stage-config"


export interface BaseStagePageProps {
  stageName: string
  currentTask: string
  agentName: string
  hitlRequired: boolean
  artifacts?: Artifact[]
  tasks?: Task[]
  onPause?: () => void
  onResume?: () => void
}

export function BaseStagePage({
  stageName,
  currentTask,
  agentName,
  hitlRequired,
  artifacts,
  tasks,
  onPause,
  onResume,
}: BaseStagePageProps) {
  return (
    <MainLayout>
      <div className="p-4 md:p-8 space-y-6">
        {/* Stage Banner */}
        <Card>
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <CardTitle className="text-2xl">{stageName} Stage</CardTitle>
                <CardDescription className="mt-2">
                  Current task: {currentTask}
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                {hitlRequired && (
                  <Badge variant="destructive" className="flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Human-in-the-Loop Required
                  </Badge>
                )}
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={onResume}>
                    <Play className="w-4 h-4 mr-2" />
                    Resume
                  </Button>
                  <Button variant="secondary" size="sm" onClick={onPause}>
                    <Pause className="w-4 h-4 mr-2" />
                    Pause
                  </Button>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-4 mt-4">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm">Agent: {agentName}</span>
              </div>
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm text-green-600">Active</span>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Main Content Tabs */}
        <Tabs defaultValue="progress" className="w-full">
          <TabsList className="mb-0">
            <TabsTrigger value="progress">Progress</TabsTrigger>
            <TabsTrigger value="config">Configuration</TabsTrigger>
          </TabsList>

          <TabsContent value="progress" className="space-y-6 p-6">
            <div className="grid gap-6 md:grid-cols-2">
              {/* Tasks Section */}
              <Card>
                <CardHeader>
                  <CardTitle>Tasks</CardTitle>
                  <CardDescription>A chronological list of tasks performed in this stage.</CardDescription>
                </CardHeader>
                <CardContent>
                  {tasks && tasks.length > 0 ? (
                    <TasksList tasks={tasks} />
                  ) : (
                    <p className="text-sm text-muted-foreground">No tasks available.</p>
                  )}
                </CardContent>
              </Card>

              {/* Artifacts Section */}
              <Card>
                <CardHeader>
                  <CardTitle>Artifacts</CardTitle>
                  <CardDescription>A list of all artifacts generated in this stage.</CardDescription>
                </CardHeader>
                <CardContent>
                  {artifacts && artifacts.length > 0 ? (
                    <ArtifactsList artifacts={artifacts} />
                  ) : (
                    <p className="text-sm text-muted-foreground">No artifacts available.</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="config" className="p-6">
            <StageConfig stageName={stageName} />
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  )
}