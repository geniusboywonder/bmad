"use client"

import { useState, useEffect, useCallback, useRef, useMemo } from "react"
import { websocketService } from "@/lib/services/websocket/websocket-service"
import { useAgentStore } from "@/lib/stores/agent-store"
import { useLogStore } from "@/lib/stores/log-store"

export interface ServiceStatus {
  name: string
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
  responseTime?: number
  lastCheck: Date
  uptime?: number
  details?: string
  endpoint?: string
}

export interface SystemHealth {
  overall: 'healthy' | 'degraded' | 'unhealthy' | 'unknown'
  services: ServiceStatus[]
  metrics: {
    totalServices: number
    healthyServices: number
    degradedServices: number
    unhealthyServices: number
    averageResponseTime: number
    systemUptime: number
    errorRate: number
  }
  lastUpdate: Date
}

export interface UseSystemHealthOptions {
  refreshInterval?: number
  autoStart?: boolean
  services?: string[]
  includeAgentHealth?: boolean
  includeLogHealth?: boolean
}

export function useSystemHealth({
  refreshInterval = 30000, // 30 seconds
  autoStart = true,
  services: servicesProp = ['backend', 'websocket', 'agents'],
  includeAgentHealth = true,
  includeLogHealth = true
}: UseSystemHealthOptions = {}) {
  const services = useMemo(() => servicesProp, [JSON.stringify(servicesProp)]);
  const [health, setHealth] = useState<SystemHealth>({
    overall: 'unknown',
    services: [],
    metrics: {
      totalServices: 0,
      healthyServices: 0,
      degradedServices: 0,
      unhealthyServices: 0,
      averageResponseTime: 0,
      systemUptime: 0,
      errorRate: 0
    },
    lastUpdate: new Date()
  })
  
  const [isChecking, setIsChecking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isMonitoring, setIsMonitoring] = useState(autoStart)

  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const { getSystemHealth: getAgentHealth } = useAgentStore()
  const { getErrorLogs, getRecentLogs, metrics: logMetrics } = useLogStore()

  // Backend health check
  const checkBackendHealth = useCallback(async (startTime: number): Promise<ServiceStatus> => {
    try {
      const response = await fetch('/api/health', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      
      const responseTime = Date.now() - startTime
      
      if (response.ok) {
        const data = await response.json()
        return {
          name: 'Backend API',
          status: responseTime < 1000 ? 'healthy' : 'degraded',
          responseTime,
          lastCheck: new Date(),
          details: `HTTP ${response.status} - ${data.status || 'OK'}`,
          endpoint: '/api/health'
        }
      } else {
        return {
          name: 'Backend API',
          status: 'unhealthy',
          responseTime,
          lastCheck: new Date(),
          details: `HTTP ${response.status} - ${response.statusText}`,
          endpoint: '/api/health'
        }
      }
    } catch (error) {
      return {
        name: 'Backend API',
        status: 'unhealthy',
        lastCheck: new Date(),
        responseTime: Date.now() - startTime,
        details: 'Connection failed',
        endpoint: '/api/health'
      }
    }
  }, []);

  // WebSocket health check
  const checkWebSocketHealth = useCallback((): ServiceStatus => {
    try {
      const connectionStatus = websocketService.getConnectionStatus()
      const wsMetrics = websocketService.getMetrics ? websocketService.getMetrics() : {}
      
      let status: ServiceStatus['status'] = 'unknown'
      let details = 'Unknown connection state'
      
      switch (connectionStatus) {
        case 'connected':
          status = 'healthy'
          details = 'Real-time connection active'
          break
        case 'connecting':
          status = 'degraded'
          details = 'Attempting to connect'
          break
        case 'disconnected':
          status = 'unhealthy'
          details = 'Disconnected from server'
          break
        default:
          status = 'unknown'
          details = 'Unknown connection state'
      }
      
      return {
        name: 'WebSocket',
        status,
        lastCheck: new Date(),
        responseTime: wsMetrics.latency,
        details,
        uptime: wsMetrics.uptime
      }
    } catch (error) {
      return {
        name: 'WebSocket',
        status: 'unhealthy',
        lastCheck: new Date(),
        details: 'WebSocket service error'
      }
    }
  }, []);

  // Agents health check
  const checkAgentsHealth = useCallback((): ServiceStatus => {
    if (!includeAgentHealth) {
      return {
        name: 'Agents',
        status: 'unknown',
        lastCheck: new Date(),
        details: 'Agent health monitoring disabled'
      }
    }

    try {
      const agents = useAgentStore.getState().agents
      const agentHealth = getAgentHealth()
      const errorAgents = agents.filter(agent => agent.status === 'error').length
      const activeAgents = agents.filter(agent => agent.status === 'active' || agent.status === 'idle').length
      
      let status: ServiceStatus['status']
      if (agentHealth.percentage >= 80) {
        status = 'healthy'
      } else if (agentHealth.percentage >= 60) {
        status = 'degraded'
      } else {
        status = 'unhealthy'
      }
      
      return {
        name: 'Agents',
        status,
        lastCheck: new Date(),
        details: `${activeAgents}/${agentHealth.total} agents healthy, ${errorAgents} errors`,
        uptime: agentHealth.percentage
      }
    } catch (error) {
      return {
        name: 'Agents',
        status: 'unhealthy',
        lastCheck: new Date(),
        details: 'Agent health check failed'
      }
    }
  }, [includeAgentHealth, getAgentHealth]);

  // Database health check (if applicable)
  const checkDatabaseHealth = useCallback(async (startTime: number): Promise<ServiceStatus> => {
    try {
      const response = await fetch('/api/db/health')
      const responseTime = Date.now() - startTime
      
      if (response.ok) {
        const data = await response.json()
        return {
          name: 'Database',
          status: data.status === 'healthy' ? 'healthy' : 'degraded',
          responseTime,
          lastCheck: new Date(),
          details: data.details || 'Database operational',
          endpoint: '/api/db/health'
        }
      } else {
        return {
          name: 'Database',
          status: 'unhealthy',
          responseTime,
          lastCheck: new Date(),
          details: 'Database connection failed',
          endpoint: '/api/db/health'
        }
      }
    } catch (error) {
      return {
        name: 'Database',
        status: 'unknown',
        lastCheck: new Date(),
        responseTime: Date.now() - startTime,
        details: 'Database health endpoint not available'
      }
    }
  }, []);

  // API health check
  const checkAPIHealth = useCallback(async (startTime: number): Promise<ServiceStatus> => {
    try {
      const response = await fetch('/api/status')
      const responseTime = Date.now() - startTime
      
      if (response.ok) {
        return {
          name: 'API',
          status: responseTime < 500 ? 'healthy' : 'degraded',
          responseTime,
          lastCheck: new Date(),
          details: 'API endpoints responding',
          endpoint: '/api/status'
        }
      } else {
        return {
          name: 'API',
          status: 'unhealthy',
          responseTime,
          lastCheck: new Date(),
          details: `API error: ${response.status}`,
          endpoint: '/api/status'
        }
      }
    } catch (error) {
      return {
        name: 'API',
        status: 'unhealthy',
        lastCheck: new Date(),
        responseTime: Date.now() - startTime,
        details: 'API connection failed'
      }
    }
  }, []);

  // Generic service health check
  const checkGenericService = useCallback(async (serviceName: string, startTime: number): Promise<ServiceStatus> => {
    const endpoint = `/api/services/${serviceName}/health`
    
    try {
      const response = await fetch(endpoint)
      const responseTime = Date.now() - startTime
      
      if (response.ok) {
        const data = await response.json()
        return {
          name: serviceName,
          status: data.status || 'healthy',
          responseTime,
          lastCheck: new Date(),
          details: data.details || 'Service operational',
          endpoint
        }
      } else {
        return {
          name: serviceName,
          status: 'unhealthy',
          responseTime,
          lastCheck: new Date(),
          details: `Service error: ${response.status}`,
          endpoint
        }
      }
    } catch (error) {
      return {
        name: serviceName,
        status: 'unknown',
        lastCheck: new Date(),
        responseTime: Date.now() - startTime,
        details: 'Service endpoint not available',
        endpoint
      }
    }
  }, []);

  // Check individual service health
  const checkServiceHealth = useCallback(async (serviceName: string): Promise<ServiceStatus> => {
    const startTime = Date.now()

    try {
      switch (serviceName) {
        case 'backend':
          return await checkBackendHealth(startTime)
        case 'websocket':
          return checkWebSocketHealth()
        case 'agents':
          return checkAgentsHealth()
        case 'database':
          return await checkDatabaseHealth(startTime)
        case 'api':
          return await checkAPIHealth(startTime)
        default:
          return await checkGenericService(serviceName, startTime)
      }
    } catch (error) {
      return {
        name: serviceName,
        status: 'unhealthy',
        lastCheck: new Date(),
        responseTime: Date.now() - startTime,
        details: error instanceof Error ? error.message : 'Service check failed'
      }
    }
  }, [checkBackendHealth, checkWebSocketHealth, checkAgentsHealth, checkDatabaseHealth, checkAPIHealth, checkGenericService]);

  // Calculate overall health metrics
  const calculateHealthMetrics = useCallback((serviceStatuses: ServiceStatus[]) => {
    const totalServices = serviceStatuses.length
    const healthyServices = serviceStatuses.filter(s => s.status === 'healthy').length
    const degradedServices = serviceStatuses.filter(s => s.status === 'degraded').length
    const unhealthyServices = serviceStatuses.filter(s => s.status === 'unhealthy').length
    
    const responseTimes = serviceStatuses
      .filter(s => s.responseTime !== undefined)
      .map(s => s.responseTime!)
    const averageResponseTime = responseTimes.length > 0 
      ? responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length 
      : 0
    
    // Calculate system uptime (average of all service uptimes)
    const uptimes = serviceStatuses
      .filter(s => s.uptime !== undefined)
      .map(s => s.uptime!)
    const systemUptime = uptimes.length > 0 
      ? uptimes.reduce((sum, uptime) => sum + uptime, 0) / uptimes.length 
      : 100
    
    // Calculate error rate from logs if enabled
    let errorRate = 0
    if (includeLogHealth) {
      const recentLogs = getRecentLogs(60) // Last hour
      const errorLogs = recentLogs.filter(log => log.level === 'error')
      errorRate = recentLogs.length > 0 ? (errorLogs.length / recentLogs.length) * 100 : 0
    }
    
    // Determine overall status
    let overall: SystemHealth['overall'] = 'healthy'
    if (unhealthyServices > 0 || errorRate > 10) {
      overall = 'unhealthy'
    } else if (degradedServices > 0 || errorRate > 5) {
      overall = 'degraded'
    } else if (totalServices === 0) {
      overall = 'unknown'
    }
    
    return {
      totalServices,
      healthyServices,
      degradedServices,
      unhealthyServices,
      averageResponseTime,
      systemUptime,
      errorRate,
      overall
    }
  }, [includeLogHealth, getRecentLogs])

  // Perform health check
  const performHealthCheck = useCallback(async () => {
    if (!isMonitoring) return

    setIsChecking(true)
    setError(null)

    try {
      // Check all configured services
      const serviceChecks = await Promise.allSettled(
        services.map(service => checkServiceHealth(service))
      )
      
      const serviceStatuses: ServiceStatus[] = serviceChecks.map((result, index) => {
        if (result.status === 'fulfilled') {
          return result.value
        } else {
          return {
            name: services[index],
            status: 'unhealthy',
            lastCheck: new Date(),
            details: 'Health check failed'
          }
        }
      })
      
      const metrics = calculateHealthMetrics(serviceStatuses)
      
      setHealth({
        overall: metrics.overall,
        services: serviceStatuses,
        metrics: {
          totalServices: metrics.totalServices,
          healthyServices: metrics.healthyServices,
          degradedServices: metrics.degradedServices,
          unhealthyServices: metrics.unhealthyServices,
          averageResponseTime: metrics.averageResponseTime,
          systemUptime: metrics.systemUptime,
          errorRate: metrics.errorRate
        },
        lastUpdate: new Date()
      })

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Health check failed')
      console.error('System health check error:', err)
    } finally {
      setIsChecking(false)
    }
  }, [isMonitoring, services, checkServiceHealth, calculateHealthMetrics])

  // Control functions
  const startMonitoring = useCallback(() => {
    if (intervalRef.current) return
    
    setIsMonitoring(true)
    performHealthCheck() // Immediate check
    intervalRef.current = setInterval(performHealthCheck, refreshInterval)
  }, [performHealthCheck, refreshInterval])

  const stopMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setIsMonitoring(false)
  }, [])

  const forceHealthCheck = useCallback(() => {
    performHealthCheck()
  }, [performHealthCheck])

  // Lifecycle management
  useEffect(() => {
    if (autoStart) {
      startMonitoring()
    }

    return () => {
      stopMonitoring()
    }
  }, [autoStart, startMonitoring, stopMonitoring])

  // Export health data
  const exportHealthData = useCallback((format: 'json' | 'csv' = 'json') => {
    if (format === 'json') {
      return JSON.stringify({
        health,
        exportDate: new Date(),
        configuration: {
          refreshInterval,
          services,
          includeAgentHealth,
          includeLogHealth
        }
      }, null, 2)
    }
    
    // CSV format
    const headers = ['service', 'status', 'responseTime', 'lastCheck', 'details']
    const rows = [headers.join(',')]
    
    health.services.forEach(service => {
      const row = [
        service.name,
        service.status,
        service.responseTime || '',
        service.lastCheck.toISOString(),
        `"${(service.details || '').replace(/"/g, '""')}"`
      ]
      rows.push(row.join(','))
    })
    
    return rows.join('\n')
  }, [health, refreshInterval, services, includeAgentHealth, includeLogHealth])

  return {
    // Current state
    health,
    isChecking,
    isMonitoring,
    error,
    
    // Controls
    startMonitoring,
    stopMonitoring,
    forceHealthCheck,
    
    // Export
    exportHealthData,
    
    // Computed values
    isHealthy: health.overall === 'healthy',
    hasIssues: health.overall === 'degraded' || health.overall === 'unhealthy',
    criticalIssues: health.services.filter(s => s.status === 'unhealthy'),
    warnings: health.services.filter(s => s.status === 'degraded'),
    
    // Quick stats
    healthPercentage: health.metrics.totalServices > 0 
      ? (health.metrics.healthyServices / health.metrics.totalServices) * 100 
      : 0,
    averageResponseTime: health.metrics.averageResponseTime,
    systemUptime: health.metrics.systemUptime,
    lastUpdate: health.lastUpdate
  }
}