"use client"

import { useEffect, useState } from "react"
import { websocketService, ConnectionStatus } from "@/lib/services/websocket/websocket-service"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Wifi, WifiOff, RefreshCw, AlertTriangle, CheckCircle, Clock } from "lucide-react"
import { cn } from "@/lib/utils"

interface ConnectionStatusProps {
  className?: string
  showText?: boolean
  showRetryButton?: boolean
  compact?: boolean
}

export function ConnectionStatusIndicator({ 
  className, 
  showText = true, 
  showRetryButton = false,
  compact = false 
}: ConnectionStatusProps) {
  const [status, setStatus] = useState<ConnectionStatus>(websocketService.getConnectionStatus())
  const [isRetrying, setIsRetrying] = useState(false)

  useEffect(() => {
    const unsubscribe = websocketService.onStatusChange((newStatus) => {
      setStatus(newStatus)
      if (newStatus.reconnecting) {
        setIsRetrying(false) // Clear manual retry state when auto-reconnect starts
      }
    })

    // Get initial status
    setStatus(websocketService.getConnectionStatus())

    return unsubscribe
  }, [])

  const handleRetry = async () => {
    setIsRetrying(true)
    try {
      websocketService.enableAutoConnect()
      // Give it a moment to attempt connection
      setTimeout(() => {
        setIsRetrying(false)
      }, 2000)
    } catch (error) {
      console.error("Failed to retry connection:", error)
      setIsRetrying(false)
    }
  }

  const getStatusConfig = () => {
    if (isRetrying) {
      return {
        variant: "secondary" as const,
        icon: RefreshCw,
        text: "Retrying...",
        color: "text-blue-500",
        bgColor: "bg-blue-50",
        title: "Manually retrying connection..."
      }
    }

    if (status.connected) {
      return {
        variant: "default" as const,
        icon: CheckCircle,
        text: "Connected",
        color: "text-green-500",
        bgColor: "bg-green-50",
        title: status.lastConnected 
          ? `Connected since ${status.lastConnected.toLocaleTimeString()}`
          : "WebSocket connected"
      }
    }

    if (status.reconnecting) {
      return {
        variant: "secondary" as const,
        icon: Clock,
        text: "Reconnecting...",
        color: "text-yellow-500",
        bgColor: "bg-yellow-50",
        title: "Attempting to reconnect to server..."
      }
    }

    if (status.error) {
      return {
        variant: "destructive" as const,
        icon: AlertTriangle,
        text: "Connection Error",
        color: "text-red-500",
        bgColor: "bg-red-50",
        title: status.error
      }
    }

    return {
      variant: "secondary" as const,
      icon: WifiOff,
      text: "Disconnected",
      color: "text-gray-500",
      bgColor: "bg-gray-50",
      title: "WebSocket disconnected"
    }
  }

  const config = getStatusConfig()
  const IconComponent = config.icon
  const spinning = status.reconnecting || isRetrying

  if (compact) {
    return (
      <div className={cn("flex items-center gap-1", className)} title={config.title}>
        <IconComponent 
          className={cn(
            "h-4 w-4", 
            config.color,
            spinning && "animate-spin"
          )} 
        />
        {showText && (
          <span className={cn("text-xs font-medium", config.color)}>
            {config.text}
          </span>
        )}
      </div>
    )
  }

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Badge 
        variant={config.variant}
        className={cn(
          "flex items-center gap-1.5 px-2.5 py-1",
          config.bgColor
        )}
        title={config.title}
      >
        <IconComponent 
          className={cn(
            "h-3.5 w-3.5", 
            spinning && "animate-spin"
          )} 
        />
        {showText && (
          <span className="text-xs font-medium">
            {config.text}
          </span>
        )}
      </Badge>

      {showRetryButton && !status.connected && !status.reconnecting && (
        <Button
          variant="outline"
          size="sm"
          onClick={handleRetry}
          disabled={isRetrying}
          className="h-7 px-2 text-xs"
          title={isRetrying ? "Retrying connection..." : "Click to retry connection"}
        >
          {isRetrying ? (
            <>
              <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
              Retrying...
            </>
          ) : (
            <>
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </>
          )}
        </Button>
      )}

      {status.error && (
        <div 
          className="h-4 w-4 text-red-500 cursor-help flex items-center"
          title={status.error}
        >
          <AlertTriangle className="h-4 w-4" />
        </div>
      )}
    </div>
  )
}

// Enhanced connection status with detailed info
export function DetailedConnectionStatus({ className }: { className?: string }) {
  const [status, setStatus] = useState<ConnectionStatus>(websocketService.getConnectionStatus())
  const [debugInfo, setDebugInfo] = useState<any>(null)

  useEffect(() => {
    const unsubscribe = websocketService.onStatusChange(setStatus)
    
    // Update debug info periodically
    const interval = setInterval(() => {
      if (websocketService.getDebugInfo) {
        setDebugInfo(websocketService.getDebugInfo())
      }
    }, 1000)

    return () => {
      unsubscribe()
      clearInterval(interval)
    }
  }, [])

  return (
    <div className={cn("space-y-2 p-3 bg-muted/50 rounded-lg", className)}>
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">WebSocket Connection</h4>
        <ConnectionStatusIndicator compact />
      </div>
      
      <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
        <div>Status: {status.connected ? 'Connected' : 'Disconnected'}</div>
        <div>Reconnecting: {status.reconnecting ? 'Yes' : 'No'}</div>
        
        {status.lastConnected && (
          <div className="col-span-2">
            Last Connected: {status.lastConnected.toLocaleString()}
          </div>
        )}
        
        {debugInfo && (
          <>
            <div>State: {debugInfo.readyState}</div>
            <div>Attempts: {debugInfo.reconnectAttempts}</div>
            <div>Auto-connect: {debugInfo.shouldAutoConnect ? 'Yes' : 'No'}</div>
            <div>Manual disconnect: {debugInfo.isManualDisconnect ? 'Yes' : 'No'}</div>
          </>
        )}
      </div>

      {status.error && (
        <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
          <strong>Error:</strong> {status.error}
        </div>
      )}
    </div>
  )
}

// Legacy export for compatibility
export const ConnectionStatus = ConnectionStatusIndicator

export default ConnectionStatusIndicator
