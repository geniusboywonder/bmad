"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Settings, Activity } from "lucide-react"
import { cn } from "@/lib/utils"
import { Project } from "@/lib/services/api/types"
import CopilotChat from "@/components/chat/copilot-chat"
import { ProjectProcessSummary } from "@/components/projects/project-process-summary"
import { ProjectBreadcrumb } from "@/components/navigation/project-breadcrumb"
import { useEffect } from "react"

interface ProjectWorkspaceProps {
  project: Project;
  onBack: () => void;
}

const getStatusBadgeClasses = (status: string) => {
  switch (status?.toLowerCase()) {
    case 'active':
    case 'running':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'paused':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'completed':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case 'failed':
    case 'error':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

export function ProjectWorkspace({ project, onBack }: ProjectWorkspaceProps) {
  // Add keyboard shortcut support
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onBack();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onBack]);

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header with navigation and project info */}
      <header className="space-y-4 p-6 border-b border-border bg-card">
        {/* Breadcrumb Navigation */}
        <ProjectBreadcrumb />

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              onClick={onBack}
              className="flex items-center gap-2 hover:bg-accent"
              title="Back to Projects (Press Escape)"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Projects
            </Button>
            <div className="border-l border-border pl-4">
              <h1 className="text-2xl font-bold text-foreground">{project.name}</h1>
              <p className="text-sm text-muted-foreground">Active workspace</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Badge
              variant="outline"
              className={cn("text-xs font-medium", getStatusBadgeClasses(project.status))}
            >
              {project.status?.toUpperCase() || 'UNKNOWN'}
            </Badge>

            {project.progress !== undefined && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Activity className="w-4 h-4" />
                <span>{Math.round(project.progress)}% Complete</span>
              </div>
            )}

            <Button variant="outline" size="sm" className="gap-2">
              <Settings className="w-4 h-4" />
              Settings
            </Button>
          </div>
        </div>
      </header>

      {/* Main workspace: 50/50 Process Summary + Chat Interface */}
      <div className="flex-1 grid grid-cols-1 xl:grid-cols-2 gap-8 p-6 min-h-0">

        {/* Left Column: Process Summary (50% width) */}
        <div className="min-h-[500px]" data-testid="process-summary-section">
          <ProjectProcessSummary projectId={project.id} />
        </div>

        {/* Right Column: Chat Interface (50% width) */}
        <div className="min-h-[500px]" data-testid="chat-section">
          <CopilotChat projectId={project.id} />
        </div>
      </div>
    </div>
  );
}