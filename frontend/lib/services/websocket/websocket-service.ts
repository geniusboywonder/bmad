import { useAppStore } from "../../stores/app-store";
import { useHITLStore } from "../../stores/hitl-store";
import { websocketManager, EnhancedWebSocketClient } from "./enhanced-websocket-client";
import { safetyEventHandler } from "../safety/safety-event-handler";
import {
  WebSocketEvent,
  AgentStatusChangedEvent,
  TaskProgressUpdatedEvent,
  HitlRequestCreatedEvent,
  ArtifactGeneratedEvent,
  ErrorNotificationEvent,
  AgentChatMessageEvent,
  WebSocketEventType
} from "../api/types";

// Legacy interface for backward compatibility
export interface WebSocketMessage {
  type: string;
  data?: any;
  agent_name?: string;
  content?: string;
  timestamp: string;
}

export interface ConnectionStatus {
  connected: boolean;
  reconnecting: boolean;
  error?: string;
}

// Enhanced WebSocket Service using the new enhanced client
class WebSocketService {
  private globalConnection: EnhancedWebSocketClient;
  private projectConnections: Map<string, EnhancedWebSocketClient> = new Map();
  private statusCallbacks: ((status: ConnectionStatus) => void)[] = [];
  private shouldAutoConnect = false;

  constructor() {
    this.connect = this.connect.bind(this);
    this.globalConnection = websocketManager.getGlobalConnection();
    this.setupGlobalEventHandlers();
    this.initializeSafetyHandling();
  }

  private initializeSafetyHandling() {
    // Connect safety event handler to global WebSocket connection
    safetyEventHandler.connectToWebSocket(this.globalConnection);

    console.log('[WebSocketService] Safety event handling initialized');
  }

  private setupGlobalEventHandlers() {
    // Subscribe to connection status changes
    this.globalConnection.on('status', (status) => {
      const connectionStatus: ConnectionStatus = {
        connected: status.connected,
        reconnecting: status.reconnecting,
        error: status.error
      };
      this.updateConnectionStatus(connectionStatus);
      useAppStore.getState().setConnectionStatus(connectionStatus);
    });

    // Subscribe to all backend event types
    this.globalConnection.on('agent_status_changed', this.handleAgentStatusChanged.bind(this));
    this.globalConnection.on('task_progress_updated', this.handleTaskProgressUpdated.bind(this));
    this.globalConnection.on('HITL_REQUEST_CREATED', this.handleHITLRequestCreated.bind(this));
    this.globalConnection.on('hitl_request_created', this.handleHITLRequestCreated.bind(this)); // backwards compatibility
    this.globalConnection.on('artifact_generated', this.handleArtifactGenerated.bind(this));
    this.globalConnection.on('error_notification', this.handleErrorNotification.bind(this));
    this.globalConnection.on('agent_chat_message', this.handleAgentChatMessage.bind(this));
  }

  connect() {
    if (typeof window === "undefined") return;

    if (!this.shouldAutoConnect) {
      console.log("[WebSocket] Auto-connect is disabled.");
      return;
    }

    console.log("[WebSocket] Connecting to backend...");
    this.globalConnection.connect();
  }

  enableAutoConnect() {
    this.shouldAutoConnect = true;
    this.connect();
  }

  // Enhanced event handlers for all backend event types
  private handleAgentStatusChanged(event: AgentStatusChangedEvent) {
    const { data } = event;
    const { updateAgent, addLog } = useAppStore.getState();

    updateAgent({
      name: data.agent_name,
      status: data.status,
      task: data.current_task
    });

    addLog({
      agent: data.agent_name,
      level: "info",
      message: `Agent ${data.agent_name} is now ${data.status}. Task: ${data.current_task}`
    });

    console.log(`[WebSocket] Agent ${data.agent_name} status changed to ${data.status}`);
  }

  private handleTaskProgressUpdated(event: TaskProgressUpdatedEvent) {
    const { data } = event;
    const { updateAgent, addLog } = useAppStore.getState();

    updateAgent({
      name: data.agent_name,
      status: "working",
      task: data.task_description,
      progress: data.progress_percentage
    });

    addLog({
      agent: data.agent_name,
      level: "info",
      message: `Task progress: ${data.progress_percentage}% - ${data.task_description}`
    });

    console.log(`[WebSocket] Task progress for ${data.agent_name}: ${data.progress_percentage}%`);
  }

  private handleHITLRequestCreated(event: HitlRequestCreatedEvent | any) {
    console.log(`[WebSocket] HITL request received:`, event);

    const { data } = event;
    const { addLog, addMessage } = useAppStore.getState();

    // Use dynamic import to avoid circular dependency issues
    import('@/lib/stores/hitl-store').then(({ useHITLStore }) => {
      const { addRequest } = useHITLStore.getState();

      addRequest({
        agentName: data.agent_type || "System",
        decision: data.request_type || "Pre-execution approval",
        context: {
          approvalId: data.approval_id,
          agentType: data.agent_type,
          requestType: data.request_type,
          estimatedTokens: data.estimated_tokens,
          estimatedCost: data.estimated_cost,
          expiresAt: data.expires_at,
          requestData: data.request_data
        },
        priority: (data.estimated_cost && data.estimated_cost > 5) ? 'high' : 'medium'
      });

      console.log(`[WebSocket] HITL request added to store for ${data.agent_type}: ${data.approval_id}`);
    }).catch(error => {
      console.error('[WebSocket] Error loading HITL store:', error);
    });

    addMessage({
      type: "hitl",
      agent: "HITL System",
      content: `HITL Request: ${data.request_type} approval needed for ${data.agent_type}`,
      urgency: (data.estimated_cost && data.estimated_cost > 5) ? "high" : "medium",
      requestId: data.approval_id
    });

    addLog({
      agent: "HITL",
      level: (data.estimated_cost && data.estimated_cost > 5) ? "warning" : "info",
      message: `HITL approval required: ${data.request_type} for ${data.agent_type}`
    });

    console.log(`[WebSocket] HITL request created: ${data.approval_id}`, data);
  }

  private handleArtifactGenerated(event: ArtifactGeneratedEvent) {
    const { data } = event;
    const { addLog } = useAppStore.getState();

    addLog({
      agent: data.agent_name,
      level: "success",
      message: `Artifact generated: ${data.artifact_name} (${data.artifact_type})`
    });

    console.log(`[WebSocket] Artifact generated: ${data.artifact_name}`);
  }

  private handleErrorNotification(event: ErrorNotificationEvent) {
    const { data } = event;
    const { updateAgent, addLog } = useAppStore.getState();

    if (data.agent_type) {
      updateAgent({
        name: data.agent_type,
        status: "error",
        task: data.message
      });
    }

    addLog({
      agent: data.agent_type || "System",
      level: "error",
      message: `${data.message} (Code: ${data.error_code})`
    });

    console.error(`[WebSocket] Error notification: ${data.message}`);
  }

  private handleAgentChatMessage(event: AgentChatMessageEvent) {
    const { data } = event;
    const { addMessage } = useAppStore.getState();

    addMessage({
      type: "agent",
      agent: data.agent_type,
      content: data.message
    });

    console.log(`[WebSocket] Chat message from ${data.agent_type}`);
  }

  // Legacy message handler for backward compatibility
  private handleMessage(message: any) {
    console.log("[DEBUG] Legacy message received:", message);
    const { type, agent_name, content, status, task, error_message } = message;

    const { updateAgent, addLog, addMessage } = useAppStore.getState();

    switch (type) {
      case "agent_status":
        if (agent_name) {
          updateAgent({ name: agent_name, status: status, task: task });
          addLog({ agent: agent_name, level: "info", message: `Agent ${agent_name} is now ${status}. Task: ${task}` });
        }
        break;

      case "agent_error":
        if (agent_name) {
          updateAgent({ name: agent_name, status: "error", task: error_message });
          addLog({ agent: agent_name, level: "error", message: error_message || "Agent error occurred" });
        }
        break;

      case "agent_response":
        if (agent_name && content) {
          addMessage({ type: "agent", agent: agent_name, content: content });
        }
        break;

      case "system":
        if (content) {
          addMessage({ type: "system", agent: "System", content: content });
        }
        break;

      default:
        if (content) {
          addLog({ agent: "System", level: "info", message: content });
        }
        break;
    }
  }

  private updateConnectionStatus(status: ConnectionStatus) {
    this.statusCallbacks.forEach((callback) => callback(status));
  }

  onStatusChange(callback: (status: ConnectionStatus) => void) {
    this.statusCallbacks.push(callback);
    return () => {
      const index = this.statusCallbacks.indexOf(callback);
      if (index > -1) this.statusCallbacks.splice(index, 1);
    };
  }

  getConnectionStatus(): ConnectionStatus {
    const status = this.globalConnection.getStatus();
    return {
      connected: status.connected,
      reconnecting: status.reconnecting,
      error: status.error
    };
  }

  // Project-scoped connection management
  connectToProject(projectId: string): EnhancedWebSocketClient {
    if (!this.projectConnections.has(projectId)) {
      const connection = websocketManager.getProjectConnection(projectId);
      this.projectConnections.set(projectId, connection);

      // Set up project-specific event handlers
      this.setupProjectEventHandlers(connection, projectId);
    }

    return this.projectConnections.get(projectId)!;
  }

  private setupProjectEventHandlers(connection: EnhancedWebSocketClient, projectId: string) {
    // Subscribe to project-specific events
    connection.on('agent_status_changed', (event) => {
      event.project_id = projectId;
      this.handleAgentStatusChanged(event);
    });

    connection.on('task_progress_updated', (event) => {
      event.project_id = projectId;
      this.handleTaskProgressUpdated(event);
    });

    connection.on('artifact_generated', (event) => {
      event.project_id = projectId;
      this.handleArtifactGenerated(event);
    });

    connection.on('agent_chat_message', (event) => {
      event.project_id = projectId;
      this.handleAgentChatMessage(event);
    });
  }

  disconnectFromProject(projectId: string) {
    websocketManager.disconnectProject(projectId);
    this.projectConnections.delete(projectId);
  }

  send(message: string | object, projectId?: string) {
    const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
    console.log("[DEBUG] Sending message:", messageStr);

    if (projectId) {
      const projectConnection = this.connectToProject(projectId);
      projectConnection.send(messageStr);
    } else {
      this.globalConnection.send(messageStr);
    }
  }

  sendChatMessage(message: string, projectId?: string) {
    const messageObj = {
      type: "chat_message",
      data: { message },
      project_id: projectId
    };

    this.send(messageObj, projectId);
  }

  // Enhanced project management methods
  startProject(brief: string, projectId?: string) {
    const message = {
      type: "start_project",
      data: { brief },
      project_id: projectId
    };

    this.send(message, projectId);
  }

  sendArtifactPreference(itemId: string, enabled: boolean) {
    const message = {
      type: "artifact_preference",
      data: { itemId, enabled }
    };

    this.send(message);
  }

  respondToHITL(requestId: string, action: 'approve' | 'reject', comment?: string) {
    const message = {
      type: "hitl_response",
      data: { requestId, action, comment }
    };

    this.send(message);
  }

  triggerEmergencyStop(projectId: string, reason: string) {
    const message = {
      type: "emergency_stop",
      data: { projectId, reason }
    };

    this.send(message, projectId);

    // Also trigger through safety event handler for immediate UI response
    safetyEventHandler.triggerEmergencyStop(projectId, reason);
  }

  // Safety-related methods
  getSafetyAlerts() {
    return safetyEventHandler.getActiveAlerts();
  }

  acknowledgeAlert(alertId: string) {
    safetyEventHandler.acknowledgeAlert(alertId);
  }

  clearAcknowledgedAlerts() {
    safetyEventHandler.clearAcknowledgedAlerts();
  }

  onSafetyAlert(handler: (alert: any) => void) {
    return safetyEventHandler.onSafetyAlert(handler);
  }

  disconnect() {
    this.shouldAutoConnect = false;

    // Disconnect safety event handler
    safetyEventHandler.disconnectFromWebSocket();

    // Disconnect all WebSocket connections
    websocketManager.disconnectAll();
    this.projectConnections.clear();

    console.log('[WebSocketService] All connections and safety handling disconnected');
  }
}

export const websocketService = new WebSocketService();