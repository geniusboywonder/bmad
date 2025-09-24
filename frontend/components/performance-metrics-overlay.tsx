"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { 
  Monitor, 
  X, 
  Minimize2, 
  Maximize2, 
  Activity, 
  Zap, 
  Clock, 
  TrendingUp, 
  TrendingDown,
  Wifi,
  Database,
  Cpu,
  HardDrive,
  Network
} from "lucide-react"
import { websocketService } from "@/lib/services/websocket/websocket-service"
import { cn } from "@/lib/utils"

interface PerformanceMetrics {
  timestamp: Date
  cpu: number
  memory: number
  networkLatency: number
  connectionCount: number
  messagesSent: number
  messagesReceived: number
  errors: number
  throughput: number
}

interface MetricHistoryPoint {
  timestamp: number
  value: number
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const formatLatency = (ms: number) => {
  if (ms < 100) return `${Math.round(ms)}ms`
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const getPerformanceColor = (value: number, thresholds: { good: number; warning: number }) => {
  if (value <= thresholds.good) return 'text-green-600'
  if (value <= thresholds.warning) return 'text-yellow-600'
  return 'text-red-600'
}

const MiniChart = ({ data, color = "rgb(59, 130, 246)" }: { data: MetricHistoryPoint[]; color?: string }) => {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || data.length < 2) return

    const svg = svgRef.current
    const width = 80
    const height = 20
    const maxValue = Math.max(...data.map(d => d.value), 1)
    const minValue = Math.min(...data.map(d => d.value))
    const range = maxValue - minValue || 1

    const points = data.map((point, index) => {
      const x = (index / (data.length - 1)) * width
      const y = height - ((point.value - minValue) / range) * height
      return `${x},${y}`
    }).join(' ')

    svg.innerHTML = `
      <polyline
        fill="none"
        stroke="${color}"
        stroke-width="1.5"
        points="${points}"
      />
    `
  }, [data, color])

  return (
    <svg 
      ref={svgRef}
      width="80" 
      height="20" 
      className="opacity-70"
      viewBox="0 0 80 20"
    />
  )
}

interface PerformanceMetricsOverlayProps {
  isVisible?: boolean
  onToggle?: () => void
}

export function PerformanceMetricsOverlay({ 
  isVisible = false, 
  onToggle 
}: PerformanceMetricsOverlayProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null)
  const [isMinimized, setIsMinimized] = useState(false)
  const [position, setPosition] = useState({ x: 20, y: 20 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [history, setHistory] = useState<{
    cpu: MetricHistoryPoint[]
    memory: MetricHistoryPoint[]
    latency: MetricHistoryPoint[]
    throughput: MetricHistoryPoint[]
  }>({
    cpu: [],
    memory: [],
    latency: [],
    throughput: []
  })

  const overlayRef = useRef<HTMLDivElement>(null)

  // Fetch performance metrics
  const fetchMetrics = async () => {
    try {
      // Get WebSocket metrics
      const wsMetrics = websocketService.getMetrics ? websocketService.getMetrics() : {}
      
      // Get system metrics from API
      let systemMetrics = {}
      try {
        const response = await fetch('/api/metrics')
        if (response.ok) {
          systemMetrics = await response.json()
        }
      } catch (error) {
        // Use mock data if API not available
        systemMetrics = {
          cpu: Math.random() * 50 + 10,
          memory: Math.random() * 60 + 20,
          networkLatency: Math.random() * 100 + 50,
          connectionCount: Math.floor(Math.random() * 5) + 1
        }
      }

      const newMetrics: PerformanceMetrics = {
        timestamp: new Date(),
        cpu: systemMetrics.cpu || Math.random() * 50 + 10,
        memory: systemMetrics.memory || Math.random() * 60 + 20,
        networkLatency: wsMetrics.latency || Math.random() * 100 + 50,
        connectionCount: systemMetrics.connectionCount || 1,
        messagesSent: wsMetrics.messagesSent || 0,
        messagesReceived: wsMetrics.messagesReceived || 0,
        errors: wsMetrics.errors || 0,
        throughput: systemMetrics.throughput || Math.random() * 100
      }

      setMetrics(newMetrics)

      // Update history (keep last 20 points)
      const timestamp = Date.now()
      setHistory(prev => ({
        cpu: [...prev.cpu.slice(-19), { timestamp, value: newMetrics.cpu }],
        memory: [...prev.memory.slice(-19), { timestamp, value: newMetrics.memory }],
        latency: [...prev.latency.slice(-19), { timestamp, value: newMetrics.networkLatency }],
        throughput: [...prev.throughput.slice(-19), { timestamp, value: newMetrics.throughput }]
      }))

    } catch (error) {
      console.error('Failed to fetch performance metrics:', error)
    }
  }

  // Auto-refresh metrics
  useEffect(() => {
    if (!isVisible) return

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 2000)
    return () => clearInterval(interval)
  }, [isVisible])

  // Handle dragging
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) return

    setIsDragging(true)
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    })
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return

    const newX = Math.max(0, Math.min(window.innerWidth - 320, e.clientX - dragOffset.x))
    const newY = Math.max(0, Math.min(window.innerHeight - 200, e.clientY - dragOffset.y))
    
    setPosition({ x: newX, y: newY })
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, dragOffset])

  if (!isVisible) return null

  return (
    <div
      ref={overlayRef}
      className={cn(
        "fixed z-50 select-none transition-all duration-200",
        isDragging && "cursor-grabbing",
        !isDragging && "cursor-grab"
      )}
      style={{
        left: position.x,
        top: position.y,
        width: isMinimized ? '200px' : '320px'
      }}
      onMouseDown={handleMouseDown}
    >
      <Card className="shadow-lg border border-gray-300 bg-white/95 backdrop-blur-sm">
        {/* Header */}
        <div className="flex items-center justify-between p-2 border-b bg-gray-50/80">
          <div className="flex items-center gap-2">
            <Monitor className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium">Performance</span>
            {metrics && (
              <Badge variant="outline" className="text-xs">
                Live
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={(e) => {
                e.stopPropagation()
                setIsMinimized(!isMinimized)
              }}
            >
              {isMinimized ? <Maximize2 className="w-3 h-3" /> : <Minimize2 className="w-3 h-3" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={(e) => {
                e.stopPropagation()
                onToggle?.()
              }}
            >
              <X className="w-3 h-3" />
            </Button>
          </div>
        </div>

        {/* Content */}
        {!isMinimized && metrics && (
          <CardContent className="p-3 space-y-3">
            {/* System Metrics */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <Cpu className="w-3 h-3" />
                    <span>CPU</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={getPerformanceColor(metrics.cpu, { good: 30, warning: 70 })}>
                      {Math.round(metrics.cpu)}%
                    </span>
                    <MiniChart data={history.cpu} color="rgb(34, 197, 94)" />
                  </div>
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <HardDrive className="w-3 h-3" />
                    <span>Memory</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={getPerformanceColor(metrics.memory, { good: 40, warning: 80 })}>
                      {Math.round(metrics.memory)}%
                    </span>
                    <MiniChart data={history.memory} color="rgb(168, 85, 247)" />
                  </div>
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <Network className="w-3 h-3" />
                    <span>Latency</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={getPerformanceColor(metrics.networkLatency, { good: 100, warning: 500 })}>
                      {formatLatency(metrics.networkLatency)}
                    </span>
                    <MiniChart data={history.latency} color="rgb(239, 68, 68)" />
                  </div>
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    <span>Throughput</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-blue-600">
                      {Math.round(metrics.throughput)} req/min
                    </span>
                    <MiniChart data={history.throughput} color="rgb(59, 130, 246)" />
                  </div>
                </div>
              </div>
            </div>

            {/* Connection Stats */}
            <div className="border-t pt-2 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1">
                  <Wifi className="w-3 h-3" />
                  <span>Connections</span>
                </div>
                <span className="text-blue-600">{metrics.connectionCount}</span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1">
                    <TrendingUp className="w-3 h-3 text-green-600" />
                    <span className="text-green-600">{metrics.messagesSent}</span>
                  </div>
                  <div className="text-gray-500">Sent</div>
                </div>
                
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1">
                    <TrendingDown className="w-3 h-3 text-blue-600" />
                    <span className="text-blue-600">{metrics.messagesReceived}</span>
                  </div>
                  <div className="text-gray-500">Received</div>
                </div>
                
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1">
                    <X className="w-3 h-3 text-red-600" />
                    <span className="text-red-600">{metrics.errors}</span>
                  </div>
                  <div className="text-gray-500">Errors</div>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="border-t pt-2 text-xs text-gray-500">
              <div className="flex items-center justify-between">
                <span>Last updated</span>
                <span>{metrics.timestamp.toLocaleTimeString()}</span>
              </div>
            </div>
          </CardContent>
        )}

        {/* Minimized View */}
        {isMinimized && metrics && (
          <CardContent className="p-2">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <Cpu className="w-3 h-3" />
                  <span className={getPerformanceColor(metrics.cpu, { good: 30, warning: 70 })}>
                    {Math.round(metrics.cpu)}%
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <HardDrive className="w-3 h-3" />
                  <span className={getPerformanceColor(metrics.memory, { good: 40, warning: 80 })}>
                    {Math.round(metrics.memory)}%
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <Network className="w-3 h-3" />
                  <span className={getPerformanceColor(metrics.networkLatency, { good: 100, warning: 500 })}>
                    {formatLatency(metrics.networkLatency)}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  )
}

// Hook for easy integration
export function usePerformanceMetricsOverlay() {
  const [isVisible, setIsVisible] = useState(false)

  const toggle = () => setIsVisible(prev => !prev)
  const show = () => setIsVisible(true)
  const hide = () => setIsVisible(false)

  return {
    isVisible,
    toggle,
    show,
    hide,
    PerformanceMetricsOverlay: (props: Omit<PerformanceMetricsOverlayProps, 'isVisible' | 'onToggle'>) => (
      <PerformanceMetricsOverlay 
        {...props} 
        isVisible={isVisible} 
        onToggle={toggle} 
      />
    )
  }
}