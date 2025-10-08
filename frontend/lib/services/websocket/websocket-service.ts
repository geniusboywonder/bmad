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
  PolicyViolationEvent,
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
    this.globalConnection.on('TASK_STARTED', this.handleTaskStarted.bind(this));
    this.globalConnection.on('task_started', this.handleTaskStarted.bind(this)); // backwards compatibility
    this.globalConnection.on('TASK_COMPLETED', this.handleTaskCompleted.bind(this));
    this.globalConnection.on('task_completed', this.handleTaskCompleted.bind(this)); // backwards compatibility
    this.globalConnection.on('HITL_REQUEST_CREATED', this.handleHITLRequestCreated.bind(this));
    this.globalConnection.on('hitl_request_created', this.handleHITLRequestCreated.bind(this)); // backwards compatibility
    this.globalConnection.on('artifact_generated', this.handleArtifactGenerated.bind(this));
    this.globalConnection.on('error_notification', this.handleErrorNotification.bind(this));
    this.globalConnection.on('agent_chat_message', this.handleAgentChatMessage.bind(this));
    this.globalConnection.on('hitl_approval_response', this.handleHITLApprovalResponse.bind(this));
    this.globalConnection.on('hitl_counter', this.handleHITLCounterEvent.bind(this));
    this.globalConnection.on('policy_violation', this.handlePolicyViolation.bind(this));
  }

  connect() {
    if (typeof window === "undefined") return;

    if (!this.shouldAutoConnect) {
      console.log("[WebSocket] Auto-connect is disabled.");
      return;
    }

    console.log("[WebSocket] Connecting to backend at ws://localhost:8000/ws");
    this.globalConnection.connect();

    // Add connection status debugging
    setTimeout(() => {
      console.log("[WebSocket] Connection status after 2s: checking...");
    }, 2000);
  }

  enableAutoConnect() {
    this.shouldAutoConnect = true;
    this.connect();

    // Poll for pending HITL requests as fallback
    this.startHITLPolling();
  }

  private startHITLPolling() {
    // Check for pending HITL requests every 10 seconds as backup
    const interval = setInterval(async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/hitl/approvals?status=pending');
        if (response.ok) {
          const pendingRequests = await response.json();
          const { addRequest } = useHITLStore.getState();
          const currentRequests = useHITLStore.getState().requests;

          // Add any missing requests
          for (const request of pendingRequests.approvals || []) {
            const existingRequest = currentRequests.find(r => r.context?.approvalId === request.id);

            // Skip if request was already resolved locally (approved/rejected/modified)
            // This prevents re-adding requests that were approved locally but backend hasn't updated yet
            if (existingRequest && existingRequest.status !== 'pending') {
              console.log(`[WebSocket] Skipping polling add for ${request.id} - already ${existingRequest.status} locally`);
              continue;
            }

            // Only add if request doesn't exist
            if (!existingRequest) {
              console.log('[WebSocket] Adding missing HITL request from API polling:', request.id);
              addRequest({
                agentName: request.agent_type || "System",
                decision: request.request_type || "Pre-execution approval",
                context: {
                  approvalId: request.id,
                  agentType: request.agent_type,
                  requestType: request.request_type,
                  estimatedTokens: request.estimated_tokens,
                  estimatedCost: request.estimated_cost,
                  expiresAt: request.expires_at,
                  requestData: request.request_data,
                  taskId: request.task_id,
                  projectId: request.project_id
                },
                priority: (request.estimated_cost && request.estimated_cost > 5) ? 'high' : 'medium'
              });

              // CRITICAL FIX: Also add the chat message (was missing before)
              const { addMessage } = useAppStore.getState();
              const taskInstructions = request.request_data?.instructions || "Execute task";
              addMessage({
                type: "hitl_request",
                agent: `${request.agent_type} Agent`,
                content: `🚨 **HITL Approval Required**\n\nI need permission to: "${taskInstructions}"\n\n📊 **Estimated cost:** $${request.estimated_cost?.toFixed(4) || '0.0150'}\n⏱️ **Estimated tokens:** ${request.estimated_tokens || 100}\n\n⚠️ **Waiting for human approval before proceeding...**`,
                urgency: (request.estimated_cost && request.estimated_cost > 5) ? "high" : "medium",
                requestId: request.id,
                taskId: request.task_id,
                approvalId: request.id,
                hitlStatus: "pending"
              });
            }
          }
        }
      } catch (error) {
        console.warn('[WebSocket] HITL polling failed:', error);
      }
    }, 10000);

    // Store interval for cleanup
    if (typeof window !== 'undefined') {
      (window as any).hitlPollingInterval = interval;
    }
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

  private handleTaskStarted(event: any) {
    const { data } = event;
    const { addMessage, updateAgent } = useAppStore.getState();

    // Update agent status
    updateAgent({
      name: data.agent_type,
      status: "working",
      task: data.message || "Processing task"
    });

    // Add a chat message showing task started
    addMessage({
      type: "agent",
      agent: `${data.agent_type} Agent`,
      content: `🚀 **Task Started**\n\n${data.message || "I've begun processing your request."}\n\n⏱️ Started at: ${new Date(data.timestamp).toLocaleTimeString()}`,
      taskId: data.task_id
    });

    console.log(`[WebSocket] Task started for ${data.agent_type}: ${data.task_id}`);
  }

  private handleTaskCompleted(event: any) {
    const { data } = event;
    const { addMessage, updateAgent } = useAppStore.getState();

    // Update agent status
    updateAgent({
      name: data.agent_type,
      status: "idle",
      task: null
    });

    // Add a chat message showing task completion
    const outputSummary = typeof data.output?.output === 'string'
      ? data.output.output
      : data.output?.message || "Task completed successfully";

    addMessage({
      type: "agent",
      agent: `${data.agent_type} Agent`,
      content: `✅ **Task Completed**\n\n${outputSummary}\n\n⏱️ Completed at: ${new Date(data.timestamp).toLocaleTimeString()}`,
      taskId: data.task_id
    });

    console.log(`[WebSocket] Task completed for ${data.agent_type}: ${data.task_id}`);
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
    console.log(`[WebSocket] HITL event data:`, event.data);

    const { data } = event;
    const { addLog, addMessage } = useAppStore.getState();
    const { addRequest } = useHITLStore.getState();

    // Enhanced logging for debugging
    console.log(`[WebSocket] Adding HITL request to store:`, {
      agentName: data.agent_type || "System",
      decision: data.request_type || "Pre-execution approval",
      approvalId: data.approval_id
    });

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
        requestData: data.request_data,
        taskId: data.task_id,
        projectId: data.project_id // Include project ID for navigation
      },
      priority: (data.estimated_cost && data.estimated_cost > 5) ? 'high' : 'medium'
    });

    console.log(`[WebSocket] HITL request added to store for ${data.agent_type}: ${data.approval_id}`);

    // Add a separate, dedicated HITL message - each HITL gets its own unique message
    const taskInstructions = data.request_data?.instructions || "Execute task";
    addMessage({
      type: "hitl_request",
      agent: `${data.agent_type} Agent`,
      content: `🚨 **HITL Approval Required**\n\nI need permission to: "${taskInstructions}"\n\n📊 **Estimated cost:** $${data.estimated_cost?.toFixed(4) || '0.0150'}\n⏱️ **Estimated tokens:** ${data.estimated_tokens || 100}\n\n⚠️ **Waiting for human approval before proceeding...**`,
      urgency: (data.estimated_cost && data.estimated_cost > 5) ? "high" : "medium",
      requestId: data.approval_id,
      taskId: data.task_id,
      approvalId: data.approval_id, // Add unique identifier for this specific HITL request
      hitlStatus: "pending" // Track the status of this specific HITL
    });
  }

  // Add handler for HITL approval responses
  private handleHITLApprovalResponse(event: any) {
    const { data } = event;
    const { updateMessage } = useAppStore.getState();

    console.log(`[WebSocket] HITL approval response:`, data);

    const action = (data.action ?? (data.approved ? "approve" : "reject")) as "approve" | "reject" | "amend";
    const mappedStatus = action === "approve" ? "approved" : action === "reject" ? "rejected" : "modified";

    const approvalResult =
      action === "approve"
        ? "✅ **APPROVED** — Agent may proceed."
        : action === "reject"
          ? "⛔ **REJECTED** — Agent workflow halted."
          : "🔄 **REDIRECTED** — Agent must adjust before continuing.";

    const timestamp = new Date().toLocaleTimeString();

    updateMessage(data.approval_id, {
      content: `${approvalResult}\n\nOriginal request: "${data.original_instructions || "Execute task"}"\n\n📊 **Cost:** $${data.estimated_cost?.toFixed(4) || "0.0150"}\n⏱️ **Tokens:** ${data.estimated_tokens || 100}\n🕒 **Decision made at:** ${timestamp}${data.comment ? `\n💬 **Reviewer note:** ${data.comment}` : ""}`,
      hitlStatus: mappedStatus,
      metadata: {
        ...(data.metadata || {}),
        selectedAction: action,
        reviewerComment: data.comment ?? null
      }
    });
  }

  private handleHITLCounterEvent(event: any) {
    const projectId: string | undefined = event.project_id || event.data?.project_id;
    if (!projectId) {
      console.warn('[WebSocket] HITL counter event missing project_id', event);
      return;
    }

    const data = event.data || {};
    const counterTotal = data.counter_total;
    const counterRemaining = data.counter_remaining;
    const hitlEnabled = data.hitl_enabled;
    const locked = data.locked;
    const reason = data.reason;

    if (
      typeof counterTotal !== 'number' ||
      typeof counterRemaining !== 'number' ||
      typeof hitlEnabled !== 'boolean'
    ) {
      console.warn('[WebSocket] HITL counter event missing required fields', event);
      return;
    }

    useHITLStore.getState().applyServerSettings(
      projectId,
      {
        counter_total: counterTotal,
        counter_remaining: counterRemaining,
        hitl_enabled: hitlEnabled,
        locked,
      },
      reason
    );

    const { addMessage, updateMessage, conversation } = useAppStore.getState();
    const messageId = `hitl-counter-${projectId}`;
    const metadata = {
      projectId,
      counterTotal,
      counterRemaining,
      hitlEnabled,
      locked: locked ?? counterRemaining <= 0,
      reason,
    };

    const shouldDisplay = ['counter_limit_reached', 'counter_limit_active'].includes(reason);
    const exists = conversation.some(
      (message) => message.approvalId === messageId && message.type === 'hitl_counter'
    );

    if (shouldDisplay && !exists) {
      addMessage({
        type: 'hitl_counter',
        agent: 'System',
        content: '',
        approvalId: messageId,
        metadata,
      });
    } else if (exists) {
      updateMessage(messageId, { metadata });
    }
  }

  private handlePolicyViolation(event: PolicyViolationEvent) {
    const { data, project_id: projectId } = event;
    const { addLog, addMessage, setPolicyGuidance } = useAppStore.getState();

    const status = data.reason_code === 'PROMPT_MISALIGNED' ? 'needs_clarification' : 'denied';

    setPolicyGuidance({
      status,
      reasonCode: data.reason_code,
      message: data.message,
      currentPhase: data.current_phase,
      allowedAgents: data.allowed_agents,
      timestamp: data.timestamp,
    });

    addLog({
      agent: 'Policy',
      level: 'info',
      message: `Request blocked: ${data.message}`,
    });

    addMessage({
      type: 'system',
      agent: 'Policy',
      content: `⚖️ **Policy Enforcement**\n\n${data.message}\n\n**Current phase:** ${data.current_phase}\n**Allowed agents:** ${data.allowed_agents.join(', ')}`,
      metadata: {
        projectId,
        reasonCode: data.reason_code,
      },
    });
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

    connection.on('hitl_request_created', (event) => {
      event.project_id = projectId;
      this.handleHITLRequestCreated(event);
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
