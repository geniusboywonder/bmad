/**
 * Project Store Tests - Phase 2 Integration
 * Tests for project state management, API integration, and WebSocket synchronization
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useProjectStore, ProjectState, projectStoreSelectors } from './project-store'
import { projectsService } from '@/lib/services/api/projects.service'
import { websocketService } from '@/lib/services/websocket/websocket-service'
import { Project, ProjectStatus } from '@/lib/services/api/types'

// Mock the services
vi.mock('@/lib/services/api/projects.service', () => ({
  projectsService: {
    createProject: vi.fn(),
    updateProject: vi.fn(),
    deleteProject: vi.fn(),
    getProjects: vi.fn(),
    getProject: vi.fn(),
    startProject: vi.fn(),
  },
}))

vi.mock('@/lib/services/websocket/websocket-service', () => ({
  websocketService: {
    connectToProject: vi.fn(),
    disconnectFromProject: vi.fn(),
    startProject: vi.fn(),
    onStatusChange: vi.fn(),
  },
}))

const mockProjectsService = projectsService as any
const mockWebSocketService = websocketService as any

describe('ProjectStore', () => {
  let store: any

  beforeEach(() => {
    vi.clearAllMocks()
    store = useProjectStore.getState()
    useProjectStore.setState({
      projects: {},
      currentProject: null,
      tasks: {},
      isLoading: false,
      error: null,
    })
  })

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      expect(store.projects).toEqual({})
      expect(store.currentProject).toBeNull()
      expect(store.tasks).toEqual({})
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('Project Creation', () => {
    it('should create project successfully', async () => {
      const mockProject: Project = {
        id: 'project-1',
        name: 'Test Project',
        description: 'Test description',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      mockProjectsService.createProject.mockResolvedValue({
        success: true,
        data: mockProject,
      })

      const result = await store.createProject({
        name: 'Test Project',
        description: 'Test description',
      })

      expect(mockProjectsService.createProject).toHaveBeenCalledWith({
        name: 'Test Project',
        description: 'Test description',
      })

      expect(result).toEqual(mockProject)
      expect(useProjectStore.getState().projects['project-1']).toEqual(mockProject)
      expect(useProjectStore.getState().currentProject).toEqual(mockProject)
      expect(useProjectStore.getState().isLoading).toBe(false)
      expect(mockWebSocketService.connectToProject).toHaveBeenCalledWith('project-1')
    })

    it('should handle project creation failure', async () => {
      const errorMessage = 'Failed to create project'
      mockProjectsService.createProject.mockResolvedValue({
        success: false,
        error: errorMessage,
      })

      const result = await store.createProject({ name: 'Test Project' })

      expect(result).toBeNull()
      expect(useProjectStore.getState().error).toBe(errorMessage)
      expect(useProjectStore.getState().isLoading).toBe(false)
      expect(useProjectStore.getState().projects).toEqual({})
    })

    it('should handle project creation exception', async () => {
      const error = new Error('Network error')
      mockProjectsService.createProject.mockRejectedValue(error)

      const result = await store.createProject({ name: 'Test Project' })

      expect(result).toBeNull()
      expect(useProjectStore.getState().error).toBe('Network error')
      expect(useProjectStore.getState().isLoading).toBe(false)
    })
  })

  describe('Project Updates', () => {
    it('should update project successfully', async () => {
      // Setup initial project
      const initialProject: Project = {
        id: 'project-1',
        name: 'Initial Project',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'project-1': initialProject },
        currentProject: initialProject,
      })

      const updatedProject: Project = {
        ...initialProject,
        name: 'Updated Project',
        status: 'active',
        updated_at: '2025-01-01T01:00:00Z',
      }

      mockProjectsService.updateProject.mockResolvedValue({
        success: true,
        data: updatedProject,
      })

      await store.updateProject('project-1', { name: 'Updated Project', status: 'active' })

      expect(mockProjectsService.updateProject).toHaveBeenCalledWith('project-1', {
        name: 'Updated Project',
        status: 'active',
      })

      expect(useProjectStore.getState().projects['project-1']).toEqual(updatedProject)
      expect(useProjectStore.getState().currentProject).toEqual(updatedProject)
    })

    it('should handle project update failure', async () => {
      const errorMessage = 'Failed to update project'
      mockProjectsService.updateProject.mockResolvedValue({
        success: false,
        error: errorMessage,
      })

      await store.updateProject('project-1', { name: 'Updated Project' })

      expect(useProjectStore.getState().error).toBe(errorMessage)
    })

    it('should update non-current project without affecting currentProject', async () => {
      const project1: Project = {
        id: 'project-1',
        name: 'Project 1',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      const project2: Project = {
        id: 'project-2',
        name: 'Project 2',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'project-1': project1, 'project-2': project2 },
        currentProject: project1,
      })

      const updatedProject2 = { ...project2, name: 'Updated Project 2' }
      mockProjectsService.updateProject.mockResolvedValue({
        success: true,
        data: updatedProject2,
      })

      await store.updateProject('project-2', { name: 'Updated Project 2' })

      expect(useProjectStore.getState().projects['project-2']).toEqual(updatedProject2)
      expect(useProjectStore.getState().currentProject).toEqual(project1) // Unchanged
    })
  })

  describe('Project Deletion', () => {
    it('should delete project successfully', async () => {
      const project: Project = {
        id: 'project-1',
        name: 'Test Project',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'project-1': project },
        currentProject: project,
      })

      mockProjectsService.deleteProject.mockResolvedValue({ success: true })

      await store.deleteProject('project-1')

      expect(mockProjectsService.deleteProject).toHaveBeenCalledWith('project-1')
      expect(useProjectStore.getState().projects).toEqual({})
      expect(useProjectStore.getState().currentProject).toBeNull()
      expect(useProjectStore.getState().isLoading).toBe(false)
      expect(mockWebSocketService.disconnectFromProject).toHaveBeenCalledWith('project-1')
    })

    it('should handle project deletion failure', async () => {
      const errorMessage = 'Failed to delete project'
      mockProjectsService.deleteProject.mockResolvedValue({
        success: false,
        error: errorMessage,
      })

      await store.deleteProject('project-1')

      expect(useProjectStore.getState().error).toBe(errorMessage)
      expect(useProjectStore.getState().isLoading).toBe(false)
    })

    it('should delete non-current project without affecting currentProject', async () => {
      const project1: Project = {
        id: 'project-1',
        name: 'Project 1',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      const project2: Project = {
        id: 'project-2',
        name: 'Project 2',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'project-1': project1, 'project-2': project2 },
        currentProject: project1,
      })

      mockProjectsService.deleteProject.mockResolvedValue({ success: true })

      await store.deleteProject('project-2')

      expect(useProjectStore.getState().projects).toEqual({ 'project-1': project1 })
      expect(useProjectStore.getState().currentProject).toEqual(project1)
    })
  })

  describe('Project Selection', () => {
    it('should select existing project', async () => {
      const project: Project = {
        id: 'project-1',
        name: 'Test Project',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'project-1': project },
        currentProject: null,
      })

      await store.selectProject('project-1')

      expect(useProjectStore.getState().currentProject).toEqual(project)
      expect(mockWebSocketService.connectToProject).toHaveBeenCalledWith('project-1')
    })

    it('should fetch and select non-existing project', async () => {
      const project: Project = {
        id: 'project-1',
        name: 'Test Project',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      mockProjectsService.getProject.mockResolvedValue({
        success: true,
        data: project,
      })

      await store.selectProject('project-1')

      expect(mockProjectsService.getProject).toHaveBeenCalledWith('project-1')
      expect(useProjectStore.getState().projects['project-1']).toEqual(project)
      expect(useProjectStore.getState().currentProject).toEqual(project)
    })
  })

  describe('Project Fetching', () => {
    it('should fetch all projects successfully', async () => {
      const projects: Project[] = [
        {
          id: 'project-1',
          name: 'Project 1',
          status: 'pending',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'project-2',
          name: 'Project 2',
          status: 'active',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ]

      mockProjectsService.getProjects.mockResolvedValue({
        success: true,
        data: projects,
      })

      await store.fetchProjects()

      expect(mockProjectsService.getProjects).toHaveBeenCalled()
      expect(useProjectStore.getState().projects).toEqual({
        'project-1': projects[0],
        'project-2': projects[1],
      })
      expect(useProjectStore.getState().isLoading).toBe(false)
    })

    it('should handle fetch projects failure', async () => {
      const errorMessage = 'Failed to fetch projects'
      mockProjectsService.getProjects.mockResolvedValue({
        success: false,
        error: errorMessage,
      })

      await store.fetchProjects()

      expect(useProjectStore.getState().error).toBe(errorMessage)
      expect(useProjectStore.getState().isLoading).toBe(false)
    })

    it('should fetch single project successfully', async () => {
      const project: Project = {
        id: 'project-1',
        name: 'Test Project',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      mockProjectsService.getProject.mockResolvedValue({
        success: true,
        data: project,
      })

      await store.fetchProject('project-1')

      expect(mockProjectsService.getProject).toHaveBeenCalledWith('project-1')
      expect(useProjectStore.getState().projects['project-1']).toEqual(project)
      expect(useProjectStore.getState().currentProject).toEqual(project)
    })
  })

  describe('Project Lifecycle Management', () => {
    it('should start project successfully', async () => {
      const project: Project = {
        id: 'project-1',
        name: 'Test Project',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      const startedProject: Project = {
        ...project,
        status: 'active',
        updated_at: '2025-01-01T01:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'project-1': project },
        currentProject: project,
      })

      mockProjectsService.startProject.mockResolvedValue({
        success: true,
        data: startedProject,
      })

      await store.startProject('project-1')

      expect(mockProjectsService.startProject).toHaveBeenCalledWith('project-1')
      expect(useProjectStore.getState().projects['project-1']).toEqual(startedProject)
      expect(useProjectStore.getState().currentProject).toEqual(startedProject)
      expect(mockWebSocketService.startProject).toHaveBeenCalledWith(
        'Project execution initiated',
        'project-1'
      )
    })

    it('should pause project', async () => {
      const project: Project = {
        id: 'project-1',
        name: 'Test Project',
        status: 'active',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      const pausedProject: Project = {
        ...project,
        status: 'paused',
        updated_at: '2025-01-01T01:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'project-1': project },
        currentProject: project,
      })

      mockProjectsService.updateProject.mockResolvedValue({
        success: true,
        data: pausedProject,
      })

      await store.pauseProject('project-1')

      expect(mockProjectsService.updateProject).toHaveBeenCalledWith('project-1', {
        status: 'paused',
      })
    })

    it('should complete project', async () => {
      const project: Project = {
        id: 'project-1',
        name: 'Test Project',
        status: 'active',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      const completedProject: Project = {
        ...project,
        status: 'completed',
        updated_at: '2025-01-01T01:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'project-1': project },
        currentProject: project,
      })

      mockProjectsService.updateProject.mockResolvedValue({
        success: true,
        data: completedProject,
      })

      await store.completeProject('project-1')

      expect(mockProjectsService.updateProject).toHaveBeenCalledWith('project-1', {
        status: 'completed',
      })
    })
  })

  describe('Real-time Updates', () => {
    it('should update project status', () => {
      const project: Project = {
        id: 'project-1',
        name: 'Test Project',
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'project-1': project },
        currentProject: project,
      })

      store.updateProjectStatus('project-1', 'active')

      const state = useProjectStore.getState()
      expect(state.projects['project-1'].status).toBe('active')
      expect(state.currentProject?.status).toBe('active')
    })

    it('should update project progress', () => {
      const project: Project = {
        id: 'project-1',
        name: 'Test Project',
        status: 'active',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'project-1': project },
        currentProject: project,
      })

      store.updateProjectProgress('project-1', 75)

      const state = useProjectStore.getState()
      expect(state.projects['project-1'].progress).toBe(75)
      expect(state.currentProject?.progress).toBe(75)
    })

    it('should not update non-existent project', () => {
      const initialState = useProjectStore.getState()

      store.updateProjectStatus('non-existent', 'active')

      expect(useProjectStore.getState()).toEqual(initialState)
    })
  })

  describe('Task Management', () => {
    it('should add task', () => {
      const task = {
        id: 'task-1',
        project_id: 'project-1',
        name: 'Test Task',
        status: 'pending' as const,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      store.addTask(task)

      expect(useProjectStore.getState().tasks['task-1']).toEqual(task)
    })

    it('should update task', () => {
      const task = {
        id: 'task-1',
        project_id: 'project-1',
        name: 'Test Task',
        status: 'pending' as const,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      useProjectStore.setState({
        tasks: { 'task-1': task },
      })

      store.updateTask('task-1', { name: 'Updated Task', status: 'active' })

      const updatedTask = useProjectStore.getState().tasks['task-1']
      expect(updatedTask.name).toBe('Updated Task')
      expect(updatedTask.status).toBe('active')
    })

    it('should update task progress', () => {
      const task = {
        id: 'task-1',
        project_id: 'project-1',
        name: 'Test Task',
        status: 'active' as const,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      useProjectStore.setState({
        tasks: { 'task-1': task },
      })

      store.updateTaskProgress('task-1', 50)

      expect(useProjectStore.getState().tasks['task-1'].progress).toBe(50)
    })

    it('should not update non-existent task', () => {
      const initialState = useProjectStore.getState()

      store.updateTask('non-existent', { name: 'Updated' })

      expect(useProjectStore.getState()).toEqual(initialState)
    })
  })

  describe('Utility Functions', () => {
    it('should clear error', () => {
      useProjectStore.setState({ error: 'Test error' })

      store.clearError()

      expect(useProjectStore.getState().error).toBeNull()
    })

    it('should reset store', () => {
      useProjectStore.setState({
        projects: { 'project-1': {} as Project },
        currentProject: {} as Project,
        tasks: { 'task-1': {} as any },
        isLoading: true,
        error: 'Test error',
      })

      store.reset()

      const state = useProjectStore.getState()
      expect(state.projects).toEqual({})
      expect(state.currentProject).toBeNull()
      expect(state.tasks).toEqual({})
      expect(state.isLoading).toBe(false)
      expect(state.error).toBeNull()
    })
  })

  describe('Store Selectors', () => {
    it('should provide correct selectors', () => {
      const projects: Project[] = [
        {
          id: 'project-1',
          name: 'Active Project',
          status: 'active',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'project-2',
          name: 'Completed Project',
          status: 'completed',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'project-3',
          name: 'Pending Project',
          status: 'pending',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ]

      const tasks = [
        {
          id: 'task-1',
          project_id: 'project-1',
          name: 'Task 1',
          status: 'pending' as const,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'task-2',
          project_id: 'project-2',
          name: 'Task 2',
          status: 'active' as const,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ]

      const state: ProjectState = {
        projects: {
          'project-1': projects[0],
          'project-2': projects[1],
          'project-3': projects[2],
        },
        currentProject: projects[0],
        tasks: {
          'task-1': tasks[0],
          'task-2': tasks[1],
        },
        isLoading: false,
        error: null,
        // Methods (not tested in selectors)
        createProject: vi.fn(),
        updateProject: vi.fn(),
        deleteProject: vi.fn(),
        selectProject: vi.fn(),
        fetchProjects: vi.fn(),
        fetchProject: vi.fn(),
        startProject: vi.fn(),
        pauseProject: vi.fn(),
        completeProject: vi.fn(),
        updateProjectStatus: vi.fn(),
        updateProjectProgress: vi.fn(),
        addTask: vi.fn(),
        updateTask: vi.fn(),
        updateTaskProgress: vi.fn(),
        clearError: vi.fn(),
        reset: vi.fn(),
      }

      expect(projectStoreSelectors.projectsList(state)).toEqual(projects)
      expect(projectStoreSelectors.activeProjects(state)).toEqual([projects[0]])
      expect(projectStoreSelectors.completedProjects(state)).toEqual([projects[1]])
      expect(projectStoreSelectors.currentProjectTasks(state)).toEqual([tasks[0]])
      expect(projectStoreSelectors.currentProject(state)).toEqual(projects[0])
      expect(projectStoreSelectors.isLoading(state)).toBe(false)
      expect(projectStoreSelectors.error(state)).toBeNull()
    })

    it('should handle empty current project in selectors', () => {
      const state: ProjectState = {
        projects: {},
        currentProject: null,
        tasks: {},
        isLoading: false,
        error: null,
        // Methods
        createProject: vi.fn(),
        updateProject: vi.fn(),
        deleteProject: vi.fn(),
        selectProject: vi.fn(),
        fetchProjects: vi.fn(),
        fetchProject: vi.fn(),
        startProject: vi.fn(),
        pauseProject: vi.fn(),
        completeProject: vi.fn(),
        updateProjectStatus: vi.fn(),
        updateProjectProgress: vi.fn(),
        addTask: vi.fn(),
        updateTask: vi.fn(),
        updateTaskProgress: vi.fn(),
        clearError: vi.fn(),
        reset: vi.fn(),
      }

      expect(projectStoreSelectors.currentProjectTasks(state)).toEqual([])
    })
  })
})