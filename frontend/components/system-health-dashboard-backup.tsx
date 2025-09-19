"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
import { 
  Activity, 
  Server, 
  Wifi, 
  WifiOff, 
  Database, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
<<<<<<< HEAD
=======
import {
  Activity,
  Server,
  Wifi,
  WifiOff,
  Database,
  Zap,
  AlertTriangle,
  CheckCircle,
>>>>>>> origin/feature/add-test-framework
=======
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
  Clock,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus
} from "lucide-react"
import { websocketService } from "@/lib/websocket/websocket-service"
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
<<<<<<< HEAD
<<<<<<< HEAD
  
=======

>>>>>>> origin/feature/add-test-framework
=======
  
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
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
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [connectionStatus, setConnectionStatus] = useState('disconnected')

  // Check WebSocket connection status
  useEffect(() => {
    const checkConnection = () => {
      try {
        const status = websocketService.getConnectionStatus()
        setConnectionStatus(status)
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
      // Check backend health
      const backendHealth = await checkBackendHealth()
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
      
      // Check WebSocket service
      const wsHealth = checkWebSocketHealth()
      
      // Check agent services
      const agentHealth = await checkAgentServices()
      
      // Combine all service statuses
      setServices([backendHealth, wsHealth, ...agentHealth])
      
      // Get system metrics
      const systemMetrics = await fetchSystemMetrics()
      setMetrics(systemMetrics)
      
<<<<<<< HEAD
=======

      // Check WebSocket service
      const wsHealth = checkWebSocketHealth()

      // Check agent services
      const agentHealth = await checkAgentServices()

      // Combine all service statuses
      setServices([backendHealth, wsHealth, ...agentHealth])

      // Get system metrics
      const systemMetrics = await fetchSystemMetrics()
      setMetrics(systemMetrics)

>>>>>>> origin/feature/add-test-framework
=======
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Failed to fetch health data:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const checkBackendHealth = async (): Promise<ServiceStatus> => {
    try {
      const startTime = Date.now()
      const response = await fetch('/api/health')
      const responseTime = Date.now() - startTime
<<<<<<< HEAD
<<<<<<< HEAD
      
=======

>>>>>>> origin/feature/add-test-framework
=======
      
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
      if (response.ok) {
        const data = await response.json()
        return {
          name: 'Backend API',
          status: responseTime < 1000 ? 'healthy' : 'degraded',
          responseTime,
          lastCheck: new Date(),
          details: `HTTP ${response.status}`
        }
      } else {
        return {
          name: 'Backend API',
          status: 'unhealthy',
          responseTime: Date.now() - startTime,
          lastCheck: new Date(),
          details: `HTTP ${response.status}`
        }
      }
    } catch (error) {
      return {
        name: 'Backend API',
        status: 'unhealthy',
        lastCheck: new Date(),
        details: 'Connection failed'
      }
    }
  }

  const checkWebSocketHealth = (): ServiceStatus => {
<<<<<<< HEAD
<<<<<<< HEAD
    const status = connectionStatus === 'connected' ? 'healthy' : 
                  connectionStatus === 'connecting' ? 'degraded' : 'unhealthy'
    
=======
    const status = connectionStatus === 'connected' ? 'healthy' :
                  connectionStatus === 'connecting' ? 'degraded' : 'unhealthy'

>>>>>>> origin/feature/add-test-framework
=======
    const status = connectionStatus === 'connected' ? 'healthy' : 
                  connectionStatus === 'connecting' ? 'degraded' : 'unhealthy'
    
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
    return {
      name: 'WebSocket',
      status,
      lastCheck: new Date(),
<<<<<<< HEAD
<<<<<<< HEAD
      details: connectionStatus === 'connected' ? 'Real-time connection active' : 
=======
      details: connectionStatus === 'connected' ? 'Real-time connection active' :
>>>>>>> origin/feature/add-test-framework
=======
      details: connectionStatus === 'connected' ? 'Real-time connection active' : 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
               connectionStatus === 'connecting' ? 'Attempting to connect' : 'Disconnected'
    }
  }

  const checkAgentServices = async (): Promise<ServiceStatus[]> => {
    try {
      const response = await fetch('/api/agents/status')
      if (response.ok) {
        const data = await response.json()
        return data.agents?.map((agent: any) => ({
          name: `${agent.name} Agent`,
<<<<<<< HEAD
<<<<<<< HEAD
          status: agent.status === 'active' ? 'healthy' : 
=======
          status: agent.status === 'active' ? 'healthy' :
>>>>>>> origin/feature/add-test-framework
=======
          status: agent.status === 'active' ? 'healthy' : 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
                  agent.status === 'idle' ? 'degraded' : 'unhealthy',
          lastCheck: new Date(),
          details: `Status: ${agent.status}`,
          uptime: agent.uptime
        })) || []
      }
    } catch (error) {
      console.log('Agent status not available')
    }
<<<<<<< HEAD
<<<<<<< HEAD
    
=======

>>>>>>> origin/feature/add-test-framework
=======
    
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
    // Return default agent statuses if API not available
    return [
      {
        name: 'Analyst Agent',
        status: 'unknown',
        lastCheck: new Date(),
        details: 'Status unknown'
      },
      {
<<<<<<< HEAD
<<<<<<< HEAD
        name: 'Architect Agent', 
=======
        name: 'Architect Agent',
>>>>>>> origin/feature/add-test-framework
=======
        name: 'Architect Agent', 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
        status: 'unknown',
        lastCheck: new Date(),
        details: 'Status unknown'
      },
      {
        name: 'Developer Agent',
<<<<<<< HEAD
<<<<<<< HEAD
        status: 'unknown', 
=======
        status: 'unknown',
>>>>>>> origin/feature/add-test-framework
=======
        status: 'unknown', 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
        lastCheck: new Date(),
        details: 'Status unknown'
      }
    ]
  }

  const fetchSystemMetrics = async (): Promise<SystemMetrics> => {
    try {
      const response = await fetch('/api/metrics')
      if (response.ok) {
        return await response.json()
      }
    } catch (error) {
      console.log('System metrics not available')
    }
<<<<<<< HEAD
<<<<<<< HEAD
    
=======

>>>>>>> origin/feature/add-test-framework
=======
    
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
    // Return mock metrics if API not available
    return {
      cpu: Math.random() * 50 + 10,
      memory: Math.random() * 60 + 20,
      connections: Math.floor(Math.random() * 10) + 1,
      throughput: Math.random() * 100,
      errorRate: Math.random() * 5
    }
  }

  // Auto-refresh every 30 seconds
  useEffect(() => {
    fetchHealthData()
    const interval = setInterval(fetchHealthData, 30000)
    return () => clearInterval(interval)
  }, [])

<<<<<<< HEAD
<<<<<<< HEAD
  const overallStatus = services.length > 0 ? 
=======
  const overallStatus = services.length > 0 ?
>>>>>>> origin/feature/add-test-framework
=======
  const overallStatus = services.length > 0 ? 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
    services.every(s => s.status === 'healthy') ? 'healthy' :
    services.some(s => s.status === 'unhealthy') ? 'unhealthy' : 'degraded'
    : 'unknown'

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
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
<<<<<<< HEAD
<<<<<<< HEAD
            <Button 
              variant="outline" 
              size="sm" 
=======
            <Button
              variant="outline"
              size="sm"
>>>>>>> origin/feature/add-test-framework
=======
            <Button 
              variant="outline" 
              size="sm" 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
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
<<<<<<< HEAD
<<<<<<< HEAD
            {connectionStatus === 'connected' ? 
              <Wifi className="w-4 h-4 text-green-600" /> : 
=======
            {connectionStatus === 'connected' ?
              <Wifi className="w-4 h-4 text-green-600" /> :
>>>>>>> origin/feature/add-test-framework
=======
            {connectionStatus === 'connected' ? 
              <Wifi className="w-4 h-4 text-green-600" /> : 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
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
<<<<<<< HEAD
<<<<<<< HEAD
              {connectionStatus === 'connected' ? 
=======
              {connectionStatus === 'connected' ?
>>>>>>> origin/feature/add-test-framework
=======
              {connectionStatus === 'connected' ? 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
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
<<<<<<< HEAD
<<<<<<< HEAD
            
=======

>>>>>>> origin/feature/add-test-framework
=======
            
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
            {metrics.memory !== undefined && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Memory Usage</span>
                  <span>{Math.round(metrics.memory)}%</span>
                </div>
                <Progress value={metrics.memory} className="h-2" />
              </div>
            )}
<<<<<<< HEAD
<<<<<<< HEAD
            
=======

>>>>>>> origin/feature/add-test-framework
=======
            
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
            {metrics.connections !== undefined && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Active Connections</span>
                  <span>{metrics.connections}</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full">
<<<<<<< HEAD
<<<<<<< HEAD
                  <div 
=======
                  <div
>>>>>>> origin/feature/add-test-framework
=======
                  <div 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
                    className="h-2 bg-blue-600 rounded-full"
                    style={{ width: `${Math.min(metrics.connections * 10, 100)}%` }}
                  />
                </div>
              </div>
            )}
<<<<<<< HEAD
<<<<<<< HEAD
            
=======

>>>>>>> origin/feature/add-test-framework
=======
            
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
            {metrics.throughput !== undefined && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Throughput</span>
                  <span>{Math.round(metrics.throughput)} req/min</span>
                </div>
                <div className="flex items-center gap-1">
                  <TrendingUp className="w-3 h-3 text-green-600" />
                  <span className="text-xs text-green-600">Normal</span>
                </div>
              </div>
            )}
<<<<<<< HEAD
<<<<<<< HEAD
            
=======

>>>>>>> origin/feature/add-test-framework
=======
            
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
            {metrics.errorRate !== undefined && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Error Rate</span>
                  <span>{metrics.errorRate.toFixed(1)}%</span>
                </div>
                <div className="flex items-center gap-1">
                  {metrics.errorRate < 5 ? (
                    <CheckCircle className="w-3 h-3 text-green-600" />
                  ) : (
                    <TrendingDown className="w-3 h-3 text-red-600" />
                  )}
                  <span className={cn(
                    "text-xs",
                    metrics.errorRate < 5 ? "text-green-600" : "text-red-600"
                  )}>
                    {metrics.errorRate < 5 ? "Low" : "High"}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-2 pt-2">
<<<<<<< HEAD
<<<<<<< HEAD
          <Button 
            variant="outline" 
            size="sm" 
=======
          <Button
            variant="outline"
            size="sm"
>>>>>>> origin/feature/add-test-framework
=======
          <Button 
            variant="outline" 
            size="sm" 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
            onClick={() => window.open('/api/health', '_blank')}
          >
            <Database className="w-4 h-4 mr-2" />
            View Raw Health
          </Button>
<<<<<<< HEAD
<<<<<<< HEAD
          <Button 
            variant="outline" 
            size="sm" 
=======
          <Button
            variant="outline"
            size="sm"
>>>>>>> origin/feature/add-test-framework
=======
          <Button 
            variant="outline" 
            size="sm" 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
            onClick={fetchHealthData}
            disabled={isRefreshing}
          >
            <Zap className="w-4 h-4 mr-2" />
            Force Refresh
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}