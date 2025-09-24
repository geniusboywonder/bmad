"use client"

import { useAppStore } from "@/lib/stores/app-store"
import { useProjectStore } from "@/lib/stores/project-store"
import { MainLayout } from "@/components/main-layout"
import { ProjectDashboard } from "@/components/projects/project-dashboard"
import { EnhancedChatInterface } from "@/components/chat/enhanced-chat-interface"
import { RecentActivities } from "@/components/mockups/recent-activities"
import CopilotChat from "@/components/chat/copilot-chat"
import { useEffect } from "react"

export default function HomePage() {
  const { addMessage } = useAppStore()
  const { currentProject } = useProjectStore()

  useEffect(() => {
    // Add welcome message on first load
    addMessage({
      type: "system",
      agent: "BMAD System",
      content: "Welcome to BotArmy Agentic Builder. Create a project to begin orchestrating your AI agents."
    })
  }, [])

  return (
    <MainLayout>
      <div className="p-6 space-y-8">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-foreground">BotArmy Agentic Builder</h1>
              <p className="text-lg text-muted-foreground">
                Multi-agent orchestration platform with real-time monitoring and HITL safety controls.
              </p>
            </div>
          </div>
        </div>

        {/* Project Management Dashboard */}
        <div className="space-y-6">
          <ProjectDashboard />
        </div>

        {/* Current Project Details & Chat */}
        {currentProject && (
          <div className="grid gap-8 grid-cols-1 xl:grid-cols-2">
            <div className="min-h-[500px]">
              <div className="bg-card border rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4">
                  Project: {currentProject.name}
                </h3>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Status:</span>
                      <span className="ml-2 font-medium">{currentProject.status}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Progress:</span>
                      <span className="ml-2 font-medium">{currentProject.progress || 0}%</span>
                    </div>
                    {currentProject.budget_limit && (
                      <div>
                        <span className="text-muted-foreground">Budget:</span>
                        <span className="ml-2 font-medium">${currentProject.budget_limit}</span>
                      </div>
                    )}
                    {currentProject.estimated_duration && (
                      <div>
                        <span className="text-muted-foreground">Duration:</span>
                        <span className="ml-2 font-medium">{currentProject.estimated_duration}h</span>
                      </div>
                    )}
                  </div>
                  {currentProject.description && (
                    <div>
                      <span className="text-muted-foreground">Description:</span>
                      <p className="mt-1 text-sm">{currentProject.description}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="min-h-[500px]">
              <CopilotChat projectId={currentProject.id} />
            </div>
          </div>
        )}

        {/* Activity Timeline */}
        <div className="space-y-4">
          <div className="border-t border-border pt-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">Activity Timeline</h2>
            <RecentActivities />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
