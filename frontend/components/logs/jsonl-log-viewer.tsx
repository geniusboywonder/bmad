"use client"

import { useEffect, useState } from "react"
import { useLogStore, LogEntry } from "@/lib/stores/log-store"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Download, Search, Filter, RefreshCw, Trash2 } from "lucide-react"

interface JSONLLogViewerProps {
  className?: string
  maxHeight?: string
}

export function JSONLLogViewer({ className, maxHeight = "60vh" }: JSONLLogViewerProps) {
  const { 
    logs, 
    filteredLogs,
    currentFilters,
    setFilters,
    clearFilters,
    clearLogs,
    exportLogs,
    searchLogs,
    metrics
  } = useLogStore()

  const [searchTerm, setSearchTerm] = useState("")
  const [selectedLevel, setSelectedLevel] = useState<string>("all")
  const [selectedAgent, setSelectedAgent] = useState<string>("all")
  const [selectedSource, setSelectedSource] = useState<string>("all")
  const [autoScroll, setAutoScroll] = useState(true)

  // Get unique agents and sources for filtering
  const uniqueAgents = Array.from(new Set(logs.map(log => log.agent)))
  const uniqueSources = Array.from(new Set(logs.map(log => log.source || 'unknown')))

  // Apply filters when they change
  useEffect(() => {
    const filters: any = {}
    
    if (selectedLevel !== "all") filters.level = selectedLevel
    if (selectedAgent !== "all") filters.agent = selectedAgent
    if (selectedSource !== "all") filters.source = selectedSource
    if (searchTerm) filters.searchTerm = searchTerm

    setFilters(filters)
    
    // If no filters are active, make sure we show all logs
    if (Object.keys(filters).length === 0) {
      clearFilters()
    }
  }, [selectedLevel, selectedAgent, selectedSource, searchTerm, setFilters, clearFilters])

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && filteredLogs.length > 0) {
      const scrollArea = document.getElementById("logs-scroll-area")
      if (scrollArea) {
        scrollArea.scrollTop = scrollArea.scrollHeight
      }
    }
  }, [filteredLogs, autoScroll])

  const handleExport = (format: 'json' | 'csv' | 'txt') => {
    const data = exportLogs(format)
    const blob = new Blob([data], { 
      type: format === 'json' ? 'application/json' : format === 'csv' ? 'text/csv' : 'text/plain' 
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `botarmy-logs-${new Date().toISOString().split('T')[0]}.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Helper function to safely get Date object from timestamp
  const getTimestamp = (log: LogEntry): Date => {
    if (log.timestamp instanceof Date) {
      return log.timestamp
    } else if (typeof log.timestamp === 'string') {
      return new Date(log.timestamp)
    } else {
      return new Date() // fallback to current date
    }
  }

  // Helper function to format time safely
  const formatTime = (log: LogEntry): string => {
    try {
      const timestamp = getTimestamp(log)
      return timestamp.toLocaleTimeString()
    } catch (error) {
      console.error('Error formatting timestamp:', error, log.timestamp)
      return 'Invalid time'
    }
  }

  const formatJSONL = (log: LogEntry): string => {
    const timestamp = getTimestamp(log)
    const jsonlEntry = {
      timestamp: timestamp.toISOString(),
      level: log.level,
      agent: log.agent,
      message: log.message,
      task: log.task,
      source: log.source || 'unknown',
      category: log.category,
      duration: log.duration,
      severity: log.severity,
      tags: log.tags,
      correlationId: log.correlationId,
      sessionId: log.sessionId,
      metadata: log.metadata
    }
    return JSON.stringify(jsonlEntry, null, 0)
  }

  const getLevelColor = (level: LogEntry["level"]) => {
    switch (level) {
      case 'error': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      case 'warning': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'info': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'success': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'debug': return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
    }
  }

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'agent': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      case 'system': return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200'
      case 'user': return 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200'
      case 'websocket': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">System Logs (JSONL Format)</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {filteredLogs.length} of {logs.length} logs • 
              Errors: {metrics.errorCount} • 
              Warnings: {metrics.warningCount} • 
              System Health: {Math.round(metrics.systemHealthScore)}%
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setAutoScroll(!autoScroll)}
              className={autoScroll ? "bg-green-50 border-green-200" : ""}
            >
              <RefreshCw className={`h-4 w-4 ${autoScroll ? "animate-spin" : ""}`} />
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleExport('json')}
            >
              <Download className="h-4 w-4" />
              JSON
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={clearLogs}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 pt-3">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            <Input
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-48"
            />
          </div>
          
          <Select value={selectedLevel} onValueChange={setSelectedLevel}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Level" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Levels</SelectItem>
              <SelectItem value="error">Error</SelectItem>
              <SelectItem value="warning">Warning</SelectItem>
              <SelectItem value="info">Info</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="debug">Debug</SelectItem>
            </SelectContent>
          </Select>

          <Select value={selectedAgent} onValueChange={setSelectedAgent}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Agent" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Agents</SelectItem>
              {uniqueAgents.map(agent => (
                <SelectItem key={agent} value={agent}>{agent}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={selectedSource} onValueChange={setSelectedSource}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sources</SelectItem>
              {uniqueSources.map(source => (
                <SelectItem key={source} value={source}>{source}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          {(selectedLevel !== "all" || selectedAgent !== "all" || selectedSource !== "all" || searchTerm) && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setSelectedLevel("all")
                setSelectedAgent("all")
                setSelectedSource("all")
                setSearchTerm("")
                clearFilters()
              }}
            >
              <Filter className="h-4 w-4" />
              Clear Filters
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <ScrollArea 
          id="logs-scroll-area"
          className="h-full"
          style={{ height: maxHeight }}
        >
          <div className="p-4 space-y-1">
            {filteredLogs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                {logs.length === 0 ? "No logs available" : "No logs match the current filters"}
              </div>
            ) : (
              filteredLogs.map((log) => (
                <div 
                  key={log.id} 
                  className="group hover:bg-muted/50 p-2 rounded-md transition-colors"
                >
                  <div className="flex items-start gap-3 mb-1">
                    <div className="flex items-center gap-2 min-w-0">
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${getLevelColor(log.level)} whitespace-nowrap`}
                      >
                        {log.level.toUpperCase()}
                      </Badge>
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${getSourceColor(log.source || 'unknown')} whitespace-nowrap`}
                      >
                        {log.source || 'unknown'}
                      </Badge>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {formatTime(log)}
                      </span>
                      <span className="text-xs font-medium text-foreground">
                        {log.agent}
                      </span>
                    </div>
                  </div>
                  
                  <div className="ml-2">
                    <pre className="text-xs font-mono bg-muted/30 p-2 rounded border overflow-x-auto whitespace-pre-wrap break-all">
                      {formatJSONL(log)}
                    </pre>
                  </div>
                  
                  {log.task && (
                    <div className="ml-2 mt-1">
                      <Badge variant="secondary" className="text-xs">
                        Task: {log.task}
                      </Badge>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}