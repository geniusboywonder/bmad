// Core type definitions for BotArmy Process View

export interface Task {
  id: string
  name: string
  description?: string
  status: 'todo' | 'wip' | 'done' | 'error' | 'blocked'
  assignedTo: string
  createdAt: string
  updatedAt?: string
  completedAt?: string
  progress?: number
  priority?: 'low' | 'medium' | 'high' | 'urgent'
  dependencies?: string[]
  estimatedDuration?: number
  actualDuration?: number
}

export interface Artifact {
  id: string
  name: string
  description?: string
  type: 'document' | 'code' | 'image' | 'data' | 'config' | 'executable'
  status: 'draft' | 'wip' | 'review' | 'approved' | 'final'
  filePath?: string
  downloadUrl?: string
  size?: number
  createdAt: string
  updatedAt?: string
  createdBy: string
  version?: string
  tags?: string[]
  // For code artifacts with file trees
  isDirectory?: boolean
  children?: Artifact[]
}

export interface ProcessStage {
  id: string
  name: string
  description: string
  status: 'done' | 'wip' | 'queued' | 'error' | 'waiting'
  agentName: string
  agentType: 'analyst' | 'architect' | 'developer' | 'tester' | 'deployer'
  currentTask: string
  hitlRequired: boolean
  tasks: Task[]
  artifacts: Artifact[]
  progress: number | { current: number; total: number; percentage: number }
  startedAt?: string
  completedAt?: string
  estimatedDuration?: number
  actualDuration?: number
  dependencies?: string[]
  nextStage?: string
}

export interface ProcessFlow {
  id: string
  name: string
  description: string
  stages: ProcessStage[]
  currentStage: string
  status: 'not_started' | 'in_progress' | 'completed' | 'failed' | 'paused'
  startedAt?: string
  completedAt?: string
  estimatedDuration?: number
  actualDuration?: number
  progress: number
}

export interface Agent {
  id: string
  name: string
  type: 'analyst' | 'architect' | 'developer' | 'tester' | 'deployer'
  status: 'idle' | 'busy' | 'error' | 'offline'
  currentTask?: string
  currentStage?: string
  capabilities: string[]
  configuration?: Record<string, any>
  lastActivity?: string
  tasksCompleted: number
  tasksInProgress: number
  successRate: number
  averageTaskDuration: number
}

export interface SystemHealth {
  overall: 'healthy' | 'warning' | 'error' | 'unknown'
  backend: 'connected' | 'disconnected' | 'error'
  websocket: 'connected' | 'disconnected' | 'reconnecting' | 'error'
  database: 'connected' | 'disconnected' | 'error'
  llmProviders: {
    openai: 'available' | 'unavailable' | 'rate_limited' | 'error'
    anthropic: 'available' | 'unavailable' | 'rate_limited' | 'error'
    google: 'available' | 'unavailable' | 'rate_limited' | 'error'
  }
  lastChecked: string
}

export interface GlobalStatistics {
  totalTasks: number
  tasksByStatus: {
    todo: number
    wip: number
    done: number
    error: number
    blocked: number
  }
  totalArtifacts: number
  artifactsByType: Record<string, number>
  systemHealth: SystemHealth
  activeAgents: number
  averageTaskDuration: number
  successRate: number
  projectsInProgress: number
  projectsCompleted: number
}

// WebSocket message types
export interface WebSocketMessage {
  id: string
  type: 'task_update' | 'stage_update' | 'artifact_update' | 'agent_status' | 'system_health' | 'chat_message' | 'hitl_required'
  timestamp: string
  data: any
  source?: string
  target?: string
}

// Chat and communication types
export interface ChatMessage {
  id: string
  content: string
  sender: 'user' | 'agent' | 'system'
  senderName?: string
  timestamp: string
  type: 'message' | 'command' | 'notification' | 'error'
  metadata?: Record<string, any>
  replyTo?: string
}

export interface HITLRequest {
  id: string
  type: 'approval' | 'input' | 'decision' | 'review'
  title: string
  description: string
  context: Record<string, any>
  options?: Array<{
    id: string
    label: string
    value: any
    description?: string
  }>
  urgency: 'low' | 'medium' | 'high' | 'critical'
  requestedAt: string
  requestedBy: string
  stage: string
  task?: string
  deadline?: string
  status: 'pending' | 'responded' | 'expired'
  response?: any
  respondedAt?: string
}

// Configuration types
export interface StageConfiguration {
  stageId: string
  stageName: string
  agentType: 'analyst' | 'architect' | 'developer' | 'tester' | 'deployer'
  agentConfiguration: {
    roleDefinition?: string
    roleFilePath?: string
    capabilities: string[]
    tools: string[]
    parameters: Record<string, any>
  }
  artifactConfiguration: {
    requiredArtifacts: string[]
    optionalArtifacts: string[]
    customArtifacts?: Array<{
      name: string
      type: string
      description: string
      template?: string
    }>
  }
  workflowConfiguration: {
    pausePoints: string[]
    hitlTriggers: string[]
    dependencies: string[]
    estimatedDuration: number
    maxRetries: number
  }
}

// Error handling types
export interface AppError {
  id: string
  type: 'validation' | 'network' | 'server' | 'client' | 'unknown'
  message: string
  details?: string
  source: string
  timestamp: string
  stack?: string
  context?: Record<string, any>
  severity: 'low' | 'medium' | 'high' | 'critical'
  resolved?: boolean
  resolvedAt?: string
}

// API response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: {
    code: string
    message: string
    details?: any
  }
  timestamp: string
  requestId?: string
}
