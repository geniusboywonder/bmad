/**
 * Safety Event Handler
 * Handles HITL safety events, emergency stops, and budget controls
 */

import { EnhancedWebSocketClient } from '../websocket/enhanced-websocket-client';
import { hitlService } from '../api/hitl.service';
import {
  WebSocketEvent,
  HitlRequestCreatedEvent,
  ErrorNotificationEvent,
  EmergencyStop,
  HitlAgentApproval,
} from '../api/types';

export interface SafetyEventConfig {
  enableAudioAlerts?: boolean;
  enableNotifications?: boolean;
  autoShowEmergencyDialog?: boolean;
  emergencyContactEmail?: string;
  budgetThresholds?: {
    warning: number; // 0.8 = 80%
    critical: number; // 0.9 = 90%
    emergency: number; // 0.95 = 95%
  };
}

export interface SafetyAlert {
  id: string;
  type: 'hitl_request' | 'budget_warning' | 'emergency_stop' | 'agent_approval' | 'safety_violation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  projectId?: string;
  timestamp: Date;
  acknowledged: boolean;
  actions?: SafetyAction[];
  metadata?: Record<string, any>;
}

export interface SafetyAction {
  id: string;
  label: string;
  type: 'approve' | 'reject' | 'emergency_stop' | 'view_details' | 'contact_admin';
  handler: () => void | Promise<void>;
  primary?: boolean;
  destructive?: boolean;
}

export type SafetyEventHandler = (alert: SafetyAlert) => void;

/**
 * Safety Event Handler Class
 */
export class SafetyEventHandler {
  private config: SafetyEventConfig;
  private alerts: Map<string, SafetyAlert> = new Map();
  private handlers: Set<SafetyEventHandler> = new Set();
  private websocketClient: EnhancedWebSocketClient | null = null;
  private audioContext: AudioContext | null = null;

  constructor(config: SafetyEventConfig = {}) {
    this.config = {
      enableAudioAlerts: true,
      enableNotifications: true,
      autoShowEmergencyDialog: true,
      budgetThresholds: {
        warning: 0.8,
        critical: 0.9,
        emergency: 0.95,
      },
      ...config,
    };

    this.initializeAudio();
  }

  /**
   * Connect to WebSocket for real-time safety events
   */
  connectToWebSocket(client: EnhancedWebSocketClient): void {
    this.websocketClient = client;

    // Subscribe to safety-related events
    client.on('hitl_request_created', this.handleHITLRequest.bind(this));
    client.on('error_notification', this.handleErrorNotification.bind(this));
    client.on('safety_alert', this.handleSafetyAlert.bind(this));

    console.log('[SafetyEventHandler] Connected to WebSocket for safety events');
  }

  /**
   * Disconnect from WebSocket
   */
  disconnectFromWebSocket(): void {
    if (this.websocketClient) {
      this.websocketClient.off('hitl_request_created');
      this.websocketClient.off('error_notification');
      this.websocketClient.off('safety_alert');
      this.websocketClient = null;
    }
  }

  /**
   * Subscribe to safety alerts
   */
  onSafetyAlert(handler: SafetyEventHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  /**
   * Get all active alerts
   */
  getActiveAlerts(): SafetyAlert[] {
    return Array.from(this.alerts.values()).filter(alert => !alert.acknowledged);
  }

  /**
   * Get alerts by severity
   */
  getAlertsBySeverity(severity: SafetyAlert['severity']): SafetyAlert[] {
    return this.getActiveAlerts().filter(alert => alert.severity === severity);
  }

  /**
   * Acknowledge an alert
   */
  acknowledgeAlert(alertId: string): void {
    const alert = this.alerts.get(alertId);
    if (alert) {
      alert.acknowledged = true;
      console.log(`[SafetyEventHandler] Alert acknowledged: ${alertId}`);
    }
  }

  /**
   * Clear all acknowledged alerts
   */
  clearAcknowledgedAlerts(): void {
    const acknowledgedIds = Array.from(this.alerts.entries())
      .filter(([_, alert]) => alert.acknowledged)
      .map(([id, _]) => id);

    acknowledgedIds.forEach(id => this.alerts.delete(id));
    console.log(`[SafetyEventHandler] Cleared ${acknowledgedIds.length} acknowledged alerts`);
  }

  /**
   * Trigger emergency stop for a project
   */
  async triggerEmergencyStop(projectId: string, reason: string): Promise<void> {
    try {
      console.log(`[SafetyEventHandler] Triggering emergency stop for project ${projectId}: ${reason}`);

      const response = await hitlService.triggerEmergencyStop(projectId, reason);

      if (response.success && response.data) {
        const emergencyStop = response.data;

        const alert: SafetyAlert = {
          id: `emergency_stop_${emergencyStop.id}`,
          type: 'emergency_stop',
          severity: 'critical',
          title: 'Emergency Stop Activated',
          message: `Emergency stop triggered for project. Reason: ${reason}`,
          projectId,
          timestamp: new Date(),
          acknowledged: false,
          actions: [
            {
              id: 'resolve',
              label: 'Resolve Emergency',
              type: 'view_details',
              handler: () => this.resolveEmergencyStop(emergencyStop.id),
              primary: true,
            },
            {
              id: 'contact',
              label: 'Contact Admin',
              type: 'contact_admin',
              handler: () => this.contactEmergencySupport(emergencyStop),
            },
          ],
          metadata: { emergencyStopId: emergencyStop.id },
        };

        this.addAlert(alert);
        this.playEmergencyAlert();

        // Show browser notification
        if (this.config.enableNotifications) {
          this.showNotification('Emergency Stop Activated', reason, 'critical');
        }
      }
    } catch (error) {
      console.error('[SafetyEventHandler] Failed to trigger emergency stop:', error);
    }
  }

  /**
   * Handle HITL request created event
   */
  private handleHITLRequest(event: HitlRequestCreatedEvent): void {
    const { data } = event;

    const alert: SafetyAlert = {
      id: `hitl_${data.request_id}`,
      type: 'hitl_request',
      severity: this.mapUrgencyToSeverity(data.urgency),
      title: 'HITL Approval Required',
      message: data.question,
      projectId: event.project_id,
      timestamp: new Date(),
      acknowledged: false,
      actions: [
        {
          id: 'approve',
          label: 'Approve',
          type: 'approve',
          handler: () => this.approveHITLRequest(data.request_id),
          primary: true,
        },
        {
          id: 'reject',
          label: 'Reject',
          type: 'reject',
          handler: () => this.rejectHITLRequest(data.request_id),
          destructive: true,
        },
        {
          id: 'view',
          label: 'View Details',
          type: 'view_details',
          handler: () => this.viewHITLRequest(data.request_id),
        },
      ],
      metadata: { requestId: data.request_id, urgency: data.urgency },
    };

    this.addAlert(alert);

    // Play audio alert for high urgency requests
    if (data.urgency === 'high' && this.config.enableAudioAlerts) {
      this.playAlert('high');
    }
  }

  /**
   * Handle error notification event
   */
  private handleErrorNotification(event: ErrorNotificationEvent): void {
    const { data } = event;

    if (data.severity === 'critical') {
      const alert: SafetyAlert = {
        id: `error_${Date.now()}`,
        type: 'safety_violation',
        severity: 'critical',
        title: 'Critical System Error',
        message: data.message,
        projectId: event.project_id,
        timestamp: new Date(),
        acknowledged: false,
        actions: [
          {
            id: 'emergency_stop',
            label: 'Emergency Stop',
            type: 'emergency_stop',
            handler: () => this.triggerEmergencyStop(event.project_id, `Critical error: ${data.message}`),
            destructive: true,
            primary: true,
          },
          {
            id: 'view',
            label: 'View Details',
            type: 'view_details',
            handler: () => console.log('Error details:', data),
          },
        ],
        metadata: { errorCode: data.error_code, agentType: data.agent_type },
      };

      this.addAlert(alert);
      this.playEmergencyAlert();
    }
  }

  /**
   * Handle general safety alert event
   */
  private handleSafetyAlert(event: WebSocketEvent): void {
    const { data } = event;

    const alert: SafetyAlert = {
      id: `safety_${Date.now()}`,
      type: data.type || 'safety_violation',
      severity: data.severity || 'medium',
      title: data.title || 'Safety Alert',
      message: data.message || 'A safety event has occurred',
      projectId: event.project_id,
      timestamp: new Date(),
      acknowledged: false,
      metadata: data,
    };

    this.addAlert(alert);

    if (alert.severity === 'critical') {
      this.playEmergencyAlert();
    }
  }

  /**
   * Add alert and notify handlers
   */
  private addAlert(alert: SafetyAlert): void {
    this.alerts.set(alert.id, alert);

    // Notify all handlers
    this.handlers.forEach(handler => {
      try {
        handler(alert);
      } catch (error) {
        console.error('[SafetyEventHandler] Handler error:', error);
      }
    });

    console.log(`[SafetyEventHandler] New ${alert.severity} alert: ${alert.title}`);
  }

  /**
   * HITL Request Actions
   */
  private async approveHITLRequest(requestId: string): Promise<void> {
    try {
      await hitlService.respondToRequest(requestId, {
        action: 'approve',
        comment: 'Approved via safety alert',
      });
      this.acknowledgeAlert(`hitl_${requestId}`);
    } catch (error) {
      console.error('[SafetyEventHandler] Failed to approve HITL request:', error);
    }
  }

  private async rejectHITLRequest(requestId: string): Promise<void> {
    try {
      await hitlService.respondToRequest(requestId, {
        action: 'reject',
        comment: 'Rejected via safety alert',
      });
      this.acknowledgeAlert(`hitl_${requestId}`);
    } catch (error) {
      console.error('[SafetyEventHandler] Failed to reject HITL request:', error);
    }
  }

  private async viewHITLRequest(requestId: string): Promise<void> {
    // This would typically open a modal or navigate to the HITL request details
    console.log(`[SafetyEventHandler] Viewing HITL request: ${requestId}`);
    // Implementation depends on UI framework
  }

  /**
   * Emergency Stop Actions
   */
  private async resolveEmergencyStop(stopId: string): Promise<void> {
    try {
      await hitlService.resolveEmergencyStop(stopId, 'Resolved via safety alert');
      this.acknowledgeAlert(`emergency_stop_${stopId}`);
    } catch (error) {
      console.error('[SafetyEventHandler] Failed to resolve emergency stop:', error);
    }
  }

  private contactEmergencySupport(emergencyStop: EmergencyStop): void {
    if (this.config.emergencyContactEmail) {
      const subject = `Emergency Stop Alert - ${emergencyStop.id}`;
      const body = `Emergency stop triggered for project ${emergencyStop.project_id}.\n\nReason: ${emergencyStop.reason}\nTriggered at: ${emergencyStop.triggered_at}`;

      window.open(`mailto:${this.config.emergencyContactEmail}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`);
    }
  }

  /**
   * Audio Alerts
   */
  private initializeAudio(): void {
    if (typeof window !== 'undefined' && this.config.enableAudioAlerts) {
      try {
        this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      } catch (error) {
        console.warn('[SafetyEventHandler] Audio context not available:', error);
      }
    }
  }

  private playAlert(severity: 'low' | 'medium' | 'high' = 'medium'): void {
    if (!this.audioContext || !this.config.enableAudioAlerts) return;

    try {
      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);

      // Different frequencies for different severities
      const frequencies = { low: 400, medium: 600, high: 800 };
      oscillator.frequency.setValueAtTime(frequencies[severity], this.audioContext.currentTime);

      gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.5);

      oscillator.start(this.audioContext.currentTime);
      oscillator.stop(this.audioContext.currentTime + 0.5);
    } catch (error) {
      console.warn('[SafetyEventHandler] Failed to play audio alert:', error);
    }
  }

  private playEmergencyAlert(): void {
    if (!this.audioContext || !this.config.enableAudioAlerts) return;

    try {
      // Play urgent triple beep pattern
      [0, 0.2, 0.4].forEach(delay => {
        setTimeout(() => this.playAlert('high'), delay * 1000);
      });
    } catch (error) {
      console.warn('[SafetyEventHandler] Failed to play emergency alert:', error);
    }
  }

  /**
   * Browser Notifications
   */
  private async showNotification(title: string, message: string, severity: SafetyAlert['severity']): Promise<void> {
    if (!this.config.enableNotifications || typeof window === 'undefined') return;

    try {
      if (Notification.permission === 'default') {
        await Notification.requestPermission();
      }

      if (Notification.permission === 'granted') {
        const icon = this.getNotificationIcon(severity);

        new Notification(title, {
          body: message,
          icon,
          tag: `safety_alert_${severity}`,
          requireInteraction: severity === 'critical',
        });
      }
    } catch (error) {
      console.warn('[SafetyEventHandler] Failed to show notification:', error);
    }
  }

  private getNotificationIcon(severity: SafetyAlert['severity']): string {
    // Return appropriate icon URLs based on severity
    const icons = {
      low: '/icons/info.png',
      medium: '/icons/warning.png',
      high: '/icons/alert.png',
      critical: '/icons/emergency.png',
    };
    return icons[severity];
  }

  /**
   * Utility Functions
   */
  private mapUrgencyToSeverity(urgency: 'low' | 'medium' | 'high'): SafetyAlert['severity'] {
    const mapping: Record<string, SafetyAlert['severity']> = {
      low: 'low',
      medium: 'medium',
      high: 'high',
    };
    return mapping[urgency] || 'medium';
  }
}

// Export singleton instance
export const safetyEventHandler = new SafetyEventHandler();