/**
 * Enhanced WebSocket Client for Backend Integration
 * Supports project-scoped connections, backend event types, and safety alerts
 */

import {
  WebSocketEvent,
  WebSocketEventType,
  AgentStatusChangedEvent,
  TaskProgressUpdatedEvent,
  HitlRequestCreatedEvent,
  ArtifactGeneratedEvent,
  ErrorNotificationEvent,
  AgentChatMessageEvent,
} from '../api/types';

export interface ConnectionConfig {
  url: string;
  projectId?: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  timeout?: number;
}

export interface ConnectionStatus {
  connected: boolean;
  reconnecting: boolean;
  attempt: number;
  error?: string;
  lastConnected?: Date;
  projectId?: string;
}

export type EventHandler<T = any> = (event: T) => void;
export type StatusHandler = (status: ConnectionStatus) => void;

/**
 * Enhanced WebSocket client with backend integration support
 */
export class EnhancedWebSocketClient {
  private ws: WebSocket | null = null;
  private config: ConnectionConfig;
  private status: ConnectionStatus;
  private eventHandlers: Map<WebSocketEventType | 'status', Set<EventHandler>> = new Map();
  private reconnectTimeoutId: NodeJS.Timeout | null = null;
  private heartbeatIntervalId: NodeJS.Timeout | null = null;
  private isDestroyed = false;

  constructor(config: ConnectionConfig) {
    this.config = {
      autoReconnect: true,
      maxReconnectAttempts: 10,
      reconnectInterval: 1000,
      heartbeatInterval: 30000,
      timeout: 15000,
      ...config,
    };

    this.status = {
      connected: false,
      reconnecting: false,
      attempt: 0,
      projectId: config.projectId,
    };

    // Auto-connect if in browser environment
    if (typeof window !== 'undefined') {
      this.connect();
    }
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.isDestroyed) {
      throw new Error('WebSocket client has been destroyed');
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[EnhancedWebSocket] Already connected');
      return;
    }

    try {
      await this.establishConnection();
    } catch (error) {
      console.error('[EnhancedWebSocket] Connection failed:', error);
      this.handleConnectionError(error);
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    console.log('[EnhancedWebSocket] Disconnecting...');

    this.cleanup();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.updateStatus({
      connected: false,
      reconnecting: false,
      attempt: 0,
    });
  }

  /**
   * Destroy the client and clean up all resources
   */
  destroy(): void {
    console.log('[EnhancedWebSocket] Destroying client...');

    this.isDestroyed = true;
    this.disconnect();
    this.eventHandlers.clear();
  }

  /**
   * Send message to server
   */
  send(message: any): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[EnhancedWebSocket] Cannot send message: not connected');
      return false;
    }

    try {
      const payload = typeof message === 'string' ? message : JSON.stringify(message);
      this.ws.send(payload);
      console.log('[EnhancedWebSocket] Message sent:', payload);
      return true;
    } catch (error) {
      console.error('[EnhancedWebSocket] Failed to send message:', error);
      return false;
    }
  }

  /**
   * Subscribe to specific event type
   */
  on<T = any>(eventType: WebSocketEventType | 'status', handler: EventHandler<T>): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }

    this.eventHandlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(eventType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.eventHandlers.delete(eventType);
        }
      }
    };
  }

  /**
   * Unsubscribe from event type
   */
  off(eventType: WebSocketEventType | 'status', handler?: EventHandler): void {
    if (!handler) {
      // Remove all handlers for this event type
      this.eventHandlers.delete(eventType);
      return;
    }

    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.eventHandlers.delete(eventType);
      }
    }
  }

  /**
   * Get current connection status
   */
  getStatus(): ConnectionStatus {
    return { ...this.status };
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.status.connected;
  }

  /**
   * Switch to different project
   */
  async switchProject(projectId?: string): Promise<void> {
    const newUrl = this.buildWebSocketUrl(projectId);

    if (newUrl === this.config.url && projectId === this.config.projectId) {
      console.log('[EnhancedWebSocket] Already connected to this project');
      return;
    }

    console.log(`[EnhancedWebSocket] Switching to project: ${projectId || 'global'}`);

    this.config.url = newUrl;
    this.config.projectId = projectId;
    this.status.projectId = projectId;

    // Reconnect with new URL
    this.disconnect();
    await this.connect();
  }

  /**
   * Establish WebSocket connection
   */
  private async establishConnection(): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = this.config.url;
      console.log(`[EnhancedWebSocket] Connecting to: ${url}`);

      this.updateStatus({
        connected: false,
        reconnecting: true,
        attempt: this.status.attempt + 1,
      });

      this.ws = new WebSocket(url);

      const timeout = setTimeout(() => {
        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
          this.ws.close();
          reject(new Error('Connection timeout'));
        }
      }, this.config.timeout);

      this.ws.onopen = () => {
        clearTimeout(timeout);
        console.log('[EnhancedWebSocket] Connected successfully');

        this.updateStatus({
          connected: true,
          reconnecting: false,
          attempt: 0,
          error: undefined,
          lastConnected: new Date(),
        });

        this.startHeartbeat();
        resolve();
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(event);
      };

      this.ws.onclose = (event) => {
        clearTimeout(timeout);
        console.log(`[EnhancedWebSocket] Connection closed: ${event.code} ${event.reason}`);

        this.cleanup();

        this.updateStatus({
          connected: false,
          reconnecting: false,
          error: event.reason || 'Connection closed',
        });

        // Auto-reconnect if enabled and not a clean close
        if (this.config.autoReconnect && event.code !== 1000 && !this.isDestroyed) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        clearTimeout(timeout);
        console.error('[EnhancedWebSocket] Connection error:', error);

        // Don't reject immediately on error - let timeout handle it
        // This helps with server reloads and temporary connection issues
        if (!this.config.autoReconnect) {
          reject(error);
        }
      };
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      console.log('[EnhancedWebSocket] Received message:', data);

      // Handle heartbeat/ping messages
      if (data.type === 'ping') {
        this.send({ type: 'pong', timestamp: Date.now() });
        return;
      }

      // Emit the event to all listeners
      this.emitEvent(data.event_type || data.type, data);

    } catch (error) {
      console.error('[EnhancedWebSocket] Failed to parse message:', error);
    }
  }

  /**
   * Emit event to all registered handlers
   */
  private emitEvent(eventType: WebSocketEventType, data: any): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`[EnhancedWebSocket] Event handler error for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Update connection status and notify listeners
   */
  private updateStatus(updates: Partial<ConnectionStatus>): void {
    this.status = { ...this.status, ...updates };

    const handlers = this.eventHandlers.get('status');
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(this.status);
        } catch (error) {
          console.error('[EnhancedWebSocket] Status handler error:', error);
        }
      });
    }
  }

  /**
   * Handle connection errors
   */
  private handleConnectionError(error: any): void {
    this.updateStatus({
      connected: false,
      reconnecting: false,
      error: error.message || 'Connection failed',
    });

    if (this.config.autoReconnect && !this.isDestroyed) {
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.status.attempt >= this.config.maxReconnectAttempts!) {
      console.error('[EnhancedWebSocket] Max reconnection attempts reached');
      this.updateStatus({
        reconnecting: false,
        error: 'Max reconnection attempts reached',
      });
      return;
    }

    const delay = Math.min(
      this.config.reconnectInterval! * Math.pow(2, this.status.attempt),
      30000 // Max 30 seconds
    );

    console.log(`[EnhancedWebSocket] Reconnecting in ${delay}ms (attempt ${this.status.attempt + 1})`);

    this.updateStatus({ reconnecting: true });

    this.reconnectTimeoutId = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    if (this.heartbeatIntervalId) {
      clearInterval(this.heartbeatIntervalId);
    }

    this.heartbeatIntervalId = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', timestamp: Date.now() });
      } else {
        this.cleanup();
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Clean up timers and intervals
   */
  private cleanup(): void {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }

    if (this.heartbeatIntervalId) {
      clearInterval(this.heartbeatIntervalId);
      this.heartbeatIntervalId = null;
    }
  }

  /**
   * Build WebSocket URL with optional project scope
   */
  private buildWebSocketUrl(projectId?: string): string {
    const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    return projectId ? `${baseUrl}/${projectId}` : baseUrl;
  }
}

/**
 * WebSocket service manager for handling multiple connections
 */
export class WebSocketManager {
  private connections: Map<string, EnhancedWebSocketClient> = new Map();
  private globalConnection: EnhancedWebSocketClient | null = null;

  /**
   * Get or create global connection
   */
  getGlobalConnection(): EnhancedWebSocketClient {
    if (!this.globalConnection) {
      this.globalConnection = new EnhancedWebSocketClient({
        url: this.buildWebSocketUrl(),
      });
    }
    return this.globalConnection;
  }

  /**
   * Get or create project-specific connection
   */
  getProjectConnection(projectId: string): EnhancedWebSocketClient {
    if (!this.connections.has(projectId)) {
      const connection = new EnhancedWebSocketClient({
        url: this.buildWebSocketUrl(projectId),
        projectId,
      });
      this.connections.set(projectId, connection);
    }
    return this.connections.get(projectId)!;
  }

  /**
   * Disconnect from specific project
   */
  disconnectProject(projectId: string): void {
    const connection = this.connections.get(projectId);
    if (connection) {
      connection.destroy();
      this.connections.delete(projectId);
    }
  }

  /**
   * Disconnect from all projects
   */
  disconnectAll(): void {
    this.connections.forEach(connection => connection.destroy());
    this.connections.clear();

    if (this.globalConnection) {
      this.globalConnection.destroy();
      this.globalConnection = null;
    }
  }

  /**
   * Get all active connections
   */
  getActiveConnections(): { projectId?: string; connected: boolean }[] {
    const connections: { projectId?: string; connected: boolean }[] = [];

    if (this.globalConnection) {
      connections.push({
        connected: this.globalConnection.isConnected(),
      });
    }

    this.connections.forEach((connection, projectId) => {
      connections.push({
        projectId,
        connected: connection.isConnected(),
      });
    });

    return connections;
  }

  private buildWebSocketUrl(projectId?: string): string {
    const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    return projectId ? `${baseUrl}/${projectId}` : baseUrl;
  }
}

// Export singleton instance
export const websocketManager = new WebSocketManager();