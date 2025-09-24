/**
 * Project Store - Backend Integrated State Management
 * Manages project lifecycle, real-time status, and WebSocket events
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { projectsService } from '@/lib/services/api/projects.service';
import { websocketService } from '@/lib/services/websocket/websocket-service';
import { Project, Task, ProjectStatus, TaskStatus } from '@/lib/services/api/types';

export interface ProjectState {
  // Project Data
  projects: Record<string, Project>;
  currentProject: Project | null;
  isLoading: boolean;
  error: string | { code: string; message: string; details?: any } | null;

  // Project Lifecycle
  createProject: (projectData: Partial<Project>) => Promise<Project | null>;
  updateProject: (projectId: string, updates: Partial<Project>) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
  selectProject: (projectId: string) => Promise<void>;

  // Project Management
  fetchProjects: () => Promise<void>;
  fetchProject: (projectId: string) => Promise<void>;
  startProject: (projectId: string) => Promise<void>;
  pauseProject: (projectId: string) => Promise<void>;
  completeProject: (projectId: string) => Promise<void>;

  // Real-time Updates
  updateProjectStatus: (projectId: string, status: ProjectStatus) => void;
  updateProjectProgress: (projectId: string, progress: number) => void;

  // Tasks Management
  tasks: Record<string, Task>;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  updateTaskProgress: (taskId: string, progress: number) => void;

  // Utility
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  projects: {},
  currentProject: null,
  tasks: {},
  isLoading: false,
  error: null,
};

export const useProjectStore = create<ProjectState>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,

    // Project Lifecycle Methods
    createProject: async (projectData) => {
      set({ isLoading: true, error: null });

      try {
        const response = await projectsService.createProject(projectData);

        if (response.success && response.data) {
          const newProject = response.data;

          set((state) => ({
            projects: { ...state.projects, [newProject.id]: newProject },
            currentProject: newProject,
            isLoading: false,
          }));

          // Connect to project-specific WebSocket
          websocketService.connectToProject(newProject.id);

          return newProject;
        } else {
          set({ error: response.error || 'Failed to create project', isLoading: false });
          return null;
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        set({ error: errorMessage, isLoading: false });
        return null;
      }
    },

    updateProject: async (projectId, updates) => {
      try {
        const response = await projectsService.updateProject(projectId, updates);

        if (response.success && response.data) {
          const updatedProject = response.data;

          set((state) => ({
            projects: { ...state.projects, [projectId]: updatedProject },
            currentProject: state.currentProject?.id === projectId ? updatedProject : state.currentProject,
          }));
        } else {
          set({ error: response.error || 'Failed to update project' });
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        set({ error: errorMessage });
      }
    },

    deleteProject: async (projectId) => {
      set({ isLoading: true, error: null });

      try {
        const response = await projectsService.deleteProject(projectId);

        if (response.success) {
          set((state) => {
            const { [projectId]: deleted, ...remainingProjects } = state.projects;
            return {
              projects: remainingProjects,
              currentProject: state.currentProject?.id === projectId ? null : state.currentProject,
              isLoading: false,
            };
          });

          // Disconnect from project WebSocket
          websocketService.disconnectFromProject(projectId);
        } else {
          set({ error: response.error || 'Failed to delete project', isLoading: false });
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        set({ error: errorMessage, isLoading: false });
      }
    },

    selectProject: async (projectId) => {
      const state = get();
      const project = state.projects[projectId];

      if (project) {
        set({ currentProject: project });
        // Connect to project-specific WebSocket
        websocketService.connectToProject(projectId);
      } else {
        // Fetch project if not in store
        await get().fetchProject(projectId);
      }
    },

    // Project Management Methods
    fetchProjects: async () => {
      set({ isLoading: true, error: null });

      try {
        const response = await projectsService.getProjects();

        if (response.success && response.data) {
          const projectsArray = response.data;
          const projectsMap = projectsArray.reduce((acc, project) => {
            acc[project.id] = project;
            return acc;
          }, {} as Record<string, Project>);

          set({ projects: projectsMap, isLoading: false });
        } else {
          set({ error: response.error || 'Failed to fetch projects', isLoading: false });
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        set({ error: errorMessage, isLoading: false });
      }
    },

    fetchProject: async (projectId) => {
      set({ isLoading: true, error: null });

      try {
        const response = await projectsService.getProject(projectId);

        if (response.success && response.data) {
          const project = response.data;

          set((state) => ({
            projects: { ...state.projects, [projectId]: project },
            currentProject: project,
            isLoading: false,
          }));
        } else {
          set({ error: response.error || 'Failed to fetch project', isLoading: false });
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        set({ error: errorMessage, isLoading: false });
      }
    },

    startProject: async (projectId) => {
      try {
        const response = await projectsService.startProject(projectId);

        if (response.success && response.data) {
          const updatedProject = response.data;

          set((state) => ({
            projects: { ...state.projects, [projectId]: updatedProject },
            currentProject: state.currentProject?.id === projectId ? updatedProject : state.currentProject,
          }));

          // Send start command via WebSocket
          websocketService.startProject('Project execution initiated', projectId);
        } else {
          set({ error: response.error || 'Failed to start project' });
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        set({ error: errorMessage });
      }
    },

    pauseProject: async (projectId) => {
      await get().updateProject(projectId, { status: 'paused' });
    },

    completeProject: async (projectId) => {
      await get().updateProject(projectId, { status: 'completed' });
    },

    // Real-time Update Methods
    updateProjectStatus: (projectId, status) => {
      set((state) => {
        const project = state.projects[projectId];
        if (!project) return state;

        const updatedProject = { ...project, status };

        return {
          projects: { ...state.projects, [projectId]: updatedProject },
          currentProject: state.currentProject?.id === projectId ? updatedProject : state.currentProject,
        };
      });
    },

    updateProjectProgress: (projectId, progress) => {
      set((state) => {
        const project = state.projects[projectId];
        if (!project) return state;

        const updatedProject = { ...project, progress };

        return {
          projects: { ...state.projects, [projectId]: updatedProject },
          currentProject: state.currentProject?.id === projectId ? updatedProject : state.currentProject,
        };
      });
    },

    // Task Management Methods
    addTask: (task) => {
      set((state) => ({
        tasks: { ...state.tasks, [task.id]: task },
      }));
    },

    updateTask: (taskId, updates) => {
      set((state) => {
        const task = state.tasks[taskId];
        if (!task) return state;

        return {
          tasks: { ...state.tasks, [taskId]: { ...task, ...updates } },
        };
      });
    },

    updateTaskProgress: (taskId, progress) => {
      get().updateTask(taskId, { progress });
    },

    // Utility Methods
    clearError: () => set({ error: null }),

    reset: () => set(initialState),
  }))
);

// WebSocket Event Listeners
if (typeof window !== 'undefined') {
  // Subscribe to WebSocket project events
  websocketService.onStatusChange((status) => {
    console.log('[ProjectStore] WebSocket status changed:', status);
  });

  // Listen for project-related WebSocket events
  const unsubscribe = useProjectStore.subscribe(
    (state) => state.currentProject?.id,
    (projectId) => {
      if (projectId) {
        console.log(`[ProjectStore] Monitoring project: ${projectId}`);
      }
    }
  );
}

// Export store selectors for optimized re-renders
export const projectStoreSelectors = {
  projects: (state: ProjectState) => state.projects,
  currentProject: (state: ProjectState) => state.currentProject,
  isLoading: (state: ProjectState) => state.isLoading,
  error: (state: ProjectState) => state.error,
  tasks: (state: ProjectState) => state.tasks,

  // Derived selectors
  projectsList: (state: ProjectState) => Object.values(state.projects),
  activeProjects: (state: ProjectState) =>
    Object.values(state.projects).filter(p => p.status === 'active'),
  completedProjects: (state: ProjectState) =>
    Object.values(state.projects).filter(p => p.status === 'completed'),
  currentProjectTasks: (state: ProjectState) =>
    state.currentProject ?
      Object.values(state.tasks).filter(t => t.project_id === state.currentProject!.id) :
      [],
};