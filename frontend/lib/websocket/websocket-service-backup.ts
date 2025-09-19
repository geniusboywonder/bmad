import { useAgentStore } from "../stores/agent-store"
import { useLogStore } from "../stores/log-store"
import { useArtifactStore } from "../stores/artifact-store"

// --- TYPE DEFINITIONS ---

export interface WebSocketMessage {
  type: string
  // Based on AG-UI protocol, most data is in a nested object.
  data?: any
  // Fields from AG-UI that can appear at the top level
  agent_name?: string;
  content?: string;
  payload?: any;
  timestamp: string
}

export interface ConnectionStatus {
  connected: boolean
  reconnecting: boolean
  lastConnected?: Date
  error?: string
  latency?: number
  reconnectCount?: number
  messagesSent?: number
  messagesReceived?: number
}

export interface ConnectionMetrics {
  totalConnections: number
  totalDisconnections: number
  totalMessagesSent: number
  totalMessagesReceived: number
  averageLatency: number
  uptime: number
  lastError?: string
}

// --- ENHANCED WEB-SOCKET SERVICE ---

class EnhancedWebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private reconnectDelay = 1000 // start with 1s
  private maxReconnectDelay = 30000 // max delay of 30s
  private maxReconnectAttempts = 10
  private connectionStatus: ConnectionStatus = { 
    connected: false, 
    reconnecting: false, 
    reconnectCount: 0,
    messagesSent: 0,
    messagesReceived: 0
  }
  private statusCallbacks: ((status: ConnectionStatus) => void)[] = []
  private messageQueue: any[] = []
  private batchQueue: any[] = []
  private batchTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null
  private latencyTimer: NodeJS.Timeout | null = null
  private pingStartTime: number = 0
  
  // Connection metrics
  private metrics: ConnectionMetrics = {
    totalConnections: 0,
    totalDisconnections: 0,
    totalMessagesSent: 0,
    totalMessagesReceived: 0,
    averageLatency: 0,
    uptime: 0
  }
  private connectionStartTime: number = 0

  // Enhanced configuration
  private config = {
    batchTimeout: 100, // ms to wait before sending batch
    maxBatchSize: 50, // max messages per batch
    heartbeatInterval: 30000, // 30 seconds
    latencyCheckInterval: 60000, // 1 minute
    messageQueueLimit: 1000, // max queued messages
    enableMetrics: true,
    enableLatencyChecks: true,
    enableAutoReconnect: true
  }

  // This flag is controlled by the UI to enable/disable auto-connection.
  private shouldAutoConnect = false

  constructor() {
    this.updateConnectionStatus = this.updateConnectionStatus.bind(this)
    this.handleMessage = this.handleMessage.bind(this)
    this.attemptReconnect = this.attemptReconnect.bind(this)
    this.setupEventHandlers = this.setupEventHandlers.bind(this)
    this.sendHeartbeat = this.sendHeartbeat.bind(this)
    this.checkLatency = this.checkLatency.bind(this)
  }

  private getWebSocketUrl(): string {
    if (typeof window !== 'undefined') {
        // Check if we have environment variables from Next.js
        const envWebSocketUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL;
        if (envWebSocketUrl) {
            console.log(`[WebSocket] Using environment URL: ${envWebSocketUrl}`);
            return envWebSocketUrl;
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        
        // For localhost development
        if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
            const url = `${protocol}//localhost:8000/api/ws`;
            console.log(`[WebSocket] Development URL: ${url}`);
            return url;
        }
        
        // For production deployments
        const url = `${protocol}//${window.location.host}/api/ws`;
        console.log(`[WebSocket] Production URL: ${url}`);
        return url;
    }
    // Default for non-browser environments
    return 'ws://localhost:8000/api/ws';
  }

  connect() {
    if (typeof window === "undefined" || this.ws) {
      console.log("[WebSocket] Connection skipped: Not in browser or already connected/connecting.");
      return
    }

    if (!this.shouldAutoConnect) {
      console.log("[WebSocket] Connection skipped: Auto-connect is disabled.")
      return
    }

    const url = this.getWebSocketUrl();
    console.log(`[WebSocket] Attempting to connect to: ${url}`)

    try {
      this.ws = new WebSocket(url)
      this.setupEventHandlers()
      this.updateConnectionStatus({ connected: false, reconnecting: true })
      this.connectionStartTime = Date.now()
    } catch (error) {
      console.error("[WebSocket] Connection failed to initiate:", error)
      this.updateConnectionStatus({
        connected: false,
        reconnecting: false,
        error: error instanceof Error ? error.message : "Connection failed",
      })
      this.metrics.lastError = error instanceof Error ? error.message : "Connection failed"
    }
  }

  // This should be called by the UI to start the connection process.
  enableAutoConnect() {
    this.shouldAutoConnect = true
    this.connect()
  }

  private setupEventHandlers() {
    if (!this.ws) return

    this.ws.onopen = () => {
      console.log("[WebSocket] Connection established.")
      this.reconnectAttempts = 0
      this.metrics.totalConnections++
      
      this.updateConnectionStatus({
        connected: true,
        reconnecting: false,
        lastConnected: new Date(),
        error: undefined,
        reconnectCount: this.metrics.totalConnections
      })
      
      // Start heartbeat and latency monitoring
      this.startHeartbeat()
      if (this.config.enableLatencyChecks) {
        this.startLatencyMonitoring()
      }
      
      // Process any queued messages
      this.processMessageQueue()
      this.requestArtifacts()
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        this.metrics.totalMessagesReceived++
        this.connectionStatus.messagesReceived = this.metrics.totalMessagesReceived
        this.handleMessage(message)
      } catch (error) {
        console.error("[WebSocket] Failed to parse message:", error)
      }
    }

    this.ws.onclose = (event) => {
      const reason = event.reason || 'No reason provided'
      const code = event.code
      const wasClean = event.wasClean
      
      console.log(`[WebSocket] Connection closed. Code: ${code}, Reason: ${reason}, Clean: ${wasClean}`)
      
      this.metrics.totalDisconnections++
      if (this.connectionStartTime) {
        this.metrics.uptime += Date.now() - this.connectionStartTime
      }
      
      // Stop heartbeat and latency monitoring
      this.stopHeartbeat()
      this.stopLatencyMonitoring()
      
      // Add detailed error message based on close code
      let errorMessage = `Connection closed (Code: ${code})`
      if (code === 1006) {
        errorMessage += ' - Backend server unreachable. Check if backend is running on port 8000.'
      } else if (code === 1000) {
        errorMessage += ' - Normal closure'
      } else if (reason) {
        errorMessage += ` - ${reason}`
      }
      
      useLogStore.getState().addLog({
        agent: "System",
        level: "error",
        message: errorMessage,
      })
      
      this.updateConnectionStatus({ connected: false, reconnecting: false, error: errorMessage })
      this.metrics.lastError = errorMessage
      
      // Only attempt reconnect if it wasn't a clean close and we haven't exceeded max attempts
      if (!wasClean && this.config.enableAutoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.attemptReconnect()
      }
    }

    this.ws.onerror = (event) => {
      console.error("[WebSocket] An error occurred.", event)
      const errorMsg = "WebSocket error occurred. This usually means the backend server is not running or not accessible on port 8000."
      
      useLogStore.getState().addLog({
        agent: "System",
        level: "error",
        message: errorMsg,
      })
      
      this.updateConnectionStatus({
        connected: false,
        reconnecting: false,
        error: errorMsg,
      })
      
      this.metrics.lastError = errorMsg
    }
  }

  private handleMessage(message: WebSocketMessage) {
    console.log("[WebSocket] Received:", message);
    const { type, data, agent_name, content } = message;

    // Handle heartbeat responses for latency calculation
    if (type === 'heartbeat_response' || type === 'pong') {
      if (this.pingStartTime) {
        const latency = Date.now() - this.pingStartTime
        this.updateConnectionStatus({ latency })
        this.updateAverageLatency(latency)
        this.pingStartTime = 0
      }
      return // Don't log heartbeat responses
    }

    // The log store is our central sink for all messages for now.
    const log = (level: 'info' | 'error' = 'info', overrideContent?: string) => {
        const agent = agent_name || (data && data.agent_name) || "System";
        const msgContent = overrideContent || content || (data && (data.content || data.thought || data.error)) || "No message content.";
        useLogStore.getState().addLog({ agent, level, message: msgContent });
    }

    switch (type) {
      case 'heartbeat':
        this.send({ type: 'heartbeat_response' });
        break;

      case 'agent_status':
        useAgentStore.getState().updateAgentFromMessage(message);
        log('info', `Agent ${agent_name} is now ${data?.status}. Task: ${data?.task}`);
        break;

      case 'agent_progress':
        useAgentStore.getState().updateAgentFromMessage(message);
        log('info', `Agent ${agent_name} progress: ${data?.stage} (${data?.current}/${data?.total})`);
        break;

      case 'agent_error':
        if (agent_name) {
          useAgentStore.getState().handleAgentError(agent_name, data?.error_message || "Unknown error");
        }
        log('error', data?.error_message || "Agent error occurred");
        break;

      case 'agent_response':
        log();
        break;

      case 'workflow_status':
        log('info', `Workflow ${data?.workflow_id}: ${data?.status}`);
        break;

      case 'error':
        const errorContent = data?.error || content || "Unknown error";
        if (agent_name) {
          useAgentStore.getState().handleAgentError(agent_name, errorContent);
        }
        log('error', errorContent);
        break;

      case 'system':
        // Handle system messages, e.g., the welcome message with client_id
        if (data?.event === 'connected') {
            console.log(`[WebSocket] Connected with client_id: ${data.client_id}`);
        }
        log();
        break;

      default:
        console.warn(`[WebSocket] Received unknown message type: ${type}`);
        log();
        break;
    }
  }

  private startHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
    }
    
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat()
    }, this.config.heartbeatInterval)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private sendHeartbeat() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.sendDirect({ type: 'ping', timestamp: Date.now() })
    }
  }

  private startLatencyMonitoring() {
    if (this.latencyTimer) {
      clearInterval(this.latencyTimer)
    }
    
    this.latencyTimer = setInterval(() => {
      this.checkLatency()
    }, this.config.latencyCheckInterval)
  }

  private stopLatencyMonitoring() {
    if (this.latencyTimer) {
      clearInterval(this.latencyTimer)
      this.latencyTimer = null
    }
  }

  private checkLatency() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.pingStartTime = Date.now()
      this.sendDirect({ type: 'ping', timestamp: this.pingStartTime })
    }
  }

  private updateAverageLatency(newLatency: number) {
    // Simple moving average calculation
    const alpha = 0.2 // smoothing factor
    this.metrics.averageLatency = this.metrics.averageLatency * (1 - alpha) + newLatency * alpha
  }

  private attemptReconnect() {
    if (!this.shouldAutoConnect || !this.config.enableAutoReconnect) {
      return
    }

    this.reconnectAttempts++
    
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(`[WebSocket] Max reconnect attempts (${this.maxReconnectAttempts}) reached. Stopping reconnection.`)
      this.updateConnectionStatus({ 
        connected: false, 
        reconnecting: false, 
        error: `Failed to reconnect after ${this.maxReconnectAttempts} attempts` 
      })
      return
    }
    
    this.updateConnectionStatus({ connected: false, reconnecting: true })

    // Exponential backoff with jitter
    const jitter = Math.random() * 1000 // add up to 1 second of jitter
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts) + jitter, this.maxReconnectDelay)

    console.log(`[WebSocket] Reconnecting in ${delay.toFixed(0)}ms... (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    setTimeout(() => this.connect(), delay)
  }

  private updateConnectionStatus(status: Partial<ConnectionStatus>) {
    this.connectionStatus = { ...this.connectionStatus, ...status }
    this.statusCallbacks.forEach((callback) => callback(this.connectionStatus))
  }

  onStatusChange(callback: (status: ConnectionStatus) => void) {
    this.statusCallbacks.push(callback)
    // Return a function to unsubscribe
    return () => {
      const index = this.statusCallbacks.indexOf(callback)
      if (index > -1) this.statusCallbacks.splice(index, 1)
    }
  }

  getConnectionStatus(): ConnectionStatus {
    return { ...this.connectionStatus }
  }

  getConnectionMetrics(): ConnectionMetrics {
    return { ...this.metrics }
  }

  private processMessageQueue() {
    if (this.messageQueue.length > 0) {
      console.log(`[WebSocket] Processing ${this.messageQueue.length} queued messages...`)
      // Send all messages in the queue
      while (this.messageQueue.length > 0 && this.messageQueue.length < this.config.messageQueueLimit) {
        const message = this.messageQueue.shift()
        this.send(message)
      }
      
      // If queue is still too large, drop oldest messages
      if (this.messageQueue.length >= this.config.messageQueueLimit) {
        const dropped = this.messageQueue.length - this.config.messageQueueLimit + 100
        this.messageQueue.splice(0, dropped)
        console.warn(`[WebSocket] Dropped ${dropped} old messages due to queue limit`)
      }
    }
  }

  private send(message: any) {
    this.batchQueue.push(message);

    // Send immediately if batch is full
    if (this.batchQueue.length >= this.config.maxBatchSize) {
      this.processBatchQueue()
      return
    }

    // Otherwise, wait for timeout
    if (!this.batchTimer) {
      this.batchTimer = setTimeout(() => {
        this.processBatchQueue();
      }, this.config.batchTimeout);
    }
  }

  private sendDirect(message: any) {
    // Send message immediately without batching (for heartbeats, etc.)
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        ...message,
        timestamp: new Date().toISOString(),
        session_id: "global_session"
      }))
      this.metrics.totalMessagesSent++
      this.connectionStatus.messagesSent = this.metrics.totalMessagesSent
    } else {
      console.warn("[WebSocket] Cannot send direct message: connection not open")
    }
  }

  private processBatchQueue() {
    if (this.batchQueue.length === 0) {
      this.batchTimer = null;
      return;
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const messagesToSend = [...this.batchQueue];
      this.batchQueue = [];
      
      const fullMessage = {
        type: "batch",
        messages: messagesToSend.map(msg => ({
          ...msg,
          timestamp: new Date().toISOString(),
          session_id: "global_session"
        }))
      };
      
      this.ws.send(JSON.stringify(fullMessage));
      this.metrics.totalMessagesSent += messagesToSend.length
      this.connectionStatus.messagesSent = this.metrics.totalMessagesSent
    } else {
      console.warn("[WebSocket] Connection not open. Queuing batch.");
      this.messageQueue.push(...this.batchQueue);
      this.batchQueue = [];
      if (!this.connectionStatus.reconnecting && this.config.enableAutoReconnect) {
        this.connect();
      }
    }

    this.batchTimer = null;
  }

  // Configuration methods
  updateConfig(newConfig: Partial<typeof this.config>) {
    this.config = { ...this.config, ...newConfig }
    console.log("[WebSocket] Configuration updated:", newConfig)
  }

  getConfig() {
    return { ...this.config }
  }

  // Public API methods
  startProject(brief: string) {
    this.send({
      type: "user_command",
      data: {
        command: "start_project",
        brief: brief,
      },
    })
  }

  testBackendConnection() {
    this.send({
      type: "user_command",
      data: {
        command: "ping",
      },
    })
  }

  testOpenAI() {
    this.send({
      type: "user_command",
      data: {
        command: "test_openai",
        message: "This is a test message to verify OpenAI integration is working properly."
      },
    })
  }

  requestArtifacts() {
    this.send({
      type: "artifacts_get_all",
    })
  }

  // Force immediate send of queued messages
  flushMessages() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer)
      this.batchTimer = null
    }
    this.processBatchQueue()
  }

  // Reset connection (force disconnect and reconnect)
  resetConnection() {
    console.log("[WebSocket] Forcing connection reset...")
    if (this.ws) {
      this.ws.close(1000, "Manual reset")
    }
    this.reconnectAttempts = 0
    setTimeout(() => {
      if (this.shouldAutoConnect) {
        this.connect()
      }
    }, 1000)
  }

  disconnect() {
    console.log("[WebSocket] Disconnecting...")
    this.shouldAutoConnect = false
    this.stopHeartbeat()
    this.stopLatencyMonitoring()
    
    if (this.batchTimer) {
      clearTimeout(this.batchTimer)
      this.batchTimer = null
    }
    
    if (this.ws) {
      this.ws.close(1000, "Manual disconnect")
    }
  }

  // Clear all queued messages
  clearMessageQueue() {
    this.messageQueue = []
    this.batchQueue = []
    console.log("[WebSocket] Message queues cleared")
  }
}

export const websocketService = new EnhancedWebSocketService()