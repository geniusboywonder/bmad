import { useEffect, useState } from "react"
import { websocketService } from "@/lib/websocket/websocket-service"

interface ConnectionStatus {
  connected: boolean
  reconnecting: boolean
  error?: string
  lastConnected?: Date
}

export function useWebSocketConnection() {
  const [status, setStatus] = useState<ConnectionStatus>({
    connected: false,
    reconnecting: false
  })

  useEffect(() => {
    // Get initial status
    const initialStatus = websocketService.getConnectionStatus()
    setStatus(initialStatus)

    // Subscribe to status changes
    const unsubscribe = websocketService.onStatusChange((newStatus) => {
      setStatus(newStatus)
    })

    // Enable auto-connect when component mounts
    websocketService.enableAutoConnect()

    // Cleanup on unmount
    return () => {
      unsubscribe()
      // Don't disconnect on unmount since other components might need it
    }
  }, [])

  const reconnect = () => {
    websocketService.disconnect()
    setTimeout(() => {
      websocketService.enableAutoConnect()
    }, 1000)
  }

  return {
    status,
    reconnect,
    isConnected: status.connected,
    isReconnecting: status.reconnecting,
    hasError: !!status.error
  }
}

export default useWebSocketConnection
