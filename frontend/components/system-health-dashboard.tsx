"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { 
  Activity, 
  Server, 
  Wifi, 
  WifiOff, 
  Database, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus
} from "lucide-react"
import { websocketService } from "@/lib/services/websocket/websocket-service"
import { cn } from "@/lib/utils"

interface ServiceStatus {
  name: string
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
  responseTime?: number
  lastCheck: Date
  uptime?: number
  details?: string
}

interface SystemMetrics {
  cpu?: number
  memory?: number
  connections?: number
  throughput?: number
  errorRate?: number
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'text-green-600 bg-green-50 border-green-200'
    case 'degraded':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    case 'unhealthy':
      return 'text-red-600 bg-red-50 border-red-200'
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="w-4 h-4 text-green-600" />
    case 'degraded':
      return <AlertTriangle className="w-4 h-4 text-yellow-600" />
    case 'unhealthy':
      return <AlertTriangle className="w-4 h-4 text-red-600" />
    default:
      return <Minus className="w-4 h-4 text-gray-600" />
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'healthy':
      return <Badge variant="default" className="bg-green-100 text-green-800">Healthy</Badge>
    case 'degraded':
      return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Degraded</Badge>
    case 'unhealthy':
      return <Badge variant="destructive">Unhealthy</Badge>
    default:
      return <Badge variant="outline">Unknown</Badge>
  }
}

const formatUptime = (seconds: number) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) return `${days}d ${hours}h ${mins}m`
  if (hours > 0) return `${hours}h ${mins}m`
  return `${mins}m`
}

const formatResponseTime = (ms: number) => {
  if (ms < 100) return `${ms}ms`
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export function SystemHealthDashboard() {
  const [services, setServices] = useState<ServiceStatus[]>([])
  const [metrics, setMetrics] = useState<SystemMetrics>({})
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string>("")
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [mounted, setMounted] = useState(false)

  // Fix hydration issue - only show time after mounting
  useEffect(() => {
    setMounted(true)
    setLastUpdated(new Date().toLocaleTimeString())
  }, [])

  // Check WebSocket connection status
  useEffect(() => {
    const checkConnection = () => {
      try {
        const status = websocketService.getConnectionStatus()
        setConnectionStatus(status.connected ? 'connected' : status.reconnecting ? 'connecting' : 'disconnected')
      } catch (error) {
        setConnectionStatus('disconnected')
      }
    }

    checkConnection()
    const interval = setInterval(checkConnection, 2000)
    return () => clearInterval(interval)
  }, [])

  // Fetch system health data
  const fetchHealthData = async () => {
    setIsRefreshing(true)
    try {
      // Check WebSocket service
      const wsHealth = checkWebSocketHealth()
      
      // Set basic services for now
      setServices([wsHealth])
      
      // Set basic metrics
      setMetrics({
        connections: 1,
        cpu: 25,
        memory: 35
      })
      
      if (mounted) {
        setLastUpdated(new Date().toLocaleTimeString())
      }
    } catch (error) {
      console.error('Failed to fetch health data:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const checkWebSocketHealth = (): ServiceStatus => {
    const status = connectionStatus === 'connected' ? 'healthy' : 
                  connectionStatus === 'connecting' ? 'degraded' : 'unhealthy'
    
    return {
      name: 'WebSocket',
      status,
      lastCheck: new Date(),
      details: connectionStatus === 'connected' ? 'Real-time connection active' : 
               connectionStatus === 'connecting' ? 'Attempting to connect' : 'Disconnected'
    }
  }

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (mounted) {
      fetchHealthData()
      const interval = setInterval(fetchHealthData, 30000)
      return () => clearInterval(interval)
    }
  }, [mounted, connectionStatus])

  const overallStatus = services.length > 0 ? 
    services.every(s => s.status === 'healthy') ? 'healthy' :
    services.some(s => s.status === 'unhealthy') ? 'unhealthy' : 'degraded'
    : 'unknown'

  // Don't render time-dependent content until mounted
  if (!mounted) {
    return (
      <Card className="w-full">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            System Health
            <Badge variant="outline">Loading...</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">Loading system status...</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            System Health
            {getStatusBadge(overallStatus)}
          </CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              Updated {lastUpdated}
            </span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchHealthData}
              disabled={isRefreshing}
            >
              <RefreshCw className={cn("w-4 h-4", isRefreshing && "animate-spin")} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Service Status Grid */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <Server className="w-4 h-4" />
            Services
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {services.map((service, index) => (
              <div
                key={index}
                className={cn(
                  "p-3 rounded-lg border",
                  getStatusColor(service.status)
                )}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(service.status)}
                    <span className="font-medium text-sm">{service.name}</span>
                  </div>
                  {service.responseTime && (
                    <span className="text-xs">
                      {formatResponseTime(service.responseTime)}
                    </span>
                  )}
                </div>
                <p className="text-xs opacity-80">{service.details}</p>
                {service.uptime && (
                  <p className="text-xs opacity-80 mt-1">
                    Uptime: {formatUptime(service.uptime)}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        <Separator />

        {/* Connection Status */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium flex items-center gap-2">
            {connectionStatus === 'connected' ? 
              <Wifi className="w-4 h-4 text-green-600" /> : 
              <WifiOff className="w-4 h-4 text-red-600" />
            }
            Connection Status
          </h4>
          <div className={cn(
            "p-3 rounded-lg border flex items-center justify-between",
            connectionStatus === 'connected' ? 'bg-green-50 border-green-200 text-green-900' :
            connectionStatus === 'connecting' ? 'bg-yellow-50 border-yellow-200 text-yellow-900' :
            'bg-red-50 border-red-200 text-red-900'
          )}>
            <div className="flex items-center gap-2">
              {connectionStatus === 'connected' ? 
                <CheckCircle className="w-4 h-4" /> :
                connectionStatus === 'connecting' ?
                <Clock className="w-4 h-4" /> :
                <AlertTriangle className="w-4 h-4" />
              }
              <span className="font-medium">
                {connectionStatus === 'connected' ? 'Connected' :
                 connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
              </span>
            </div>
            <span className="text-sm">
              Real-time communication {connectionStatus === 'connected' ? 'active' : 'inactive'}
            </span>
          </div>
        </div>

        <Separator />

        {/* System Metrics */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            System Metrics
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {metrics.cpu !== undefined && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>CPU Usage</span>
                  <span>{Math.round(metrics.cpu)}%</span>
                </div>
                <Progress value={metrics.cpu} className="h-2" />
              </div>
            )}
            
            {metrics.memory !== undefined && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Memory Usage</span>
                  <span>{Math.round(metrics.memory)}%</span>
                </div>
                <Progress value={metrics.memory} className="h-2" />
              </div>
            )}
            
            {metrics.connections !== undefined && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Active Connections</span>
                  <span>{metrics.connections}</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full">
                  <div 
                    className="h-2 bg-blue-600 rounded-full"
                    style={{ width: `${Math.min(metrics.connections * 10, 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-2 pt-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchHealthData}
            disabled={isRefreshing}
          >
            <Zap className="w-4 h-4 mr-2" />
            Refresh Status
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
