"use client"

import { useState, useEffect } from "react"
import { Wifi, Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import { websocketService } from "@/lib/websocket/websocket-service"

interface ServiceStatus {
  name: string
  status: 'connected' | 'disconnected' | 'connecting'
}

const getStatusColor = (status: ServiceStatus['status']) => {
  switch (status) {
    case 'connected':
      return 'text-green-600'
    case 'connecting':
      return 'text-yellow-600'
    case 'disconnected':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

export function ServicesStatus() {
  const [wsStatus, setWsStatus] = useState<ServiceStatus['status']>('disconnected')
  const [llmStatus, setLlmStatus] = useState<ServiceStatus['status']>('connected') // Placeholder

  useEffect(() => {
    const checkWsConnection = () => {
      try {
        const status = websocketService.getConnectionStatus()
        setWsStatus(status.connected ? 'connected' : status.reconnecting ? 'connecting' : 'disconnected')
      } catch (error) {
        setWsStatus('disconnected')
      }
    }

    checkWsConnection()
    const interval = setInterval(checkWsConnection, 2000)
    return () => clearInterval(interval)
  }, [])

  // TODO: Implement a real LLM status check
  useEffect(() => {
    // This is a placeholder for LLM status
    setLlmStatus('connected')
  }, [])

  return (
    <div className="space-y-1 text-xs text-muted-foreground">
      <div className="font-semibold">Services</div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wifi className={cn("w-3 h-3", getStatusColor(wsStatus))} />
          <span>WebSocket</span>
        </div>
        <span className={cn("font-semibold", getStatusColor(wsStatus))}>
          {wsStatus.charAt(0).toUpperCase() + wsStatus.slice(1)}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className={cn("w-3 h-3", getStatusColor(llmStatus))} />
          <span>LLMs</span>
        </div>
        <span className={cn("font-semibold", getStatusColor(llmStatus))}>
          {llmStatus.charAt(0).toUpperCase() + llmStatus.slice(1)}
        </span>
      </div>
    </div>
  )
}
