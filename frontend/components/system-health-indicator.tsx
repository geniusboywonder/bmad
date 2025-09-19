"use client"

import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { Activity, Wifi, WifiOff, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"
import { getStatusBadgeClasses } from "@/lib/utils/badge-utils"

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'healthy':
      return <Wifi className="w-3 h-3 text-tester" />
    case 'degraded':
      return <AlertTriangle className="w-3 h-3 text-amber" />
    case 'unhealthy':
      return <WifiOff className="w-3 h-3 text-destructive" />
    default:
      return <Activity className="w-3 h-3 text-muted-foreground" />
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'healthy': return 'Healthy'
    case 'degraded': return 'Degraded' 
    case 'unhealthy': return 'Offline'
    default: return 'Unknown'
  }
}

export function SystemHealthIndicator() {
  const [status, setStatus] = useState('unknown')
  const [lastUpdated, setLastUpdated] = useState("")
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // In a real app, this would fetch from a health endpoint
    setStatus('healthy')
    setLastUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
  }, [])

  if (!mounted) {
    return (
      <div className="text-xs text-muted-foreground">
        System Health: <span className="font-semibold">Loading...</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <Badge 
        variant="muted" 
        size="sm" 
        className={cn(
          "flex items-center gap-1.5 px-2 py-1",
          getStatusBadgeClasses(status === 'healthy' ? 'completed' : status === 'degraded' ? 'waiting' : 'error')
        )}
      >
        {getStatusIcon(status)}
        <span className="font-medium">{getStatusText(status)}</span>
      </Badge>
      <span className="text-xs text-muted-foreground">
        {lastUpdated}
      </span>
    </div>
  )
}
