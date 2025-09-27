"use client"

import { useAppStore } from "@/lib/stores/app-store"
import { useProjectStore } from "@/lib/stores/project-store"
import { useNavigationStore } from "@/lib/stores/navigation-store"
import { MainLayout } from "@/components/main-layout"
import { ProjectDashboard } from "@/components/projects/project-dashboard"
import { ProjectWorkspace } from "@/components/projects/project-workspace"
import { RecentActivities } from "@/components/mockups/recent-activities"
import { Button } from "@/components/ui/button"
import { useEffect } from "react"
import { cn } from "@/lib/utils"

function ProjectHeader() {
  return (
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
  );
}

export default function HomePage() {
  const { addMessage } = useAppStore()
  const { projects } = useProjectStore()
  const {
    currentView,
    selectedProjectId,
    isTransitioning,
    navigateToProject,
    navigateToDashboard
  } = useNavigationStore()

  // Get selected project from store
  const selectedProject = selectedProjectId ? projects[selectedProjectId] : null;

  useEffect(() => {
    // Add welcome message on first load
    addMessage({
      type: "system",
      agent: "BMAD System",
      content: "Welcome to BotArmy Agentic Builder. Create a project to begin orchestrating your AI agents."
    })
  }, [addMessage])

  const handleSelectProject = (projectId: string) => {
    navigateToProject(projectId);
  };

  const handleBackToDashboard = () => {
    navigateToDashboard();
  };

  return (
    <MainLayout>
      <div className={cn(
        "transition-opacity duration-300",
        isTransitioning && "opacity-50"
      )}>
        {currentView === 'dashboard' ? (
          <div className="p-6 space-y-8">
            <ProjectHeader />

            {/* Project Management Dashboard */}
            <div className="space-y-6">
              <ProjectDashboard onSelectProject={handleSelectProject} />
            </div>

            {/* Activity Timeline */}
            <div className="space-y-4">
              <div className="border-t border-border pt-8">
                <h2 className="text-xl font-semibold text-foreground mb-4">Activity Timeline</h2>
                <RecentActivities />
              </div>
            </div>
          </div>
        ) : currentView === 'project-workspace' && selectedProject ? (
          <ProjectWorkspace
            project={selectedProject}
            onBack={handleBackToDashboard}
          />
        ) : (
          <div className="p-6 flex items-center justify-center min-h-[400px]">
            <div className="text-center space-y-4">
              <h2 className="text-xl font-semibold text-muted-foreground">Project Not Found</h2>
              <p className="text-sm text-muted-foreground">
                The selected project could not be loaded.
              </p>
              <Button onClick={handleBackToDashboard} variant="outline">
                Return to Dashboard
              </Button>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  )
}
