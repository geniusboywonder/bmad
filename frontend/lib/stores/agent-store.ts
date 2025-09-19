import { create } from "zustand"
import { subscribeWithSelector, persist, createJSONStorage } from "zustand/middleware"

// Safe storage implementation with error handling
const createSafeStorage = () => {
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

export interface Agent {
  id: string
  name: string
  role: string
  status: "active" | "idle" | "error" | "offline" | "thinking" | "paused"
  currentTask?: string
  lastActivity: Date
  tasksCompleted: number
  successRate: number
  progress?: number
  progress_stage?: string
  progress_current?: number
  progress_total?: number
  progress_estimated_time_remaining?: number
  is_thinking?: boolean
  currentStep?: string
  
  // Enhanced tracking fields
  startTime?: Date
  endTime?: Date
  totalRuntime: number // in seconds
  averageTaskTime: number // in seconds
  errorCount: number
  lastError?: string
  queue: {
    todo: number
    inProgress: number
    done: number
    failed: number
  }
  
  // Performance metrics
  performance: {
    responseTime: number // in milliseconds
    throughput: number // tasks per hour
    efficiency: number // percentage
    uptime: number // percentage
  }
}

// WebSocket message interface for agent updates
export interface WebSocketMessage {
  type: string
  agent_name?: string
  data?: {
    status?: Agent['status']
    current_task?: string
    progress?: number
    progress_stage?: string
    progress_current?: number
    progress_total?: number
    progress_estimated_time_remaining?: number
    is_thinking?: boolean
    current_step?: string
    [key: string]: any
  }
  [key: string]: any
}

interface AgentMetrics {
  totalTasks: number
  completedTasks: number
  failedTasks: number
  avgResponseTime: number
  overallSuccessRate: number
  systemUptime: number
}

interface AgentStore {
  agents: Agent[]
  activeAgentCount: number
  metrics: AgentMetrics
  isInitialized: boolean
  lastSync: Date | null
  
  // Agent filtering
  agent: Agent | null
  agentFilter: string
  setAgentFilter: (filter: string) => void
  
  // Core agent management
  setAgents: (agents: Agent[]) => void
  updateAgent: (id: string, updates: Partial<Agent>) => void
  updateAgentByName: (name: string, updates: Partial<Agent>) => void
  getAgentById: (id: string) => Agent | undefined
  getAgentByName: (name: string) => Agent | undefined
  
  // Message handling
  updateAgentFromMessage: (message: WebSocketMessage) => void
  handleAgentError: (agentName: string, error: string) => void
  
  // Enhanced functionality
  startAgentTask: (agentName: string, task: string) => void
  completeAgentTask: (agentName: string, success?: boolean) => void
  pauseAgent: (agentName: string) => void
  resumeAgent: (agentName: string) => void
  resetAgent: (agentName: string) => void
  
  // Metrics and analytics
  updateMetrics: () => void
  getAgentPerformance: (agentName: string) => Agent['performance'] | null
  getSystemHealth: () => { healthy: number; total: number; percentage: number }
  
  // Persistence and sync
  syncWithBackend: () => Promise<void>
  exportAgentData: () => string
  importAgentData: (data: string) => void
}

// Helper function to calculate agent performance
const calculatePerformance = (agent: Agent): Agent['performance'] => {
  const totalTasks = agent.tasksCompleted + agent.errorCount
  const efficiency = totalTasks > 0 ? (agent.tasksCompleted / totalTasks) * 100 : 100
  const uptime = agent.totalRuntime > 0 ? 
    ((agent.totalRuntime - (agent.errorCount * 60)) / agent.totalRuntime) * 100 : 100
  
  return {
    responseTime: agent.averageTaskTime * 1000, // convert to ms
    throughput: agent.totalRuntime > 0 ? (agent.tasksCompleted / (agent.totalRuntime / 3600)) : 0,
    efficiency: Math.max(0, Math.min(100, efficiency)),
    uptime: Math.max(0, Math.min(100, uptime))
  }
}


// Helper function to parse agent messages
const parseAgentMessage = (message: WebSocketMessage): { name: string; updates: Partial<Agent> } | null => {
  const agentName = message.agent_name || (message.data?.agent_name)
  if (!agentName) return null

  const updates: Partial<Agent> = {
    lastActivity: new Date()
  }

  if (message.data) {
    const data = message.data
    
    if (data.status) updates.status = data.status
    if (data.current_task) updates.currentTask = data.current_task
    if (typeof data.progress === 'number') updates.progress = data.progress
    if (data.progress_stage) updates.progress_stage = data.progress_stage
    if (typeof data.progress_current === 'number') updates.progress_current = data.progress_current
    if (typeof data.progress_total === 'number') updates.progress_total = data.progress_total
    if (typeof data.progress_estimated_time_remaining === 'number') {
      updates.progress_estimated_time_remaining = data.progress_estimated_time_remaining
    }
    if (typeof data.is_thinking === 'boolean') updates.is_thinking = data.is_thinking
    if (data.current_step) updates.currentStep = data.current_step
  }

  return { name: agentName, updates }
}

export const useAgentStore = create<AgentStore>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        agents: [],
        activeAgentCount: 0,
        metrics: {
          totalTasks: 0,
          completedTasks: 0,
          failedTasks: 0,
          avgResponseTime: 0,
          overallSuccessRate: 0,
          systemUptime: 0
        },
        isInitialized: false,
        lastSync: null,
        
        // Agent filtering
        agent: null,
        agentFilter: '',
        setAgentFilter: (filter) => {
          const agent = filter ? get().getAgentByName(filter) : null;
          set({ agentFilter: filter, agent });
        },

        // Core agent management
        setAgents: (agents) => {
          set({ agents, isInitialized: true })
          get().updateMetrics()
        },

        updateAgent: (id, updates) => {
          set((state) => ({
            agents: state.agents.map((agent) => {
              if (agent.id === id) {
                const updatedAgent = { ...agent, ...updates }
                // Recalculate performance if relevant fields changed
                if ('tasksCompleted' in updates || 'errorCount' in updates || 'totalRuntime' in updates) {
                  updatedAgent.performance = calculatePerformance(updatedAgent)
                }
                return updatedAgent
              }
              return agent
            })
          }))
          get().updateMetrics()
        },

        updateAgentByName: (name, updates) => {
          const agent = get().getAgentByName(name)
          if (agent) {
            get().updateAgent(agent.id, updates)
          }
        },

        getAgentById: (id) => get().agents.find((agent) => agent.id === id),
        
        getAgentByName: (name) => get().agents.find((agent) => 
          agent.name.toLowerCase() === name.toLowerCase()
        ),

        // Message handling
        updateAgentFromMessage: (message) => {
          const parsed = parseAgentMessage(message)
          if (parsed) {
            get().updateAgentByName(parsed.name, parsed.updates)
          }
        },

        handleAgentError: (agentName, error) => {
          get().updateAgentByName(agentName, {
            status: 'error',
            lastError: error,
            errorCount: (get().getAgentByName(agentName)?.errorCount || 0) + 1
          })
        },

        // Enhanced functionality
        startAgentTask: (agentName, task) => {
          get().updateAgentByName(agentName, {
            status: 'active',
            currentTask: task,
            startTime: new Date(),
            is_thinking: true
          })
        },

        completeAgentTask: (agentName, success = true) => {
          const agent = get().getAgentByName(agentName)
          if (agent) {
            const endTime = new Date()
            const taskDuration = agent.startTime ? 
              (endTime.getTime() - agent.startTime.getTime()) / 1000 : 0

            const updates: Partial<Agent> = {
              status: 'idle',
              endTime,
              is_thinking: false,
              totalRuntime: agent.totalRuntime + taskDuration,
              queue: {
                ...agent.queue,
                inProgress: Math.max(0, agent.queue.inProgress - 1),
                done: agent.queue.done + (success ? 1 : 0),
                failed: agent.queue.failed + (success ? 0 : 1)
              }
            }

            if (success) {
              updates.tasksCompleted = agent.tasksCompleted + 1
              const newTotal = agent.tasksCompleted + 1 + agent.errorCount
              updates.successRate = (agent.tasksCompleted + 1) / newTotal * 100
            }

            // Update average task time
            if (agent.tasksCompleted > 0) {
              updates.averageTaskTime = 
                (agent.averageTaskTime * agent.tasksCompleted + taskDuration) / 
                (agent.tasksCompleted + (success ? 1 : 0))
            } else if (success) {
              updates.averageTaskTime = taskDuration
            }

            get().updateAgent(agent.id, updates)
          }
        },

        pauseAgent: (agentName) => {
          get().updateAgentByName(agentName, { status: 'paused' })
        },

        resumeAgent: (agentName) => {
          get().updateAgentByName(agentName, { status: 'active' })
        },

        resetAgent: (agentName) => {
          const agent = get().getAgentByName(agentName)
          if (agent) {
            get().updateAgent(agent.id, {
              status: 'idle',
              currentTask: undefined,
              progress: 0,
              tasksCompleted: 0,
              successRate: 0,
              totalRuntime: 0,
              averageTaskTime: 0,
              errorCount: 0,
              lastError: undefined,
              queue: { todo: 0, inProgress: 0, done: 0, failed: 0 },
              performance: { responseTime: 0, throughput: 0, efficiency: 0, uptime: 0 }
            })
          }
        },

        // Metrics and analytics
        updateMetrics: () => {
          const { agents } = get()
          const totalTasks = agents.reduce((sum, agent) => sum + agent.tasksCompleted, 0)
          const completedTasks = totalTasks
          const failedTasks = agents.reduce((sum, agent) => sum + agent.errorCount, 0)
          const avgResponseTime = agents.length > 0 ?
            agents.reduce((sum, agent) => sum + agent.performance.responseTime, 0) / agents.length : 0
          
          const totalWithFailed = completedTasks + failedTasks
          const overallSuccessRate = totalWithFailed > 0 ? (completedTasks / totalWithFailed) * 100 : 0
          
          const activeAgents = agents.filter(a => a.status !== 'offline').length
          const systemUptime = agents.length > 0 ?
            agents.reduce((sum, agent) => sum + agent.performance.uptime, 0) / agents.length : 0

          set({
            activeAgentCount: activeAgents,
            metrics: {
              totalTasks,
              completedTasks,
              failedTasks,
              avgResponseTime,
              overallSuccessRate,
              systemUptime
            }
          })
        },

        getAgentPerformance: (agentName) => {
          const agent = get().getAgentByName(agentName)
          return agent?.performance || null
        },

        getSystemHealth: () => {
          const { agents } = get()
          const healthy = agents.filter(a => a.status !== 'error' && a.status !== 'offline').length
          const total = agents.length
          const percentage = total > 0 ? (healthy / total) * 100 : 0
          return { healthy, total, percentage }
        },

        // Persistence and sync
        syncWithBackend: async () => {
          try {
            // This would typically fetch from /api/agents
            // For now, we'll just update the lastSync timestamp
            set({ lastSync: new Date() })
          } catch (error) {
            console.error('Failed to sync with backend:', error)
          }
        },

        exportAgentData: () => {
          const { agents, metrics } = get()
          return JSON.stringify({ agents, metrics, exportedAt: new Date() }, null, 2)
        },

        importAgentData: (data) => {
          try {
            const parsed = JSON.parse(data)
            if (parsed.agents && Array.isArray(parsed.agents)) {
              get().setAgents(parsed.agents)
            }
          } catch (error) {
            console.error('Failed to import agent data:', error)
          }
        }
      }),
      {
        name: 'agent-store',
        storage: createJSONStorage(() => createSafeStorage()),
        version: 1,
        partialize: (state) => ({
          agents: state.agents,
          isInitialized: state.isInitialized,
          agentFilter: state.agentFilter
        })
      }
    )
  )
)

// The store now starts with an empty agent list.
// It will be populated dynamically based on the selected process.
