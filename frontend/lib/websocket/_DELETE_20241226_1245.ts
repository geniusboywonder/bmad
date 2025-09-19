  private handleConnectionFailure() {
    console.log(`[WebSocket] Connection failed (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`)
    
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn("[WebSocket] Max reconnection attempts reached - entering offline mode")
      this.updateConnectionStatus({
        connected: false,
        reconnecting: false,
        error: "Unable to connect to backend. Operating in offline mode."
      })
      
      // Add a user-friendly log message
      useLogStore.getState().addLog({
        agent: "System",
        level: "warning",
        message: "Backend connection unavailable. Demo data only - real-time features disabled.",
        metadata: { 
          websocket_url: this.getWebSocketUrl(),
          offline_mode: true 
        }
      })
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000) // Max 30 seconds
    
    console.log(`[WebSocket] Retrying connection in ${delay}ms...`)
    this.reconnectTimeout = setTimeout(() => {
      this.connect()
    }, delay)
  }

  private handleConnectionError(error: Event | Error, errorType: WebSocketErrorInfo['type'] = 'unknown') {
    const errorMessage = error instanceof Error ? error.message : 'Unknown WebSocket error'
    console.warn(`[WebSocket] Error occurred (readyState: ${this.getReadyStateString()}):`, errorMessage)
    
    // Don't spam logs with connection errors - only log first few attempts
    if (this.reconnectAttempts < 3) {
      useLogStore.getState().addLog({
        agent: "WebSocket",
        level: "warning", 
        message: `Connection error: ${errorMessage}`,
        metadata: { 
          errorType, 
          readyState: this.getReadyStateString(),
          attempt: this.reconnectAttempts + 1
        }
      })
    }
  }