/**
 * Enhanced WebSocket Client Tests - Phase 1 Integration
 * Tests for WebSocket connection, reconnection, and event handling
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { EnhancedWebSocketClient, WebSocketManager } from './enhanced-websocket-client'
import { WebSocketEventType } from '../api/types'

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
    // Simulate async connection
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

  // Test helper methods
  simulateMessage(data: any) {
    const event = new MessageEvent('message', { data: JSON.stringify(data) })
    this.onmessage?.(event)
  }

  simulateError() {
    this.onerror?.(new Event('error'))
  }

  simulateClose(code = 1000, reason = 'Normal closure') {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.(new CloseEvent('close', { code, reason }))
  }
}

// Replace global WebSocket with mock
global.WebSocket = MockWebSocket as any

describe('EnhancedWebSocketClient', () => {
  let client: EnhancedWebSocketClient
  let mockWs: MockWebSocket

  beforeEach(() => {
    vi.clearAllTimers()
    vi.useFakeTimers()

    client = new EnhancedWebSocketClient({
      url: 'ws://localhost:8000/ws',
      autoReconnect: true,
      maxReconnectAttempts: 3,
      reconnectInterval: 1000,
      heartbeatInterval: 30000,
    })
  })

  afterEach(() => {
    client.destroy()
    vi.useRealTimers()
  })

  describe('Connection Management', () => {
    it('should connect successfully', async () => {
      const connectPromise = client.connect()

      // Advance time to trigger connection
      vi.advanceTimersByTime(20)

      await connectPromise

      const status = client.getStatus()
      expect(status.connected).toBe(true)
      expect(status.reconnecting).toBe(false)
    })

    it('should handle connection failure', async () => {
      const statusHandler = vi.fn()
      client.on('status', statusHandler)

      // Override to simulate connection failure
      global.WebSocket = vi.fn().mockImplementation(() => {
        const ws = new MockWebSocket('ws://localhost:8000/ws')
        setTimeout(() => ws.simulateError(), 5)
        return ws
      }) as any

      await expect(client.connect()).rejects.toThrow()

      expect(statusHandler).toHaveBeenCalledWith(
        expect.objectContaining({ connected: false, error: expect.any(String) })
      )
    })

    it('should disconnect properly', async () => {
      await client.connect()
      vi.advanceTimersByTime(20)

      client.disconnect()

      const status = client.getStatus()
      expect(status.connected).toBe(false)
    })

    it('should destroy and cleanup resources', async () => {
      const eventHandler = vi.fn()
      client.on('agent_status_changed', eventHandler)

      await client.connect()
      vi.advanceTimersByTime(20)

      client.destroy()

      const status = client.getStatus()
      expect(status.connected).toBe(false)

      // Should not receive events after destroy
      global.WebSocket = vi.fn().mockImplementation(() => {
        const ws = new MockWebSocket('ws://localhost:8000/ws')
        setTimeout(() => ws.simulateMessage({ event_type: 'agent_status_changed', data: {} }), 5)
        return ws
      }) as any

      vi.advanceTimersByTime(10)
      expect(eventHandler).not.toHaveBeenCalled()
    })
  })

  describe('Auto-Reconnection', () => {
    it('should attempt reconnection on connection loss', async () => {
      await client.connect()
      vi.advanceTimersByTime(20)

      const connectSpy = vi.spyOn(client, 'connect')

      // Simulate connection loss
      const mockWs = (client as any).ws as MockWebSocket
      mockWs.simulateClose(1006, 'Connection lost')

      // Advance time to trigger reconnection
      vi.advanceTimersByTime(1000)

      expect(connectSpy).toHaveBeenCalled()
    })

    it('should use exponential backoff for reconnection', async () => {
      await client.connect()
      vi.advanceTimersByTime(20)

      const statusHandler = vi.fn()
      client.on('status', statusHandler)

      // Simulate multiple connection failures
      for (let i = 0; i < 3; i++) {
        const mockWs = (client as any).ws as MockWebSocket
        mockWs.simulateClose(1006, 'Connection lost')

        // Should wait exponentially longer each time
        const expectedDelay = Math.min(1000 * Math.pow(2, i), 30000)
        vi.advanceTimersByTime(expectedDelay - 100)

        // Should still be reconnecting
        expect(client.getStatus().reconnecting).toBe(true)

        vi.advanceTimersByTime(200)
      }
    })

    it('should stop reconnecting after max attempts', async () => {
      await client.connect()
      vi.advanceTimersByTime(20)

      // Override to always fail connection
      global.WebSocket = vi.fn().mockImplementation(() => {
        const ws = new MockWebSocket('ws://localhost:8000/ws')
        setTimeout(() => ws.simulateError(), 5)
        return ws
      }) as any

      // Simulate connection loss
      const mockWs = (client as any).ws as MockWebSocket
      mockWs.simulateClose(1006, 'Connection lost')

      // Advance through all reconnection attempts
      for (let i = 0; i < 4; i++) {
        vi.advanceTimersByTime(5000)
      }

      const status = client.getStatus()
      expect(status.reconnecting).toBe(false)
      expect(status.connected).toBe(false)
    })
  })

  describe('Event Handling', () => {
    beforeEach(async () => {
      await client.connect()
      vi.advanceTimersByTime(20)
    })

    it('should handle agent status events', async () => {
      const eventHandler = vi.fn()
      client.on('agent_status_changed', eventHandler)

      const eventData = {
        event_type: 'agent_status_changed',
        data: {
          agent_name: 'test-agent',
          status: 'working',
          current_task: 'processing data'
        }
      }

      const mockWs = (client as any).ws as MockWebSocket
      mockWs.simulateMessage(eventData)

      expect(eventHandler).toHaveBeenCalledWith(eventData)
    })

    it('should handle task progress events', async () => {
      const eventHandler = vi.fn()
      client.on('task_progress_updated', eventHandler)

      const eventData = {
        event_type: 'task_progress_updated',
        data: {
          task_id: 'task-123',
          progress_percentage: 75,
          task_description: 'Analyzing requirements'
        }
      }

      const mockWs = (client as any).ws as MockWebSocket
      mockWs.simulateMessage(eventData)

      expect(eventHandler).toHaveBeenCalledWith(eventData)
    })

    it('should handle HITL request events', async () => {
      const eventHandler = vi.fn()
      client.on('hitl_request_created', eventHandler)

      const eventData = {
        event_type: 'hitl_request_created',
        data: {
          request_id: 'hitl-123',
          question: 'Should we proceed with deployment?',
          urgency: 'high'
        }
      }

      const mockWs = (client as any).ws as MockWebSocket
      mockWs.simulateMessage(eventData)

      expect(eventHandler).toHaveBeenCalledWith(eventData)
    })

    it('should handle heartbeat/ping messages', async () => {
      const mockWs = (client as any).ws as MockWebSocket

      mockWs.simulateMessage({ type: 'ping' })

      expect(mockWs.send).toHaveBeenCalledWith(
        JSON.stringify({ type: 'pong', timestamp: expect.any(Number) })
      )
    })

    it('should remove event listeners when off is called', async () => {
      const eventHandler = vi.fn()
      client.on('agent_status_changed', eventHandler)
      client.off('agent_status_changed', eventHandler)

      const mockWs = (client as any).ws as MockWebSocket
      mockWs.simulateMessage({
        event_type: 'agent_status_changed',
        data: { agent_name: 'test' }
      })

      expect(eventHandler).not.toHaveBeenCalled()
    })
  })

  describe('Heartbeat Mechanism', () => {
    it('should send heartbeat messages', async () => {
      await client.connect()
      vi.advanceTimersByTime(20)

      const mockWs = (client as any).ws as MockWebSocket

      // Advance time to trigger heartbeat
      vi.advanceTimersByTime(30000)

      expect(mockWs.send).toHaveBeenCalledWith(
        JSON.stringify({ type: 'heartbeat', timestamp: expect.any(Number) })
      )
    })

    it('should detect connection loss via heartbeat timeout', async () => {
      await client.connect()
      vi.advanceTimersByTime(20)

      const statusHandler = vi.fn()
      client.on('status', statusHandler)

      // Don't respond to heartbeat
      vi.advanceTimersByTime(30000 + 10000) // heartbeat + timeout

      expect(statusHandler).toHaveBeenCalledWith(
        expect.objectContaining({ connected: false })
      )
    })
  })

  describe('Project-Scoped Connections', () => {
    it('should switch to project-specific URL', async () => {
      await client.connect()
      vi.advanceTimersByTime(20)

      await client.switchToProject('project-123')
      vi.advanceTimersByTime(20)

      // Should have created new connection with project URL
      expect(client.getStatus().projectId).toBe('project-123')
    })

    it('should handle project switching errors', async () => {
      await client.connect()
      vi.advanceTimersByTime(20)

      // Override to fail project connection
      global.WebSocket = vi.fn().mockImplementation((url) => {
        if (url.includes('project-123')) {
          const ws = new MockWebSocket(url)
          setTimeout(() => ws.simulateError(), 5)
          return ws
        }
        return new MockWebSocket(url)
      }) as any

      await expect(client.switchToProject('project-123')).rejects.toThrow()
    })
  })
})

describe('WebSocketManager', () => {
  let manager: WebSocketManager

  beforeEach(() => {
    manager = new WebSocketManager()
    vi.useFakeTimers()
  })

  afterEach(() => {
    manager.disconnectAll()
    vi.useRealTimers()
  })

  describe('Connection Management', () => {
    it('should create global connection', () => {
      const connection = manager.getGlobalConnection()

      expect(connection).toBeInstanceOf(EnhancedWebSocketClient)

      // Should return same instance on subsequent calls
      const connection2 = manager.getGlobalConnection()
      expect(connection2).toBe(connection)
    })

    it('should create project-specific connections', () => {
      const projectId = 'project-123'
      const connection = manager.getProjectConnection(projectId)

      expect(connection).toBeInstanceOf(EnhancedWebSocketClient)
      expect(connection.getStatus().projectId).toBe(projectId)

      // Should return same instance for same project
      const connection2 = manager.getProjectConnection(projectId)
      expect(connection2).toBe(connection)
    })

    it('should create separate connections for different projects', () => {
      const connection1 = manager.getProjectConnection('project-1')
      const connection2 = manager.getProjectConnection('project-2')

      expect(connection1).not.toBe(connection2)
      expect(connection1.getStatus().projectId).toBe('project-1')
      expect(connection2.getStatus().projectId).toBe('project-2')
    })

    it('should disconnect specific project', () => {
      const projectId = 'project-123'
      const connection = manager.getProjectConnection(projectId)
      const destroySpy = vi.spyOn(connection, 'destroy')

      manager.disconnectProject(projectId)

      expect(destroySpy).toHaveBeenCalled()
    })

    it('should disconnect all connections', () => {
      const globalConnection = manager.getGlobalConnection()
      const projectConnection1 = manager.getProjectConnection('project-1')
      const projectConnection2 = manager.getProjectConnection('project-2')

      const globalDestroySpy = vi.spyOn(globalConnection, 'destroy')
      const project1DestroySpy = vi.spyOn(projectConnection1, 'destroy')
      const project2DestroySpy = vi.spyOn(projectConnection2, 'destroy')

      manager.disconnectAll()

      expect(globalDestroySpy).toHaveBeenCalled()
      expect(project1DestroySpy).toHaveBeenCalled()
      expect(project2DestroySpy).toHaveBeenCalled()
    })
  })

  describe('URL Building', () => {
    it('should build global WebSocket URL', () => {
      const manager = new WebSocketManager()
      const url = (manager as any).buildWebSocketUrl()

      expect(url).toBe('ws://localhost:8000/ws')
    })

    it('should build project-specific WebSocket URL', () => {
      const manager = new WebSocketManager()
      const projectId = 'project-123'
      const url = (manager as any).buildWebSocketUrl(projectId)

      expect(url).toBe(`ws://localhost:8000/ws/${projectId}`)
    })

    it('should use environment variable for base URL', () => {
      vi.stubEnv('NEXT_PUBLIC_WS_URL', 'wss://api.example.com/ws')

      const manager = new WebSocketManager()
      const url = (manager as any).buildWebSocketUrl()

      expect(url).toBe('wss://api.example.com/ws')
    })
  })
})