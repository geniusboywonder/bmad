/**
 * Projects Service Tests - Phase 1 Integration
 * Tests for project lifecycle management API integration
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { projectsService } from './projects.service'
import { apiClient } from './client'
import { Project } from './types'

// Mock the API client
vi.mock('./client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockApiClient = apiClient as any

describe('ProjectsService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getProjects', () => {
    it('should fetch all projects successfully', async () => {
      const mockProjects: Project[] = [
        {
          id: '1',
          name: 'Test Project 1',
          description: 'Test description',
          status: 'active',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
        {
          id: '2',
          name: 'Test Project 2',
          status: 'completed',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ]

      mockApiClient.get.mockResolvedValue({
        data: { success: true, data: mockProjects }
      })

      const result = await projectsService.getProjects()

      expect(mockApiClient.get).toHaveBeenCalledWith('/api/v1/projects')
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockProjects)
    })

    it('should handle API errors', async () => {
      const errorMessage = 'Failed to fetch projects'
      mockApiClient.get.mockRejectedValue(new Error(errorMessage))

      const result = await projectsService.getProjects()

      expect(result.success).toBe(false)
      expect(result.error).toBe(errorMessage)
    })
  })

  describe('getProject', () => {
    it('should fetch a single project successfully', async () => {
      const projectId = 'test-id'
      const mockProject: Project = {
        id: projectId,
        name: 'Test Project',
        status: 'active',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      mockApiClient.get.mockResolvedValue({
        data: { success: true, data: mockProject }
      })

      const result = await projectsService.getProject(projectId)

      expect(mockApiClient.get).toHaveBeenCalledWith(`/api/v1/projects/${projectId}`)
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockProject)
    })

    it('should handle project not found', async () => {
      const projectId = 'non-existent'
      const errorMessage = 'Project not found'

      mockApiClient.get.mockResolvedValue({
        data: { success: false, error: errorMessage }
      })

      const result = await projectsService.getProject(projectId)

      expect(result.success).toBe(false)
      expect(result.error).toBe(errorMessage)
    })
  })

  describe('createProject', () => {
    it('should create a project successfully', async () => {
      const projectData = {
        name: 'New Project',
        description: 'Project description',
        priority: 'high' as const,
        budget_limit: 1000,
      }

      const mockCreatedProject: Project = {
        id: 'new-id',
        ...projectData,
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      mockApiClient.post.mockResolvedValue({
        data: { success: true, data: mockCreatedProject }
      })

      const result = await projectsService.createProject(projectData)

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/projects', projectData)
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockCreatedProject)
    })

    it('should handle validation errors', async () => {
      const invalidProjectData = { name: '' } // Invalid: empty name

      const validationError = {
        success: false,
        error: 'Validation failed',
        details: {
          name: ['Name is required']
        }
      }

      mockApiClient.post.mockResolvedValue({
        data: validationError
      })

      const result = await projectsService.createProject(invalidProjectData)

      expect(result.success).toBe(false)
      expect(result.error).toBe('Validation failed')
      expect(result.details).toEqual({ name: ['Name is required'] })
    })
  })

  describe('updateProject', () => {
    it('should update a project successfully', async () => {
      const projectId = 'test-id'
      const updates = {
        name: 'Updated Name',
        status: 'paused' as const,
      }

      const mockUpdatedProject: Project = {
        id: projectId,
        name: 'Updated Name',
        status: 'paused',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T01:00:00Z',
      }

      mockApiClient.put.mockResolvedValue({
        data: { success: true, data: mockUpdatedProject }
      })

      const result = await projectsService.updateProject(projectId, updates)

      expect(mockApiClient.put).toHaveBeenCalledWith(`/api/v1/projects/${projectId}`, updates)
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockUpdatedProject)
    })

    it('should handle update conflicts', async () => {
      const projectId = 'test-id'
      const updates = { name: 'Updated Name' }
      const conflictError = 'Project was modified by another user'

      mockApiClient.put.mockResolvedValue({
        data: { success: false, error: conflictError }
      })

      const result = await projectsService.updateProject(projectId, updates)

      expect(result.success).toBe(false)
      expect(result.error).toBe(conflictError)
    })
  })

  describe('deleteProject', () => {
    it('should delete a project successfully', async () => {
      const projectId = 'test-id'

      mockApiClient.delete.mockResolvedValue({
        data: { success: true, data: { deleted: true } }
      })

      const result = await projectsService.deleteProject(projectId)

      expect(mockApiClient.delete).toHaveBeenCalledWith(`/api/v1/projects/${projectId}`)
      expect(result.success).toBe(true)
    })

    it('should handle deletion of active project', async () => {
      const projectId = 'active-project'
      const errorMessage = 'Cannot delete active project'

      mockApiClient.delete.mockResolvedValue({
        data: { success: false, error: errorMessage }
      })

      const result = await projectsService.deleteProject(projectId)

      expect(result.success).toBe(false)
      expect(result.error).toBe(errorMessage)
    })
  })

  describe('startProject', () => {
    it('should start a project successfully', async () => {
      const projectId = 'test-id'

      const mockStartedProject: Project = {
        id: projectId,
        name: 'Test Project',
        status: 'active',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T01:00:00Z',
      }

      mockApiClient.post.mockResolvedValue({
        data: { success: true, data: mockStartedProject }
      })

      const result = await projectsService.startProject(projectId)

      expect(mockApiClient.post).toHaveBeenCalledWith(`/api/v1/projects/${projectId}/start`)
      expect(result.success).toBe(true)
      expect(result.data?.status).toBe('active')
    })

    it('should handle starting already active project', async () => {
      const projectId = 'already-active'
      const errorMessage = 'Project is already active'

      mockApiClient.post.mockResolvedValue({
        data: { success: false, error: errorMessage }
      })

      const result = await projectsService.startProject(projectId)

      expect(result.success).toBe(false)
      expect(result.error).toBe(errorMessage)
    })
  })

  describe('getProjectStatus', () => {
    it('should fetch project status successfully', async () => {
      const projectId = 'test-id'
      const mockStatus = {
        status: 'active',
        progress: 75,
        agents_active: 3,
        current_phase: 'execution',
        estimated_completion: '2025-01-02T00:00:00Z',
      }

      mockApiClient.get.mockResolvedValue({
        data: { success: true, data: mockStatus }
      })

      const result = await projectsService.getProjectStatus(projectId)

      expect(mockApiClient.get).toHaveBeenCalledWith(`/api/v1/projects/${projectId}/status`)
      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockStatus)
    })

    it('should handle status fetch for non-existent project', async () => {
      const projectId = 'non-existent'
      const errorMessage = 'Project not found'

      mockApiClient.get.mockRejectedValue(new Error(errorMessage))

      const result = await projectsService.getProjectStatus(projectId)

      expect(result.success).toBe(false)
      expect(result.error).toBe(errorMessage)
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      const networkError = new Error('Network Error')
      mockApiClient.get.mockRejectedValue(networkError)

      const result = await projectsService.getProjects()

      expect(result.success).toBe(false)
      expect(result.error).toBe('Network Error')
    })

    it('should handle timeout errors', async () => {
      const timeoutError = new Error('Request timeout')
      mockApiClient.get.mockRejectedValue(timeoutError)

      const result = await projectsService.getProjects()

      expect(result.success).toBe(false)
      expect(result.error).toBe('Request timeout')
    })

    it('should handle server errors', async () => {
      const serverError = {
        response: {
          status: 500,
          data: { success: false, error: 'Internal server error' }
        }
      }
      mockApiClient.get.mockRejectedValue(serverError)

      const result = await projectsService.getProjects()

      expect(result.success).toBe(false)
      expect(result.error).toContain('server error')
    })
  })
})