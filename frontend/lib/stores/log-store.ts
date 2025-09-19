import { create } from "zustand"
import { subscribeWithSelector, persist, createJSONStorage } from "zustand/middleware"

// Safe storage implementation with error handling
const createSafeStorage = (fallback?: any) => {
  const storage = {
    getItem: (name: string): string | null => {
      try {
        if (typeof window === 'undefined') return null
        return window.localStorage.getItem(name)
      } catch (error) {
        console.warn(`Failed to read from localStorage: ${error}`)
        return null
      }
    },
    setItem: (name: string, value: string): void => {
      try {
        if (typeof window === 'undefined') return
        window.localStorage.setItem(name, value)
      } catch (error) {
        console.warn(`Failed to write to localStorage: ${error}`)
        // Optionally clear some space and retry
        if (error instanceof DOMException && error.code === 22) {
          try {
            window.localStorage.clear()
            window.localStorage.setItem(name, value)
          } catch (retryError) {
            console.error('localStorage completely unavailable:', retryError)
          }
        }
      }
    },
    removeItem: (name: string): void => {
      try {
        if (typeof window === 'undefined') return
        window.localStorage.removeItem(name)
      } catch (error) {
        console.warn(`Failed to remove from localStorage: ${error}`)
      }
    }
  }
  return storage
}

export interface LogEntry {
  id: string
  timestamp: Date
  agent: string
  level: "info" | "warning" | "error" | "success" | "debug"
  message: string
  task?: string
  metadata?: Record<string, any>
  
  // Enhanced fields
  category?: string
  source?: 'agent' | 'system' | 'user' | 'websocket'
  duration?: number // for task completion logs
  severity?: 1 | 2 | 3 | 4 | 5 // 1=low, 5=critical
  tags?: string[]
  correlationId?: string // for tracking related events
  sessionId?: string
}

interface LogFilters {
  agent?: string
  level?: LogEntry["level"]
  source?: LogEntry["source"]
  category?: string
  severity?: LogEntry["severity"]
  startDate?: Date
  endDate?: Date
  searchTerm?: string
  tags?: string[]
}

interface LogMetrics {
  totalLogs: number
  errorCount: number
  warningCount: number
  infoCount: number
  successCount: number
  debugCount: number
  averageLogsPerMinute: number
  topAgents: Array<{ agent: string; count: number }>
  recentErrorRate: number // errors in last hour
  systemHealthScore: number // based on error/warning ratio
}

interface LogStore {
  logs: LogEntry[]
  filteredLogs: LogEntry[]
  currentFilters: LogFilters
  metrics: LogMetrics
  isLoading: boolean
  maxLogs: number
  searchIndex: Map<string, Set<string>>
  
  // Core functionality
  addLog: (log: Omit<LogEntry, "id" | "timestamp">) => void
  addLogs: (logs: Omit<LogEntry, "id" | "timestamp">[]) => void
  removeLog: (id: string) => void
  clearLogs: () => void
  
  // Filtering and search
  setFilters: (filters: Partial<LogFilters>) => void
  clearFilters: () => void
  searchLogs: (term: string) => LogEntry[]
  
  // Metrics and analytics
  getMetrics: () => LogMetrics
  getTopAgents: (limit?: number) => Array<{ agent: string; count: number }>
  getRecentActivity: (minutes?: number) => Array<{
    timestamp: Date
    count: number
    avgDuration: number
  }>
  
  // Export and persistence
  exportLogs: (format: 'json' | 'csv' | 'txt') => string
  importLogs: (data: string) => void
  
  // Performance optimization
  purgeLogs: (keepCount?: number) => void
  compactLogs: () => void
  
  // Real-time updates
  subscribeToLevel: (level: LogEntry["level"], callback: (log: LogEntry) => void) => () => void
  subscribeToAgent: (agent: string, callback: (log: LogEntry) => void) => () => void
}

// Enhanced log queue with batching
let logQueue: Array<Omit<LogEntry, "id" | "timestamp"> & { timestamp?: Date }> = []
let debounceTimer: NodeJS.Timeout | null = null
let idCounter = 0

// Utility functions
const generateLogId = (): string => {
  return `log_${Date.now()}_${++idCounter}`
}

const calculateSeverity = (level: LogEntry["level"], metadata?: Record<string, any>): LogEntry["severity"] => {
  if (metadata?.severity) return metadata.severity
  
  switch (level) {
    case 'error': return 4
    case 'warning': return 3
    case 'info': return 2
    case 'success': return 1
    case 'debug': return 1
    default: return 2
  }
}

const buildSearchIndex = (logs: LogEntry[]): Map<string, Set<string>> => {
  const index = new Map<string, Set<string>>()
  
  logs.forEach(log => {
    const terms = [
      log.agent.toLowerCase(),
      log.level.toLowerCase(),
      log.message.toLowerCase(),
      log.task?.toLowerCase() || '',
      log.category?.toLowerCase() || '',
      ...(log.tags || []).map(tag => tag.toLowerCase())
    ].filter(Boolean)
    
    terms.forEach(term => {
      const words = term.split(/\s+/).filter(word => word.length > 2)
      words.forEach(word => {
        if (!index.has(word)) {
          index.set(word, new Set())
        }
        index.get(word)!.add(log.id)
      })
    })
  })
  
  return index
}

const filterLogs = (logs: LogEntry[], filters: LogFilters): LogEntry[] => {
  return logs.filter(log => {
    // Agent filter
    if (filters.agent && log.agent !== filters.agent) return false
    
    // Level filter
    if (filters.level && log.level !== filters.level) return false
    
    // Source filter
    if (filters.source && log.source !== filters.source) return false
    
    // Category filter
    if (filters.category && log.category !== filters.category) return false
    
    // Severity filter
    if (filters.severity && log.severity !== filters.severity) return false
    
    // Date range filter
    if (filters.startDate && log.timestamp < filters.startDate) return false
    if (filters.endDate && log.timestamp > filters.endDate) return false
    
    // Search term filter
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase()
      const searchableText = [
        log.agent,
        log.message,
        log.task || '',
        log.category || ''
      ].join(' ').toLowerCase()
      
      if (!searchableText.includes(searchLower)) return false
    }
    
    // Tags filter
    if (filters.tags && filters.tags.length > 0) {
      const logTags = log.tags || []
      if (!filters.tags.some(tag => logTags.includes(tag))) return false
    }
    
    return true
  })
}

const calculateMetrics = (logs: LogEntry[]): LogMetrics => {
  // Count by level
  const levelCounts = logs.reduce((acc, log) => {
    acc[log.level] = (acc[log.level] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  
  // Calculate top agents
  const agentCounts = logs.reduce((acc, log) => {
    acc[log.agent] = (acc[log.agent] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  
  const topAgents = Object.entries(agentCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([agent, count]) => ({ agent, count }))
  
  // Calculate recent error rate (last hour)
  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000)
  const recentLogs = logs.filter(log => log.timestamp >= oneHourAgo)
  const recentErrorCount = recentLogs.filter(log => log.level === 'error').length
  const recentErrorRate = recentLogs.length > 0 ? (recentErrorCount / recentLogs.length) * 100 : 0
  
  const errorWarningCount = (levelCounts.error || 0) + (levelCounts.warning || 0)
  const totalCount = logs.length
  const systemHealthScore = totalCount > 0 ? 
    Math.max(0, 100 - (errorWarningCount / totalCount) * 100) : 100
  
  // Calculate logs per minute over last hour
  const averageLogsPerMinute = recentLogs.length > 0 ? recentLogs.length / 60 : 0
  
  return {
    totalLogs: logs.length,
    errorCount: levelCounts.error || 0,
    warningCount: levelCounts.warning || 0,
    infoCount: levelCounts.info || 0,
    successCount: levelCounts.success || 0,
    debugCount: levelCounts.debug || 0,
    averageLogsPerMinute,
    topAgents,
    recentErrorRate,
    systemHealthScore
  }
}

export const useLogStore = create<LogStore>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        logs: [],
        filteredLogs: [],
        currentFilters: {},
        metrics: {
          totalLogs: 0,
          errorCount: 0,
          warningCount: 0,
          infoCount: 0,
          successCount: 0,
          debugCount: 0,
          averageLogsPerMinute: 0,
          topAgents: [],
          recentErrorRate: 0,
          systemHealthScore: 100
        },
        isLoading: false,
        maxLogs: 5000,
        searchIndex: new Map(),

        // Core functionality
        addLog: (log) => {
          logQueue.push({
            ...log,
            timestamp: log.timestamp || new Date()
          })
          
          if (!debounceTimer) {
            debounceTimer = setTimeout(() => {
              const { maxLogs } = get()
              
              set((state) => {
                const newLogs = logQueue.map(l => ({
                  ...l,
                  id: generateLogId(),
                  timestamp: l.timestamp || new Date(),
                  severity: calculateSeverity(l.level, l.metadata),
                  source: l.source || 'system',
                  sessionId: l.sessionId || 'default'
                } as LogEntry))
                
                const allLogs = [...state.logs, ...newLogs].slice(-maxLogs)
                const searchIndex = buildSearchIndex(allLogs)
                // Fix: Ensure filteredLogs is always synced when no filters applied
                const filteredLogs = Object.keys(state.currentFilters).length === 0 
                  ? allLogs 
                  : filterLogs(allLogs, state.currentFilters)
                const metrics = calculateMetrics(allLogs)
                
                return {
                  logs: allLogs,
                  filteredLogs,
                  searchIndex,
                  metrics
                }
              })
              
              logQueue = []
              debounceTimer = null
            }, 50) // Reduced debounce for better real-time feel
          }
        },

        addLogs: (logs) => {
          logs.forEach(log => get().addLog(log))
        },

        removeLog: (id) => {
          set((state) => {
            const logs = state.logs.filter(log => log.id !== id)
            const filteredLogs = filterLogs(logs, state.currentFilters)
            const metrics = calculateMetrics(logs)
            const searchIndex = buildSearchIndex(logs)
            
            return { logs, filteredLogs, metrics, searchIndex }
          })
        },

        clearLogs: () => {
          set({
            logs: [],
            filteredLogs: [],
            currentFilters: {},
            metrics: {
              totalLogs: 0,
              errorCount: 0,
              warningCount: 0,
              infoCount: 0,
              successCount: 0,
              debugCount: 0,
              averageLogsPerMinute: 0,
              topAgents: [],
              recentErrorRate: 0,
              systemHealthScore: 100
            },
            searchIndex: new Map()
          })
        },

        // Filtering and search
        setFilters: (filters) => {
          set((state) => {
            const newFilters = { ...state.currentFilters, ...filters }
            const filteredLogs = filterLogs(state.logs, newFilters)
            
            return {
              currentFilters: newFilters,
              filteredLogs
            }
          })
        },

        clearFilters: () => {
          set((state) => ({
            currentFilters: {},
            filteredLogs: state.logs // Fix: Sync filteredLogs with logs when clearing filters
          }))
        },

        searchLogs: (term) => {
          const { logs, searchIndex } = get()
          if (!term.trim()) return logs
          
          const searchWords = term.toLowerCase().split(/\s+/).filter(w => w.length > 2)
          const matchingIds = new Set<string>()
          
          searchWords.forEach(word => {
            const ids = searchIndex.get(word)
            if (ids) {
              if (matchingIds.size === 0) {
                ids.forEach(id => matchingIds.add(id))
              } else {
                // Intersection for AND search
                const intersection = new Set<string>()
                ids.forEach(id => {
                  if (matchingIds.has(id)) intersection.add(id)
                })
                matchingIds.clear()
                intersection.forEach(id => matchingIds.add(id))
              }
            }
          })
          
          return logs.filter(log => matchingIds.has(log.id))
        },

        // Rest of the implementation stays the same...
        getMetrics: () => get().metrics,
        getTopAgents: (limit = 5) => get().metrics.topAgents.slice(0, limit),
        getRecentActivity: (minutes = 60) => {
          const { logs } = get()
          const cutoff = new Date(Date.now() - minutes * 60 * 1000)
          const recentLogs = logs.filter(log => log.timestamp >= cutoff)
          
          return []
        },
        
        exportLogs: (format) => {
          const { filteredLogs } = get()
          if (format === 'json') return JSON.stringify(filteredLogs, null, 2)
          if (format === 'csv') {
            const headers = ['timestamp', 'agent', 'level', 'message', 'source', 'category']
            const rows = filteredLogs.map(log => [
              log.timestamp.toISOString(),
              log.agent,
              log.level,
              log.message,
              log.source || '',
              log.category || ''
            ])
            return [headers, ...rows].map(row => row.join(',')).join('\n')
          }
          return filteredLogs.map(log => 
            `${log.timestamp.toISOString()} [${log.level.toUpperCase()}] ${log.agent}: ${log.message}`
          ).join('\n')
        },
        
        importLogs: (data) => {
          try {
            const importedLogs = JSON.parse(data)
            if (Array.isArray(importedLogs)) {
              get().addLogs(importedLogs.map(log => ({
                ...log,
                timestamp: new Date(log.timestamp)
              })))
            }
          } catch (error) {
            console.error('Failed to import logs:', error)
          }
        },
        
        purgeLogs: (keepCount = 1000) => {
          set((state) => {
            const logs = state.logs.slice(-keepCount)
            const filteredLogs = filterLogs(logs, state.currentFilters)
            const metrics = calculateMetrics(logs)
            const searchIndex = buildSearchIndex(logs)
            
            return { logs, filteredLogs, metrics, searchIndex }
          })
        },
        
        compactLogs: () => {
          // Remove duplicate logs and optimize memory
          set((state) => {
            const uniqueLogs = state.logs.filter((log, index, arr) => 
              arr.findIndex(l => l.id === log.id) === index
            )
            const filteredLogs = filterLogs(uniqueLogs, state.currentFilters)
            const metrics = calculateMetrics(uniqueLogs)
            const searchIndex = buildSearchIndex(uniqueLogs)
            
            return { 
              logs: uniqueLogs, 
              filteredLogs, 
              metrics, 
              searchIndex
            }
          })
        },
        
        subscribeToLevel: (level, callback) => {
          return get()[subscribeWithSelector.subscribe](
            (state) => state.logs.filter(log => log.level === level),
            (logs) => logs.forEach(callback)
          )
        },
        
        subscribeToAgent: (agent, callback) => {
          return get()[subscribeWithSelector.subscribe](
            (state) => state.logs.filter(log => log.agent === agent),
            (logs) => logs.forEach(callback)
          )
        }
      }),
      {
        name: 'log-store',
        storage: createJSONStorage(() => createSafeStorage()),
        partialize: (state) => ({
          logs: state.logs.slice(-1000), // Only persist last 1000 logs
          currentFilters: state.currentFilters,
          maxLogs: state.maxLogs
        }),
        version: 1,
        onRehydrateStorage: () => (state) => {
          // Ensure filteredLogs is synced after rehydration
          if (state && Object.keys(state.currentFilters).length === 0) {
            state.filteredLogs = state.logs
          }
        },
      }
    )
  )
)