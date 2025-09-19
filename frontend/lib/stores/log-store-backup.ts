import { create } from "zustand"
import { subscribeWithSelector, persist, createJSONStorage } from "zustand/middleware"

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
  searchIndex: Map<string, Set<string>> // for fast searching
  
  // Core functionality
  addLog: (log: Omit<LogEntry, "id" | "timestamp">) => void
  addLogs: (logs: Omit<LogEntry, "id" | "timestamp">[]) => void
  clearLogs: () => void
  
  // Enhanced queries
  getLogsByAgent: (agent: string) => LogEntry[]
  getLogsByLevel: (level: LogEntry["level"]) => LogEntry[]
  getLogsByTimeRange: (start: Date, end: Date) => LogEntry[]
  getRecentLogs: (minutes: number) => LogEntry[]
  
  // Filtering and search
  setFilters: (filters: Partial<LogFilters>) => void
  clearFilters: () => void
  searchLogs: (term: string) => LogEntry[]
  
  // Analytics and metrics
  updateMetrics: () => void
  getErrorLogs: () => LogEntry[]
  getSystemErrors: () => LogEntry[]
  getAgentPerformanceLog: (agent: string) => {
    errors: number
    warnings: number
    tasks: number
    avgDuration: number
  }
  
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
  const now = new Date()
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)
  const recentLogs = logs.filter(log => log.timestamp > oneHourAgo)
  
  const levelCounts = logs.reduce((acc, log) => {
    acc[log.level] = (acc[log.level] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  
  const agentCounts = logs.reduce((acc, log) => {
    acc[log.agent] = (acc[log.agent] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  
  const topAgents = Object.entries(agentCounts)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)
    .map(([agent, count]) => ({ agent, count }))
  
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
                const filteredLogs = filterLogs(allLogs, state.currentFilters)
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

        clearLogs: () => {
          set({
            logs: [],
            filteredLogs: [],
            searchIndex: new Map(),
            metrics: calculateMetrics([])
          })
        },

        // Enhanced queries
        getLogsByAgent: (agent) => {
          return get().logs.filter(log => log.agent === agent)
        },

        getLogsByLevel: (level) => {
          return get().logs.filter(log => log.level === level)
        },

        getLogsByTimeRange: (start, end) => {
          return get().logs.filter(log => 
            log.timestamp >= start && log.timestamp <= end
          )
        },

        getRecentLogs: (minutes) => {
          const cutoff = new Date(Date.now() - minutes * 60 * 1000)
          return get().logs.filter(log => log.timestamp > cutoff)
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
            filteredLogs: state.logs
          }))
        },

        searchLogs: (term) => {
          const { logs, searchIndex } = get()
          if (!term.trim()) return logs
          
          const searchTerms = term.toLowerCase().split(/\s+/)
          let matchingIds = new Set<string>()
          
          searchTerms.forEach((searchTerm, index) => {
            const termMatches = new Set<string>()
            
            for (const [indexedTerm, logIds] of searchIndex.entries()) {
              if (indexedTerm.includes(searchTerm)) {
                logIds.forEach(id => termMatches.add(id))
              }
            }
            
            if (index === 0) {
              matchingIds = termMatches
            } else {
              // Intersection for AND behavior
              matchingIds = new Set([...matchingIds].filter(id => termMatches.has(id)))
            }
          })
          
          return logs.filter(log => matchingIds.has(log.id))
        },

        // Analytics and metrics
        updateMetrics: () => {
          set((state) => ({
            metrics: calculateMetrics(state.logs)
          }))
        },

        getErrorLogs: () => {
          return get().logs.filter(log => log.level === 'error')
        },

        getSystemErrors: () => {
          return get().logs.filter(log => 
            log.level === 'error' && log.source === 'system'
          )
        },

        getAgentPerformanceLog: (agent) => {
          const agentLogs = get().getLogsByAgent(agent)
          const errors = agentLogs.filter(log => log.level === 'error').length
          const warnings = agentLogs.filter(log => log.level === 'warning').length
          const tasks = agentLogs.filter(log => log.task).length
          
          const durationsAvailable = agentLogs
            .filter(log => log.duration !== undefined)
            .map(log => log.duration!)
          
          const avgDuration = durationsAvailable.length > 0 ?
            durationsAvailable.reduce((sum, d) => sum + d, 0) / durationsAvailable.length : 0
          
          return { errors, warnings, tasks, avgDuration }
        },

        // Export and persistence
        exportLogs: (format) => {
          const { logs } = get()
          
          switch (format) {
            case 'json':
              return JSON.stringify(logs, null, 2)
              
            case 'csv':
              const headers = ['timestamp', 'agent', 'level', 'message', 'task', 'source', 'severity']
              const csvRows = [
                headers.join(','),
                ...logs.map(log => [
                  log.timestamp.toISOString(),
                  log.agent,
                  log.level,
                  `"${log.message.replace(/"/g, '""')}"`,
                  log.task || '',
                  log.source || '',
                  log.severity || ''
                ].join(','))
              ]
              return csvRows.join('\n')
              
            case 'txt':
              return logs.map(log => 
                `[${log.timestamp.toISOString()}] ${log.level.toUpperCase()} ${log.agent}: ${log.message}`
              ).join('\n')
              
            default:
              return JSON.stringify(logs, null, 2)
          }
        },

        importLogs: (data) => {
          try {
            const parsed = JSON.parse(data)
            if (Array.isArray(parsed)) {
              const validLogs = parsed.filter(log => 
                log.agent && log.level && log.message
              ).map(log => ({
                ...log,
                timestamp: new Date(log.timestamp)
              }))
              
              set((state) => {
                const allLogs = [...state.logs, ...validLogs].slice(-state.maxLogs)
                const searchIndex = buildSearchIndex(allLogs)
                const filteredLogs = filterLogs(allLogs, state.currentFilters)
                const metrics = calculateMetrics(allLogs)
                
                return {
                  logs: allLogs,
                  filteredLogs,
                  searchIndex,
                  metrics
                }
              })
            }
          } catch (error) {
            console.error('Failed to import logs:', error)
          }
        },

        // Performance optimization
        purgeLogs: (keepCount = 1000) => {
          set((state) => {
            const sortedLogs = [...state.logs].sort((a, b) => 
              b.timestamp.getTime() - a.timestamp.getTime()
            )
            const keptLogs = sortedLogs.slice(0, keepCount)
            const searchIndex = buildSearchIndex(keptLogs)
            const filteredLogs = filterLogs(keptLogs, state.currentFilters)
            const metrics = calculateMetrics(keptLogs)
            
            return {
              logs: keptLogs,
              filteredLogs,
              searchIndex,
              metrics
            }
          })
        },

        compactLogs: () => {
          // Remove debug logs older than 1 hour, keep critical logs
          const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000)
          
          set((state) => {
            const compactedLogs = state.logs.filter(log => {
              if (log.level === 'debug' && log.timestamp < oneHourAgo) {
                return false
              }
              return true
            })
            
            const searchIndex = buildSearchIndex(compactedLogs)
            const filteredLogs = filterLogs(compactedLogs, state.currentFilters)
            const metrics = calculateMetrics(compactedLogs)
            
            return {
              logs: compactedLogs,
              filteredLogs,
              searchIndex,
              metrics
            }
          })
        },

        // Real-time subscriptions
        subscribeToLevel: (level, callback) => {
          return get().subscribe(
            (state) => state.logs,
            (logs, prevLogs) => {
              const newLogs = logs.slice(prevLogs.length)
              newLogs.forEach(log => {
                if (log.level === level) {
                  callback(log)
                }
              })
            }
          )
        },

        subscribeToAgent: (agent, callback) => {
          return get().subscribe(
            (state) => state.logs,
            (logs, prevLogs) => {
              const newLogs = logs.slice(prevLogs.length)
              newLogs.forEach(log => {
                if (log.agent === agent) {
                  callback(log)
                }
              })
            }
          )
        }
      }),
      {
        name: 'log-store',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          logs: state.logs.slice(-1000), // Only persist last 1000 logs
          currentFilters: state.currentFilters,
          maxLogs: state.maxLogs
        }),
        version: 1,
      }
    )
  )
)