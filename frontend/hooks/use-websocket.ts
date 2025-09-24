"use client"

import { useState, useEffect, useCallback } from "react"
import { websocketService, type ConnectionStatus } from "../lib/services/websocket/websocket-service"

const defaultConnectionStatus: ConnectionStatus = {
  connected: false,
  reconnecting: false,
}

export function useWebSocket(autoConnect = true) {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(defaultConnectionStatus)

  useEffect(() => {
    const currentStatus = websocketService.getConnectionStatus()
    setConnectionStatus(currentStatus)

    const unsubscribe = websocketService.onStatusChange(setConnectionStatus)

    if (autoConnect && !currentStatus.connected && !currentStatus.reconnecting) {
      console.log("[WebSocket] Auto-connecting...")
      websocketService.enableAutoConnect()
    }

    return () => {
      unsubscribe()
    }
  }, [autoConnect])

  const connect = useCallback(() => {
    websocketService.enableAutoConnect()
  }, [])

  const disconnect = useCallback(() => {
    websocketService.disconnect()
  }, [])

  const startProject = useCallback((brief: string) => {
    websocketService.startProject(brief)
  }, [])

  return {
    connectionStatus,
    connect,
    disconnect,
    startProject,
    isConnected: connectionStatus.connected,
    isReconnecting: connectionStatus.reconnecting,
  }
}
