import { useAppStore } from "../stores/app-store";

// --- TYPE DEFINITIONS ---

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

// --- SIMPLIFIED WEB-SOCKET SERVICE ---

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private shouldAutoConnect = false;
  private statusCallbacks: ((status: ConnectionStatus) => void)[] = [];
  private connectionStatus: ConnectionStatus = { connected: false, reconnecting: false };

  constructor() {
    this.connect = this.connect.bind(this);
  }

  private getWebSocketUrl(): string {
    // Use the backend URL directly as specified in environment variables
    // For development, this is typically ws://localhost:8000/ws
    return "ws://localhost:8000/ws";
  }

  connect() {
    if (typeof window === "undefined" || this.ws) return;

    if (!this.shouldAutoConnect) {
      console.log("[WebSocket] Auto-connect is disabled.");
      return;
    }

    const url = this.getWebSocketUrl();
    console.log(`[WebSocket] Connecting to: ${url}`);
    this.updateConnectionStatus({ connected: false, reconnecting: true });

    try {
      this.ws = new WebSocket(url);
      this.setupEventHandlers();
    } catch (error) {
      console.error("[WebSocket] Connection failed to initiate:", error);
      this.updateConnectionStatus({ connected: false, reconnecting: false, error: "Connection failed" });
    }
  }

  enableAutoConnect() {
    this.shouldAutoConnect = true;
    this.connect();
  }

  private setupEventHandlers() {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log("[WebSocket] Connection established.");
      this.reconnectAttempts = 0;
      this.updateConnectionStatus({ connected: true, reconnecting: false, error: undefined });
      useAppStore.getState().setConnectionStatus({ connected: true, reconnecting: false });
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error("[WebSocket] Failed to parse message:", error);
      }
    };

    this.ws.onclose = () => {
      console.log("[WebSocket] Connection closed.");
      this.updateConnectionStatus({ connected: false, reconnecting: false, error: "Connection closed" });
      useAppStore.getState().setConnectionStatus({ connected: false, reconnecting: false });
      if (this.shouldAutoConnect && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.attemptReconnect();
      }
    };

    this.ws.onerror = () => {
      console.error("[WebSocket] An error occurred.");
      this.updateConnectionStatus({ connected: false, reconnecting: false, error: "WebSocket error" });
      useAppStore.getState().setConnectionStatus({ connected: false, reconnecting: false });
    };
  }

  private handleMessage(message: any) {
    console.log("[DEBUG] Received message from backend:", message);
    const { type, agent_name, content, status, task, error_message } = message;

    if (type === "ping") {
      this.send(JSON.stringify({ type: "pong" }));
      return;
    }

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

  private attemptReconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    console.log(`[WebSocket] Reconnecting in ${delay}ms...`);
    this.updateConnectionStatus({ connected: false, reconnecting: true });
    useAppStore.getState().setConnectionStatus({ connected: false, reconnecting: true });
    setTimeout(this.connect, delay);
  }

  private updateConnectionStatus(status: Partial<ConnectionStatus>) {
    this.connectionStatus = { ...this.connectionStatus, ...status };
    this.statusCallbacks.forEach((callback) => callback(this.connectionStatus));
  }

  onStatusChange(callback: (status: ConnectionStatus) => void) {
    this.statusCallbacks.push(callback);
    return () => {
      const index = this.statusCallbacks.indexOf(callback);
      if (index > -1) this.statusCallbacks.splice(index, 1);
    };
  }

  getConnectionStatus(): ConnectionStatus {
    return { ...this.connectionStatus };
  }

  send(message: string) {
    console.log("[DEBUG] Sending message from frontend:", message);
    if (this.ws) {
      console.log(`[WebSocket] Current readyState before sending: ${this.ws.readyState}`);
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(message);
      } else {
        console.warn("[WebSocket] Connection not open. Message not sent. readyState: ", this.ws.readyState);
      }
    } else {
      console.warn("[WebSocket] WebSocket instance is null. Message not sent.");
    }
  }

  startProject(brief: string) {
    this.send(JSON.stringify({
      type: "start_project",
      data: {
        brief: brief,
      },
    }));
  }

  disconnect() {
    this.shouldAutoConnect = false;
    if (this.ws) {
      this.ws.close();
    }
  }
}

export const websocketService = new WebSocketService();