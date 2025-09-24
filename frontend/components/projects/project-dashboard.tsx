/**
 * Project Dashboard Component
 * Real-time project monitoring with status updates and lifecycle management
 */

"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Play,
  Pause,
  Square,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Users,
  DollarSign,
  Calendar,
  MoreVertical,
  Trash2,
  Edit,
  Eye
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useProjectStore, projectStoreSelectors } from '@/lib/stores/project-store';
import { useAppStore } from '@/lib/stores/app-store';
import { Project, ProjectStatus } from '@/lib/services/api/types';
import { ProjectCreationForm } from './project-creation-form';
import { LoadingSpinner } from '@/lib/services/api/loading-states';
import { useToast } from '@/hooks/use-toast';

interface ProjectCardProps {
  project: Project;
  onSelect: (project: Project) => void;
  onUpdate: (projectId: string, updates: Partial<Project>) => void;
  onDelete: (projectId: string) => void;
  isSelected?: boolean;
}

function ProjectCard({ project, onSelect, onUpdate, onDelete, isSelected = false }: ProjectCardProps) {
  const { toast } = useToast();

  const getStatusIcon = (status: ProjectStatus) => {
    switch (status) {
      case 'active': return <Play className="w-4 h-4 text-green-500" />;
      case 'paused': return <Pause className="w-4 h-4 text-yellow-500" />;
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-blue-500" />;
      case 'failed': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: ProjectStatus) => {
    switch (status) {
      case 'active': return 'default';
      case 'paused': return 'secondary';
      case 'completed': return 'default';
      case 'failed': return 'destructive';
      default: return 'outline';
    }
  };

  const handleStatusChange = async (newStatus: ProjectStatus) => {
    try {
      await onUpdate(project.id, { status: newStatus });
      toast({
        title: 'Status Updated',
        description: `Project status changed to ${newStatus}`,
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Update Failed',
        description: 'Failed to update project status',
        variant: 'destructive',
        duration: 3000,
      });
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown date';

    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      // If invalid date, try parsing as ISO string or return current date
      const fallbackDate = new Date();
      return fallbackDate.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    }

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getTimeElapsed = () => {
    if (!project.created_at) return 'Unknown';

    const start = new Date(project.created_at);
    if (isNaN(start.getTime())) {
      // If invalid date, show as just started
      return 'Just started';
    }

    const now = new Date();
    const diffHours = Math.floor((now.getTime() - start.getTime()) / (1000 * 60 * 60));

    if (diffHours < 1) return 'Just started';
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  return (
    <Card
      className={`cursor-pointer transition-all hover:shadow-md ${
        isSelected ? 'ring-2 ring-primary ring-offset-2' : ''
      }`}
      onClick={() => onSelect(project)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold">{project.name}</CardTitle>
            <div className="flex items-center space-x-2">
              {getStatusIcon(project.status)}
              <Badge variant={getStatusColor(project.status)} className="text-xs">
                {project.status.toUpperCase()}
              </Badge>
              <span className="text-xs text-muted-foreground">
                Created {formatDate(project.created_at)}
              </span>
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="sm">
                <MoreVertical className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onSelect(project)}>
                <Eye className="w-4 h-4 mr-2" />
                View Details
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Edit className="w-4 h-4 mr-2" />
                Edit Project
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {project.status === 'pending' && (
                <DropdownMenuItem onClick={() => handleStatusChange('active')}>
                  <Play className="w-4 h-4 mr-2" />
                  Start Project
                </DropdownMenuItem>
              )}
              {project.status === 'active' && (
                <DropdownMenuItem onClick={() => handleStatusChange('paused')}>
                  <Pause className="w-4 h-4 mr-2" />
                  Pause Project
                </DropdownMenuItem>
              )}
              {project.status === 'paused' && (
                <DropdownMenuItem onClick={() => handleStatusChange('active')}>
                  <Play className="w-4 h-4 mr-2" />
                  Resume Project
                </DropdownMenuItem>
              )}
              {['active', 'paused'].includes(project.status) && (
                <DropdownMenuItem onClick={() => handleStatusChange('completed')}>
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Complete Project
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDelete(project.id)}
                className="text-destructive"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Project
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {project.description && (
          <CardDescription className="line-clamp-2">
            {project.description}
          </CardDescription>
        )}

        {/* Progress Bar */}
        {project.progress !== undefined && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progress</span>
              <span>{Math.round(project.progress)}%</span>
            </div>
            <Progress value={project.progress} className="h-2" />
          </div>
        )}

        {/* Project Metrics */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <span className="text-muted-foreground">
              {getTimeElapsed()}
            </span>
          </div>

          {project.budget_limit && (
            <div className="flex items-center space-x-2">
              <DollarSign className="w-4 h-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                ${project.budget_limit}
              </span>
            </div>
          )}

          {project.estimated_duration && (
            <div className="flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                {project.estimated_duration}h est.
              </span>
            </div>
          )}

          {project.agent_config?.max_agents && (
            <div className="flex items-center space-x-2">
              <Users className="w-4 h-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                {project.agent_config.max_agents} agents
              </span>
            </div>
          )}
        </div>

        {/* Tags */}
        {project.tags && project.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {project.tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
            {project.tags.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{project.tags.length - 3} more
              </Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function ProjectDashboard() {
  const {
    fetchProjects,
    updateProject,
    deleteProject,
    selectProject,
    clearError
  } = useProjectStore();

  const projects = useProjectStore(projectStoreSelectors.projects);
  const currentProject = useProjectStore(projectStoreSelectors.currentProject);
  const isLoading = useProjectStore(projectStoreSelectors.isLoading);
  const error = useProjectStore(projectStoreSelectors.error);

  const { connection } = useAppStore();
  const { toast } = useToast();

  const [view, setView] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    // Fetch projects on component mount
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    // Clear errors after 5 seconds
    if (error) {
      const timer = setTimeout(clearError, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const handleProjectSelect = (project: Project) => {
    selectProject(project.id);
  };

  const handleProjectDelete = async (projectId: string) => {
    if (confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      try {
        await deleteProject(projectId);
        toast({
          title: 'Project Deleted',
          description: 'Project has been successfully deleted.',
          duration: 3000,
        });
      } catch (error) {
        toast({
          title: 'Delete Failed',
          description: 'Failed to delete project. Please try again.',
          variant: 'destructive',
          duration: 3000,
        });
      }
    }
  };

  const projectsList = Object.values(projects);
  const activeProjects = projectsList.filter(p => p.status === 'active');
  const completedProjects = projectsList.filter(p => p.status === 'completed');

  if (isLoading && projectsList.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner message="Loading projects..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Projects</h2>
          <p className="text-muted-foreground">
            Manage and monitor your agent-orchestrated projects
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-sm">
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${connection.connected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span>{connection.connected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>

          <ProjectCreationForm
            onSuccess={() => fetchProjects()}
            trigger={
              <Button>
                <Play className="w-4 h-4 mr-2" />
                New Project
              </Button>
            }
          />
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="border-destructive bg-destructive/5">
          <CardContent className="flex items-center space-x-2 p-4">
            <AlertTriangle className="w-4 h-4 text-destructive" />
            <span className="text-sm text-destructive">
              {typeof error === 'string' ? error : error?.message || 'An error occurred'}
            </span>
          </CardContent>
        </Card>
      )}

      {/* Project Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{projectsList.length}</p>
                <p className="text-xs text-muted-foreground">Total Projects</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <Play className="w-4 h-4 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{activeProjects.length}</p>
                <p className="text-xs text-muted-foreground">Active</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">{completedProjects.length}</p>
                <p className="text-xs text-muted-foreground">Completed</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-orange-100 dark:bg-orange-900 rounded-lg flex items-center justify-center">
                <DollarSign className="w-4 h-4 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  ${projectsList.reduce((total, p) => total + (p.budget_limit || 0), 0)}
                </p>
                <p className="text-xs text-muted-foreground">Total Budget</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Projects Grid */}
      {projectsList.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Calendar className="w-12 h-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No projects yet</h3>
            <p className="text-muted-foreground mb-6 max-w-md">
              Create your first project to start orchestrating agents and automating workflows.
            </p>
            <ProjectCreationForm
              onSuccess={() => fetchProjects()}
              trigger={
                <Button>
                  <Play className="w-4 h-4 mr-2" />
                  Create Your First Project
                </Button>
              }
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projectsList.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onSelect={handleProjectSelect}
              onUpdate={updateProject}
              onDelete={handleProjectDelete}
              isSelected={currentProject?.id === project.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}