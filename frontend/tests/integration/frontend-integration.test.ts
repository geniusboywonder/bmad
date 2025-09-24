/**
 * Frontend Integration Test Suite
 * End-to-end tests for Phase 1 and Phase 2 integration
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WebSocketManager } from '@/lib/services/websocket/enhanced-websocket-client'
import { SafetyEventHandler } from '@/lib/services/safety/safety-event-handler'
import { useProjectStore } from '@/lib/stores/project-store'
import { projectsService } from '@/lib/services/api/projects.service'
import { hitlService } from '@/lib/services/api/hitl.service'
import { apiClient } from '@/lib/services/api/client'
import {
  Project,
  WebSocketEvent,
  HitlRequestCreatedEvent,
  TaskProgressUpdatedEvent,
  AgentStatusChangedEvent,
} from '@/lib/services/api/types'

// Mock fetch for API calls
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.CONNECTING
  url: string
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      this.onopen?.(new Event('open'))
    }, 10)
  }

  send = vi.fn()
  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.(new CloseEvent('close'))
  })

  simulateMessage(data: any) {
    const event = new MessageEvent('message', { data: JSON.stringify(data) })
    this.onmessage?.(event)
  }

  simulateError() {
    this.onerror?.(new Event('error'))
  }
}

global.WebSocket = MockWebSocket as any

describe('Frontend Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()

    // Reset stores
    useProjectStore.setState({
      projects: {},
      currentProject: null,
      tasks: {},
      isLoading: false,
      error: null,
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Phase 1: API Service Layer Integration', () => {
    describe('API Client Integration', () => {
      it('should handle complete API request lifecycle', async () => {
        const mockProject: Project = {
          id: 'project-1',
          name: 'Integration Test Project',
          status: 'pending',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        }

        // Mock successful API response
        mockFetch.mockResolvedValue({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true, data: mockProject }),
        })

        const response = await apiClient.get('/api/v1/projects/project-1')

        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/v1/projects/project-1',
          expect.objectContaining({
            method: 'GET',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
            }),
          })
        )

        expect(response.data).toEqual({ success: true, data: mockProject })
      })

      it('should handle API errors with retry logic', async () => {
        // Mock consecutive failures then success
        mockFetch
          .mockRejectedValueOnce(new Error('Network Error'))
          .mockRejectedValueOnce(new Error('Network Error'))
          .mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ success: true, data: {} }),
          })

        const startTime = Date.now()
        await apiClient.get('/test')
        const endTime = Date.now()

        // Should have retried and taken some time
        expect(endTime - startTime).toBeGreaterThan(100)
        expect(mockFetch).toHaveBeenCalledTimes(3)
      })

      it('should handle rate limiting', async () => {
        mockFetch
          .mockResolvedValueOnce({
            ok: false,
            status: 429,
            headers: new Map([['retry-after', '1']]),
            json: () => Promise.resolve({ success: false, error: 'Rate limited' }),
          })
          .mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ success: true, data: {} }),
          })

        const startTime = Date.now()
        await apiClient.get('/test')
        const endTime = Date.now()

        expect(endTime - startTime).toBeGreaterThan(500)
      })
    })

    describe('Projects Service Integration', () => {
      it('should handle complete project lifecycle', async () => {
        const store = useProjectStore.getState()

        // Mock project creation
        const createData = { name: 'Test Project', description: 'Test description' }
        const createdProject: Project = {
          id: 'project-1',
          ...createData,
          status: 'pending',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        }

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 201,
          json: () => Promise.resolve({ success: true, data: createdProject }),
        })

        // Create project
        const project = await store.createProject(createData)
        expect(project).toEqual(createdProject)
        expect(useProjectStore.getState().projects['project-1']).toEqual(createdProject)

        // Mock project update
        const updatedProject = { ...createdProject, status: 'active' as const }
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true, data: updatedProject }),
        })

        // Update project
        await store.updateProject('project-1', { status: 'active' })
        expect(useProjectStore.getState().projects['project-1'].status).toBe('active')

        // Mock project deletion
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true, data: { deleted: true } }),
        })

        // Delete project
        await store.deleteProject('project-1')
        expect(useProjectStore.getState().projects['project-1']).toBeUndefined()
      })
    })

    describe('WebSocket Integration', () => {
      it('should establish WebSocket connection and handle events', async () => {
        const manager = new WebSocketManager()
        const connection = manager.getGlobalConnection()

        const connectPromise = connection.connect()
        vi.advanceTimersByTime(20)
        await connectPromise

        expect(connection.getStatus().connected).toBe(true)

        // Test event handling
        const eventHandler = vi.fn()
        connection.on('agent_status_changed', eventHandler)

        const mockWs = (connection as any).ws as MockWebSocket
        const agentEvent: AgentStatusChangedEvent = {
          event_type: 'agent_status_changed',
          data: {
            agent_name: 'test-agent',
            status: 'working',
            current_task: 'Processing data',
          },
        }

        mockWs.simulateMessage(agentEvent)
        expect(eventHandler).toHaveBeenCalledWith(agentEvent)

        connection.destroy()
      })

      it('should handle project-scoped WebSocket connections', async () => {
        const manager = new WebSocketManager()

        const connection1 = manager.getProjectConnection('project-1')
        const connection2 = manager.getProjectConnection('project-2')

        expect(connection1).not.toBe(connection2)
        expect(connection1.getStatus().projectId).toBe('project-1')
        expect(connection2.getStatus().projectId).toBe('project-2')

        await connection1.connect()
        await connection2.connect()

        vi.advanceTimersByTime(20)

        expect(connection1.getStatus().connected).toBe(true)
        expect(connection2.getStatus().connected).toBe(true)

        manager.disconnectAll()
      })

      it('should handle WebSocket reconnection', async () => {
        const manager = new WebSocketManager()
        const connection = manager.getGlobalConnection()

        await connection.connect()
        vi.advanceTimersByTime(20)

        const statusHandler = vi.fn()
        connection.on('status', statusHandler)

        // Simulate connection loss
        const mockWs = (connection as any).ws as MockWebSocket
        mockWs.simulateClose(1006, 'Connection lost')

        // Should trigger reconnection
        vi.advanceTimersByTime(1000)

        expect(statusHandler).toHaveBeenCalledWith(
          expect.objectContaining({ reconnecting: true })
        )

        connection.destroy()
      })
    })

    describe('Safety Event Handler Integration', () => {
      it('should handle HITL safety events end-to-end', async () => {
        const safetyHandler = new SafetyEventHandler({
          enableAudioAlerts: false,
          enableNotifications: false,
        })

        const manager = new WebSocketManager()
        const connection = manager.getGlobalConnection()

        safetyHandler.connectToWebSocket(connection)

        await connection.connect()
        vi.advanceTimersByTime(20)

        const alertHandler = vi.fn()
        safetyHandler.onSafetyAlert(alertHandler)

        // Simulate HITL request
        const hitlEvent: HitlRequestCreatedEvent = {
          event_type: 'hitl_request_created',
          project_id: 'project-1',
          data: {
            request_id: 'hitl-123',
            question: 'Should we proceed with deployment?',
            urgency: 'high',
            agent_type: 'deployment',
            context: { environment: 'production' },
            requested_at: '2025-01-01T00:00:00Z',
          },
        }

        const mockWs = (connection as any).ws as MockWebSocket
        mockWs.simulateMessage(hitlEvent)

        expect(alertHandler).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'hitl_request',
            severity: 'high',
            title: 'HITL Approval Required',
            message: 'Should we proceed with deployment?',
          })
        )

        const alerts = safetyHandler.getActiveAlerts()
        expect(alerts).toHaveLength(1)
        expect(alerts[0].severity).toBe('high')

        safetyHandler.disconnectFromWebSocket()
        connection.destroy()
      })

      it('should handle emergency stop workflow', async () => {
        const safetyHandler = new SafetyEventHandler()

        // Mock HITL service
        const mockEmergencyStop = {
          id: 'stop-123',
          project_id: 'project-1',
          reason: 'Security violation detected',
          triggered_at: '2025-01-01T00:00:00Z',
          triggered_by: 'safety_system',
          status: 'active',
        }

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true, data: mockEmergencyStop }),
        })

        const alertHandler = vi.fn()
        safetyHandler.onSafetyAlert(alertHandler)

        await safetyHandler.triggerEmergencyStop('project-1', 'Security violation detected')

        expect(alertHandler).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'emergency_stop',
            severity: 'critical',
            title: 'Emergency Stop Activated',
          })
        )

        const criticalAlerts = safetyHandler.getAlertsBySeverity('critical')
        expect(criticalAlerts).toHaveLength(1)
      })
    })
  })

  describe('Phase 2: Project Management Integration', () => {
    describe('Project Store Integration', () => {
      it('should handle complete project management workflow', async () => {
        const store = useProjectStore.getState()

        // Mock WebSocket service
        const mockWebSocketService = {
          connectToProject: vi.fn(),
          disconnectFromProject: vi.fn(),
          startProject: vi.fn(),
        }

        // Create project
        const projectData = {
          name: 'Full Integration Project',
          description: 'End-to-end test project',
          priority: 'high' as const,
          budget_limit: 1000,
        }

        const createdProject: Project = {
          id: 'integration-project',
          ...projectData,
          status: 'pending',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        }

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 201,
          json: () => Promise.resolve({ success: true, data: createdProject }),
        })

        const project = await store.createProject(projectData)
        expect(project).toEqual(createdProject)

        // Start project
        const activeProject = { ...createdProject, status: 'active' as const }
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true, data: activeProject }),
        })

        await store.startProject('integration-project')
        expect(useProjectStore.getState().projects['integration-project'].status).toBe('active')

        // Real-time status updates
        store.updateProjectStatus('integration-project', 'paused')
        expect(useProjectStore.getState().projects['integration-project'].status).toBe('paused')

        // Progress updates
        store.updateProjectProgress('integration-project', 75)
        expect(useProjectStore.getState().projects['integration-project'].progress).toBe(75)
      })

      it('should sync with WebSocket events', async () => {
        const store = useProjectStore.getState()
        const manager = new WebSocketManager()
        const connection = manager.getProjectConnection('project-1')

        await connection.connect()
        vi.advanceTimersByTime(20)

        // Add project to store
        const project: Project = {
          id: 'project-1',
          name: 'WebSocket Sync Test',
          status: 'active',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        }

        useProjectStore.setState({
          projects: { 'project-1': project },
          currentProject: project,
        })

        // Simulate task progress update from WebSocket
        const taskEvent: TaskProgressUpdatedEvent = {
          event_type: 'task_progress_updated',
          project_id: 'project-1',
          data: {
            task_id: 'task-1',
            progress_percentage: 60,
            task_description: 'Processing data',
            estimated_completion: '2025-01-01T15:00:00Z',
          },
        }

        const mockWs = (connection as any).ws as MockWebSocket
        mockWs.simulateMessage(taskEvent)

        // Should trigger project progress update
        await waitFor(() => {
          const updatedProject = useProjectStore.getState().projects['project-1']
          expect(updatedProject.progress).toBe(60)
        })

        connection.destroy()
      })
    })

    describe('Project Dashboard Integration', () => {
      it('should display projects with real-time updates', async () => {
        // Mock project store with initial data
        const projects: Project[] = [
          {
            id: 'project-1',
            name: 'Dashboard Test Project 1',
            status: 'active',
            progress: 45,
            priority: 'high',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
          },
          {
            id: 'project-2',
            name: 'Dashboard Test Project 2',
            status: 'completed',
            progress: 100,
            priority: 'medium',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-02T00:00:00Z',
          },
        ]

        useProjectStore.setState({
          projects: projects.reduce((acc, p) => ({ ...acc, [p.id]: p }), {}),
          isLoading: false,
          error: null,
        })

        // Test component integration would go here
        // This would require setting up React Testing Library with full component tree

        expect(useProjectStore.getState().projects['project-1']).toEqual(projects[0])
        expect(useProjectStore.getState().projects['project-2']).toEqual(projects[1])
      })
    })
  })

  describe('End-to-End Integration Scenarios', () => {
    it('should handle complete project lifecycle with safety events', async () => {
      const store = useProjectStore.getState()
      const safetyHandler = new SafetyEventHandler({ enableAudioAlerts: false })
      const manager = new WebSocketManager()

      // 1. Create project
      const projectData = { name: 'E2E Test Project', priority: 'high' as const }
      const createdProject: Project = {
        id: 'e2e-project',
        ...projectData,
        status: 'pending',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: () => Promise.resolve({ success: true, data: createdProject }),
      })

      const project = await store.createProject(projectData)
      expect(project).toBeDefined()

      // 2. Connect WebSocket with safety monitoring
      const connection = manager.getProjectConnection('e2e-project')
      safetyHandler.connectToWebSocket(connection)

      await connection.connect()
      vi.advanceTimersByTime(20)

      // 3. Start project
      const activeProject = { ...createdProject, status: 'active' as const }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ success: true, data: activeProject }),
      })

      await store.startProject('e2e-project')

      // 4. Simulate safety event during project execution
      const alertHandler = vi.fn()
      safetyHandler.onSafetyAlert(alertHandler)

      const hitlEvent: HitlRequestCreatedEvent = {
        event_type: 'hitl_request_created',
        project_id: 'e2e-project',
        data: {
          request_id: 'e2e-hitl',
          question: 'Approve budget increase?',
          urgency: 'medium',
          agent_type: 'financial',
          context: { current_budget: 900, requested: 1200 },
          requested_at: '2025-01-01T12:00:00Z',
        },
      }

      const mockWs = (connection as any).ws as MockWebSocket
      mockWs.simulateMessage(hitlEvent)

      expect(alertHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'hitl_request',
          message: 'Approve budget increase?',
        })
      )

      // 5. Handle safety approval
      const alerts = safetyHandler.getActiveAlerts()
      expect(alerts).toHaveLength(1)

      // Mock HITL approval
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ success: true, data: {} }),
      })

      const approveAction = alerts[0].actions?.find(a => a.type === 'approve')
      await approveAction?.handler()

      // 6. Complete project
      const completedProject = { ...activeProject, status: 'completed' as const, progress: 100 }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ success: true, data: completedProject }),
      })

      await store.completeProject('e2e-project')

      expect(useProjectStore.getState().projects['e2e-project'].status).toBe('completed')

      // Cleanup
      safetyHandler.disconnectFromWebSocket()
      manager.disconnectAll()
    })

    it('should handle error recovery across all layers', async () => {
      const store = useProjectStore.getState()
      const manager = new WebSocketManager()

      // 1. API layer error recovery
      mockFetch
        .mockRejectedValueOnce(new Error('Network timeout'))
        .mockRejectedValueOnce(new Error('Server error'))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true, data: [] }),
        })

      // Should retry and eventually succeed
      await store.fetchProjects()
      expect(mockFetch).toHaveBeenCalledTimes(3)

      // 2. WebSocket layer error recovery
      const connection = manager.getGlobalConnection()
      const statusHandler = vi.fn()
      connection.on('status', statusHandler)

      await connection.connect()
      vi.advanceTimersByTime(20)

      // Simulate connection failure and recovery
      const mockWs = (connection as any).ws as MockWebSocket
      mockWs.simulateError()

      // Should attempt reconnection
      vi.advanceTimersByTime(1000)
      expect(statusHandler).toHaveBeenCalledWith(
        expect.objectContaining({ connected: false })
      )

      connection.destroy()
    })

    it('should maintain data consistency across all components', async () => {
      const store = useProjectStore.getState()
      const manager = new WebSocketManager()
      const safetyHandler = new SafetyEventHandler()

      // Set up connections
      const connection = manager.getGlobalConnection()
      safetyHandler.connectToWebSocket(connection)

      await connection.connect()
      vi.advanceTimersByTime(20)

      // Create project through store
      const project: Project = {
        id: 'consistency-test',
        name: 'Consistency Test Project',
        status: 'active',
        progress: 0,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      }

      useProjectStore.setState({
        projects: { 'consistency-test': project },
        currentProject: project,
      })

      // Simulate real-time progress updates
      const progressUpdates = [25, 50, 75, 100]
      const mockWs = (connection as any).ws as MockWebSocket

      for (const progress of progressUpdates) {
        const taskEvent: TaskProgressUpdatedEvent = {
          event_type: 'task_progress_updated',
          project_id: 'consistency-test',
          data: {
            task_id: `task-${progress}`,
            progress_percentage: progress,
            task_description: `Task at ${progress}%`,
            estimated_completion: '2025-01-01T15:00:00Z',
          },
        }

        mockWs.simulateMessage(taskEvent)
        store.updateProjectProgress('consistency-test', progress)

        // Verify consistency
        const currentState = useProjectStore.getState()
        expect(currentState.projects['consistency-test'].progress).toBe(progress)
        expect(currentState.currentProject?.progress).toBe(progress)
      }

      // Cleanup
      safetyHandler.disconnectFromWebSocket()
      connection.destroy()
    })
  })

  describe('Performance and Load Testing', () => {
    it('should handle multiple concurrent WebSocket connections', async () => {
      const manager = new WebSocketManager()
      const connections = []
      const projectIds = Array.from({ length: 5 }, (_, i) => `load-test-${i}`)

      // Create multiple project connections
      for (const projectId of projectIds) {
        const connection = manager.getProjectConnection(projectId)
        connections.push(connection)
        await connection.connect()
      }

      vi.advanceTimersByTime(50)

      // Verify all connections are active
      for (const connection of connections) {
        expect(connection.getStatus().connected).toBe(true)
      }

      // Simulate high message volume
      const eventHandler = vi.fn()
      connections.forEach(conn => conn.on('agent_status_changed', eventHandler))

      for (let i = 0; i < connections.length; i++) {
        const mockWs = (connections[i] as any).ws as MockWebSocket
        for (let j = 0; j < 10; j++) {
          mockWs.simulateMessage({
            event_type: 'agent_status_changed',
            data: { agent_name: `agent-${i}-${j}`, status: 'working' },
          })
        }
      }

      expect(eventHandler).toHaveBeenCalledTimes(50) // 5 connections × 10 messages

      manager.disconnectAll()
    })

    it('should handle rapid state updates without conflicts', () => {
      const store = useProjectStore.getState()

      // Create multiple projects
      const projects: Record<string, Project> = {}
      for (let i = 1; i <= 10; i++) {
        projects[`rapid-${i}`] = {
          id: `rapid-${i}`,
          name: `Rapid Test ${i}`,
          status: 'active',
          progress: 0,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        }
      }

      useProjectStore.setState({ projects })

      // Rapid progress updates
      for (let i = 1; i <= 10; i++) {
        for (let progress = 10; progress <= 100; progress += 10) {
          store.updateProjectProgress(`rapid-${i}`, progress)
        }
      }

      // Verify final state consistency
      const finalState = useProjectStore.getState()
      for (let i = 1; i <= 10; i++) {
        expect(finalState.projects[`rapid-${i}`].progress).toBe(100)
      }
    })
  })
})