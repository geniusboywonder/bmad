import WebSocket from 'ws';

class WebSocketBridge {
  private static instance: WebSocketBridge;
  private ws: WebSocket | null = null;
  private messageListeners: ((message: any) => void)[] = [];

  private constructor() {
    this.connect();
  }

  public static getInstance(): WebSocketBridge {
    if (!WebSocketBridge.instance) {
      WebSocketBridge.instance = new WebSocketBridge();
    }
    return WebSocketBridge.instance;
  }

  private connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this.ws = new WebSocket('ws://localhost:8000/api/ws');

    this.ws.on('open', () => {
      console.log('Bridge: Connected to backend WebSocket');
    });

    this.ws.on('message', (data) => {
      const message = JSON.parse(data.toString());
      console.log('Bridge: Received from backend:', message);
      
      // Handle heartbeat pings by responding with pong
      if (message.type === 'heartbeat' && message.content === 'ping') {
        console.log('Bridge: Responding to heartbeat ping with pong');
        this.sendMessage({
          type: 'heartbeat_response',
          content: 'pong',
          timestamp: new Date().toISOString()
        });
      }
      
      this.messageListeners.forEach(listener => listener(message));
    });

    this.ws.on('close', () => {
      console.log('Bridge: Disconnected from backend WebSocket');
      this.ws = null;
      setTimeout(() => this.connect(), 1000);
    });

    this.ws.on('error', (error) => {
      console.error('Bridge: Backend WebSocket error:', error);
    });
  }

  public sendMessage(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('Bridge: Sending to backend:', message);
      this.ws.send(JSON.stringify(message));
    }
  }

  public addMessageListener(listener: (message: any) => void) {
    this.messageListeners.push(listener);
  }

  public removeMessageListener(listener: (message: any) => void) {
    this.messageListeners = this.messageListeners.filter(l => l !== listener);
  }
}

export const webSocketBridge = WebSocketBridge.getInstance();
