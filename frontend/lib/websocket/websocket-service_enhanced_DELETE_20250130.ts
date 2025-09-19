  private attemptReconnect() {
    if (!this.shouldAutoConnect || !this.config.enableAutoReconnect) {
      console.log("[WebSocket] Reconnection skipped: auto-connect disabled")
      return
    }

    // Don't increment attempts on first reconnection after deliberate disconnect
    if (this.ws && this.ws.readyState === WebSocket.CLOSED) {
      this.reconnectAttempts++
    }
    
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(`[WebSocket] Max reconnect attempts (${this.maxReconnectAttempts}) reached. Stopping reconnection.`)
      this.updateConnectionStatus({ 
        connected: false, 
        reconnecting: false, 
        error: `Failed to reconnect after ${this.maxReconnectAttempts} attempts. Try refreshing the page.` 
      })
      // Add log entry for user visibility
      if (typeof window !== 'undefined') {
        const { useLogStore } = require('@/lib/stores/log-store')
        useLogStore.getState().addLog({
          agent: "System",
          level: "error", 
          message: `❌ WebSocket connection failed after ${this.maxReconnectAttempts} attempts. Please refresh the page.`
        })
      }
      return
    }
    
    this.updateConnectionStatus({ connected: false, reconnecting: true })

    // Exponential backoff with jitter but more aggressive initial retry
    let delay: number
    if (this.reconnectAttempts === 1) {
      delay = 1000 // First retry after 1 second
    } else if (this.reconnectAttempts === 2) {
      delay = 3000 // Second retry after 3 seconds
    } else {
      // Exponential backoff for subsequent attempts
      const jitter = Math.random() * 1000
      delay = Math.min(this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts) + jitter, this.maxReconnectDelay)
    }

    console.log(`[WebSocket] Reconnecting in ${delay.toFixed(0)}ms... (Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    
    // Add visible feedback for user
    if (typeof window !== 'undefined') {
      const { useLogStore } = require('@/lib/stores/log-store')
      useLogStore.getState().addLog({
        agent: "System",
        level: "info",
        message: `🔄 Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      })
    }
    
    setTimeout(() => {
      // Check if we should still reconnect before attempting
      if (this.shouldAutoConnect && this.config.enableAutoReconnect) {
        this.connect()
      }
    }, delay)
  }

  // Enhanced connection reset for navigation scenarios
  ensureConnection() {
    const status = this.getConnectionStatus()
    if (!status.connected && !status.reconnecting && this.shouldAutoConnect) {
      console.log("[WebSocket] Ensuring connection after navigation")
      this.reconnectAttempts = 0 // Reset attempts for navigation-based reconnection
      this.connect()
    }
    return status
  }

  // Add method to reset reconnection state
  resetReconnectionState() {
    this.reconnectAttempts = 0
    console.log("[WebSocket] Reconnection state reset")
  }
