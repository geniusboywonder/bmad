/**
 * Safety Event Handler Tests - Phase 1 Integration
 * Tests for safety event handling, HITL requests, and emergency controls
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { SafetyEventHandler, SafetyAlert, SafetyEventConfig } from './safety-event-handler'
import { EnhancedWebSocketClient } from '../websocket/enhanced-websocket-client'
import { hitlService } from '../api/hitl.service'
import {
  HitlRequestCreatedEvent,
  ErrorNotificationEvent,
  WebSocketEvent,
} from '../api/types'

// Mock the HITL service
vi.mock('../api/hitl.service', () => ({
  hitlService: {
    triggerEmergencyStop: vi.fn(),
    respondToRequest: vi.fn(),
    resolveEmergencyStop: vi.fn(),
  },
}))

// Mock WebSocket client
const mockWebSocketClient = {
  on: vi.fn(),
  off: vi.fn(),
} as any

describe('SafetyEventHandler', () => {
  let handler: SafetyEventHandler
  let mockConfig: SafetyEventConfig
  const mockHitlService = hitlService as any

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()

    mockConfig = {
      enableAudioAlerts: true,
      enableNotifications: true,
      autoShowEmergencyDialog: true,
      emergencyContactEmail: 'admin@test.com',
      budgetThresholds: {
        warning: 0.8,
        critical: 0.9,
        emergency: 0.95,
      },
    }

    handler = new SafetyEventHandler(mockConfig)
  })

  afterEach(() => {
    vi.useRealTimers()
    handler.disconnectFromWebSocket()
  })

  describe('Configuration', () => {
    it('should initialize with default configuration', () => {
      const defaultHandler = new SafetyEventHandler()
      expect(defaultHandler).toBeInstanceOf(SafetyEventHandler)
    })

    it('should merge provided config with defaults', () => {
      const customConfig = { enableAudioAlerts: false }
      const customHandler = new SafetyEventHandler(customConfig)
      expect(customHandler).toBeInstanceOf(SafetyEventHandler)
    })
  })

  describe('WebSocket Connection', () => {
    it('should connect to WebSocket and subscribe to events', () => {
      handler.connectToWebSocket(mockWebSocketClient)

      expect(mockWebSocketClient.on).toHaveBeenCalledWith('hitl_request_created', expect.any(Function))
      expect(mockWebSocketClient.on).toHaveBeenCalledWith('error_notification', expect.any(Function))
      expect(mockWebSocketClient.on).toHaveBeenCalledWith('safety_alert', expect.any(Function))
    })

    it('should disconnect from WebSocket and unsubscribe events', () => {
      handler.connectToWebSocket(mockWebSocketClient)
      handler.disconnectFromWebSocket()

      expect(mockWebSocketClient.off).toHaveBeenCalledWith('hitl_request_created')
      expect(mockWebSocketClient.off).toHaveBeenCalledWith('error_notification')
      expect(mockWebSocketClient.off).toHaveBeenCalledWith('safety_alert')
    })
  })

  describe('Alert Management', () => {
    it('should get active alerts only', () => {
      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      // Simulate HITL event that creates an alert
      const hitlEvent: HitlRequestCreatedEvent = {
        event_type: 'hitl_request_created',
        project_id: 'test-project',
        data: {
          request_id: 'test-request',
          question: 'Should we proceed?',
          urgency: 'medium',
          agent_type: 'researcher',
          context: {},
          requested_at: '2025-01-01T00:00:00Z',
        },
      }

      // Trigger the event handler
      handler.connectToWebSocket(mockWebSocketClient)
      const hitlHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'hitl_request_created'
      )?.[1]
      hitlHandler?.(hitlEvent)

      const activeAlerts = handler.getActiveAlerts()
      expect(activeAlerts).toHaveLength(1)
      expect(activeAlerts[0].type).toBe('hitl_request')
      expect(activeAlerts[0].acknowledged).toBe(false)
    })

    it('should filter alerts by severity', () => {
      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      // Create high severity HITL event
      const highSeverityEvent: HitlRequestCreatedEvent = {
        event_type: 'hitl_request_created',
        project_id: 'test-project',
        data: {
          request_id: 'high-request',
          question: 'Critical decision needed',
          urgency: 'high',
          agent_type: 'researcher',
          context: {},
          requested_at: '2025-01-01T00:00:00Z',
        },
      }

      handler.connectToWebSocket(mockWebSocketClient)
      const hitlHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'hitl_request_created'
      )?.[1]
      hitlHandler?.(highSeverityEvent)

      const highAlerts = handler.getAlertsBySeverity('high')
      expect(highAlerts).toHaveLength(1)
      expect(highAlerts[0].severity).toBe('high')
    })

    it('should acknowledge alerts', () => {
      const alertHandler = vi.fn()
      const unsubscribe = handler.onSafetyAlert(alertHandler)

      // Create and trigger alert
      const hitlEvent: HitlRequestCreatedEvent = {
        event_type: 'hitl_request_created',
        project_id: 'test-project',
        data: {
          request_id: 'test-request',
          question: 'Test question',
          urgency: 'low',
          agent_type: 'researcher',
          context: {},
          requested_at: '2025-01-01T00:00:00Z',
        },
      }

      handler.connectToWebSocket(mockWebSocketClient)
      const hitlHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'hitl_request_created'
      )?.[1]
      hitlHandler?.(hitlEvent)

      const alertId = 'hitl_test-request'
      handler.acknowledgeAlert(alertId)

      const activeAlerts = handler.getActiveAlerts()
      expect(activeAlerts).toHaveLength(0)

      unsubscribe()
    })

    it('should clear acknowledged alerts', () => {
      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      // Create and acknowledge multiple alerts
      const events = [
        {
          event_type: 'hitl_request_created' as const,
          project_id: 'test-project',
          data: {
            request_id: 'request-1',
            question: 'Question 1',
            urgency: 'low' as const,
            agent_type: 'researcher',
            context: {},
            requested_at: '2025-01-01T00:00:00Z',
          },
        },
        {
          event_type: 'hitl_request_created' as const,
          project_id: 'test-project',
          data: {
            request_id: 'request-2',
            question: 'Question 2',
            urgency: 'medium' as const,
            agent_type: 'researcher',
            context: {},
            requested_at: '2025-01-01T00:00:00Z',
          },
        },
      ]

      handler.connectToWebSocket(mockWebSocketClient)
      const hitlHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'hitl_request_created'
      )?.[1]

      events.forEach(event => hitlHandler?.(event))

      // Acknowledge first alert
      handler.acknowledgeAlert('hitl_request-1')

      handler.clearAcknowledgedAlerts()

      const activeAlerts = handler.getActiveAlerts()
      expect(activeAlerts).toHaveLength(1)
      expect(activeAlerts[0].id).toBe('hitl_request-2')
    })
  })

  describe('HITL Request Handling', () => {
    it('should create alert for HITL request', () => {
      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      const hitlEvent: HitlRequestCreatedEvent = {
        event_type: 'hitl_request_created',
        project_id: 'test-project',
        data: {
          request_id: 'test-request',
          question: 'Should we proceed with this action?',
          urgency: 'high',
          agent_type: 'researcher',
          context: { additional: 'data' },
          requested_at: '2025-01-01T00:00:00Z',
        },
      }

      handler.connectToWebSocket(mockWebSocketClient)
      const hitlHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'hitl_request_created'
      )?.[1]
      hitlHandler?.(hitlEvent)

      expect(alertHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'hitl_test-request',
          type: 'hitl_request',
          severity: 'high',
          title: 'HITL Approval Required',
          message: 'Should we proceed with this action?',
          projectId: 'test-project',
          acknowledged: false,
          actions: expect.arrayContaining([
            expect.objectContaining({ type: 'approve' }),
            expect.objectContaining({ type: 'reject' }),
            expect.objectContaining({ type: 'view_details' }),
          ]),
        })
      )
    })

    it('should approve HITL request', async () => {
      mockHitlService.respondToRequest.mockResolvedValue({ success: true })

      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      const hitlEvent: HitlRequestCreatedEvent = {
        event_type: 'hitl_request_created',
        project_id: 'test-project',
        data: {
          request_id: 'test-request',
          question: 'Test question',
          urgency: 'medium',
          agent_type: 'researcher',
          context: {},
          requested_at: '2025-01-01T00:00:00Z',
        },
      }

      handler.connectToWebSocket(mockWebSocketClient)
      const hitlHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'hitl_request_created'
      )?.[1]
      hitlHandler?.(hitlEvent)

      // Get the approve action and execute it
      const alert = alertHandler.mock.calls[0][0] as SafetyAlert
      const approveAction = alert.actions?.find(action => action.type === 'approve')

      await approveAction?.handler()

      expect(mockHitlService.respondToRequest).toHaveBeenCalledWith('test-request', {
        action: 'approve',
        comment: 'Approved via safety alert',
      })
    })

    it('should reject HITL request', async () => {
      mockHitlService.respondToRequest.mockResolvedValue({ success: true })

      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      const hitlEvent: HitlRequestCreatedEvent = {
        event_type: 'hitl_request_created',
        project_id: 'test-project',
        data: {
          request_id: 'test-request',
          question: 'Test question',
          urgency: 'medium',
          agent_type: 'researcher',
          context: {},
          requested_at: '2025-01-01T00:00:00Z',
        },
      }

      handler.connectToWebSocket(mockWebSocketClient)
      const hitlHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'hitl_request_created'
      )?.[1]
      hitlHandler?.(hitlEvent)

      const alert = alertHandler.mock.calls[0][0] as SafetyAlert
      const rejectAction = alert.actions?.find(action => action.type === 'reject')

      await rejectAction?.handler()

      expect(mockHitlService.respondToRequest).toHaveBeenCalledWith('test-request', {
        action: 'reject',
        comment: 'Rejected via safety alert',
      })
    })
  })

  describe('Emergency Stop Handling', () => {
    it('should trigger emergency stop', async () => {
      const mockEmergencyStop = {
        id: 'stop-123',
        project_id: 'test-project',
        reason: 'Test emergency',
        triggered_at: '2025-01-01T00:00:00Z',
        triggered_by: 'user',
        status: 'active',
      }

      mockHitlService.triggerEmergencyStop.mockResolvedValue({
        success: true,
        data: mockEmergencyStop,
      })

      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      await handler.triggerEmergencyStop('test-project', 'Test emergency')

      expect(mockHitlService.triggerEmergencyStop).toHaveBeenCalledWith(
        'test-project',
        'Test emergency'
      )

      expect(alertHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'emergency_stop',
          severity: 'critical',
          title: 'Emergency Stop Activated',
          message: 'Emergency stop triggered for project. Reason: Test emergency',
          projectId: 'test-project',
        })
      )
    })

    it('should resolve emergency stop', async () => {
      mockHitlService.resolveEmergencyStop.mockResolvedValue({ success: true })

      const mockEmergencyStop = {
        id: 'stop-123',
        project_id: 'test-project',
        reason: 'Test emergency',
        triggered_at: '2025-01-01T00:00:00Z',
        triggered_by: 'user',
        status: 'active',
      }

      mockHitlService.triggerEmergencyStop.mockResolvedValue({
        success: true,
        data: mockEmergencyStop,
      })

      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      await handler.triggerEmergencyStop('test-project', 'Test emergency')

      const alert = alertHandler.mock.calls[0][0] as SafetyAlert
      const resolveAction = alert.actions?.find(action => action.type === 'view_details')

      await resolveAction?.handler()

      expect(mockHitlService.resolveEmergencyStop).toHaveBeenCalledWith(
        'stop-123',
        'Resolved via safety alert'
      )
    })
  })

  describe('Error Notification Handling', () => {
    it('should handle critical error notifications', () => {
      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      const errorEvent: ErrorNotificationEvent = {
        event_type: 'error_notification',
        project_id: 'test-project',
        data: {
          message: 'Critical system failure',
          severity: 'critical',
          error_code: 'SYS_001',
          agent_type: 'researcher',
          timestamp: '2025-01-01T00:00:00Z',
        },
      }

      handler.connectToWebSocket(mockWebSocketClient)
      const errorHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'error_notification'
      )?.[1]
      errorHandler?.(errorEvent)

      expect(alertHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'safety_violation',
          severity: 'critical',
          title: 'Critical System Error',
          message: 'Critical system failure',
          projectId: 'test-project',
          actions: expect.arrayContaining([
            expect.objectContaining({ type: 'emergency_stop' }),
            expect.objectContaining({ type: 'view_details' }),
          ]),
        })
      )
    })

    it('should not create alerts for non-critical errors', () => {
      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      const errorEvent: ErrorNotificationEvent = {
        event_type: 'error_notification',
        project_id: 'test-project',
        data: {
          message: 'Warning message',
          severity: 'warning',
          error_code: 'WARN_001',
          agent_type: 'researcher',
          timestamp: '2025-01-01T00:00:00Z',
        },
      }

      handler.connectToWebSocket(mockWebSocketClient)
      const errorHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'error_notification'
      )?.[1]
      errorHandler?.(errorEvent)

      expect(alertHandler).not.toHaveBeenCalled()
    })
  })

  describe('General Safety Alert Handling', () => {
    it('should handle general safety alerts', () => {
      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      const safetyEvent: WebSocketEvent = {
        event_type: 'safety_alert',
        project_id: 'test-project',
        data: {
          type: 'budget_warning',
          severity: 'high',
          title: 'Budget Threshold Exceeded',
          message: 'Project budget has exceeded 90% threshold',
        },
      }

      handler.connectToWebSocket(mockWebSocketClient)
      const safetyHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'safety_alert'
      )?.[1]
      safetyHandler?.(safetyEvent)

      expect(alertHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'budget_warning',
          severity: 'high',
          title: 'Budget Threshold Exceeded',
          message: 'Project budget has exceeded 90% threshold',
          projectId: 'test-project',
        })
      )
    })
  })

  describe('Event Handler Management', () => {
    it('should subscribe and unsubscribe event handlers', () => {
      const handler1 = vi.fn()
      const handler2 = vi.fn()

      const unsubscribe1 = handler.onSafetyAlert(handler1)
      const unsubscribe2 = handler.onSafetyAlert(handler2)

      // Trigger an alert
      const hitlEvent: HitlRequestCreatedEvent = {
        event_type: 'hitl_request_created',
        project_id: 'test-project',
        data: {
          request_id: 'test-request',
          question: 'Test question',
          urgency: 'low',
          agent_type: 'researcher',
          context: {},
          requested_at: '2025-01-01T00:00:00Z',
        },
      }

      handler.connectToWebSocket(mockWebSocketClient)
      const hitlHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'hitl_request_created'
      )?.[1]
      hitlHandler?.(hitlEvent)

      expect(handler1).toHaveBeenCalled()
      expect(handler2).toHaveBeenCalled()

      // Unsubscribe first handler
      unsubscribe1()
      vi.clearAllMocks()

      // Trigger another alert
      const hitlEvent2: HitlRequestCreatedEvent = {
        ...hitlEvent,
        data: { ...hitlEvent.data, request_id: 'test-request-2' },
      }
      hitlHandler?.(hitlEvent2)

      expect(handler1).not.toHaveBeenCalled()
      expect(handler2).toHaveBeenCalled()

      unsubscribe2()
    })

    it('should handle errors in event handlers gracefully', () => {
      const goodHandler = vi.fn()
      const badHandler = vi.fn().mockImplementation(() => {
        throw new Error('Handler error')
      })

      handler.onSafetyAlert(goodHandler)
      handler.onSafetyAlert(badHandler)

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const hitlEvent: HitlRequestCreatedEvent = {
        event_type: 'hitl_request_created',
        project_id: 'test-project',
        data: {
          request_id: 'test-request',
          question: 'Test question',
          urgency: 'low',
          agent_type: 'researcher',
          context: {},
          requested_at: '2025-01-01T00:00:00Z',
        },
      }

      handler.connectToWebSocket(mockWebSocketClient)
      const hitlHandler = mockWebSocketClient.on.mock.calls.find(
        call => call[0] === 'hitl_request_created'
      )?.[1]
      hitlHandler?.(hitlEvent)

      expect(goodHandler).toHaveBeenCalled()
      expect(badHandler).toHaveBeenCalled()
      expect(consoleSpy).toHaveBeenCalledWith('[SafetyEventHandler] Handler error:', expect.any(Error))

      consoleSpy.mockRestore()
    })
  })

  describe('Audio Alert System', () => {
    it('should initialize audio context when enabled', () => {
      const audioHandler = new SafetyEventHandler({ enableAudioAlerts: true })
      expect(audioHandler).toBeInstanceOf(SafetyEventHandler)
    })

    it('should not initialize audio context when disabled', () => {
      const audioHandler = new SafetyEventHandler({ enableAudioAlerts: false })
      expect(audioHandler).toBeInstanceOf(SafetyEventHandler)
    })
  })

  describe('Urgency to Severity Mapping', () => {
    it('should map urgency levels to correct severity', () => {
      const alertHandler = vi.fn()
      handler.onSafetyAlert(alertHandler)

      const urgencyLevels: Array<'low' | 'medium' | 'high'> = ['low', 'medium', 'high']
      const expectedSeverities: Array<'low' | 'medium' | 'high'> = ['low', 'medium', 'high']

      urgencyLevels.forEach((urgency, index) => {
        vi.clearAllMocks()

        const hitlEvent: HitlRequestCreatedEvent = {
          event_type: 'hitl_request_created',
          project_id: 'test-project',
          data: {
            request_id: `request-${urgency}`,
            question: `${urgency} urgency question`,
            urgency,
            agent_type: 'researcher',
            context: {},
            requested_at: '2025-01-01T00:00:00Z',
          },
        }

        handler.connectToWebSocket(mockWebSocketClient)
        const hitlHandler = mockWebSocketClient.on.mock.calls.find(
          call => call[0] === 'hitl_request_created'
        )?.[1]
        hitlHandler?.(hitlEvent)

        const alert = alertHandler.mock.calls[0][0] as SafetyAlert
        expect(alert.severity).toBe(expectedSeverities[index])
      })
    })
  })
})