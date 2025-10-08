/**
 * TypeScript types matching backend Pydantic models
 * Generated from backend/app/models/ for frontend-backend integration
 */

// Core Task Types
export type TaskStatus = 'pending' | 'working' | 'completed' | 'failed' | 'cancelled';

export interface Task {
  task_id: string;
  project_id: string;
  agent_type: string;
  status: TaskStatus;
  context_ids: string[];
  instructions: string;
  output?: Record<string, any> | null;
  error_message?: string | null;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
  started_at?: string | null; // ISO datetime string
  completed_at?: string | null; // ISO datetime string
}

// Agent Types
export type AgentType = 'orchestrator' | 'analyst' | 'architect' | 'coder' | 'tester' | 'deployer';
export type AgentStatus = 'idle' | 'working' | 'waiting_for_hitl' | 'error';

export interface AgentStatusModel {
  agent_type: AgentType;
  status: AgentStatus;
  current_task_id?: string | null;
  last_activity: string; // ISO datetime string
  error_message?: string | null;
}

// HITL Types
export type HitlStatus = 'pending' | 'approved' | 'rejected' | 'amended' | 'expired';
export type HitlAction = 'approve' | 'reject' | 'amend';

export interface HitlHistoryEntry {
  timestamp: string; // ISO datetime string
  action: string;
  user_id?: string | null;
  content?: Record<string, any> | null;
  comment?: string | null;
}

export interface HitlRequest {
  request_id: string;
  project_id: string;
  task_id: string;
  question: string;
  options: string[];
  status: HitlStatus;
  user_response?: string | null;
  amended_content?: Record<string, any> | null;
  history: HitlHistoryEntry[];
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
  expires_at?: string | null; // ISO datetime string
}

export interface HitlResponse {
  request_id: string;
  action: HitlAction;
  response_content?: string | null;
  amended_data?: Record<string, any> | null;
  comment?: string | null;
  user_id?: string | null;
  timestamp: string; // ISO datetime string
}

export interface HitlRequestResponse {
  request_id: string;
  project_id: string;
  task_id?: string | null;
  question: string;
  options: string[];
  status: string;
  user_response?: string | null;
  response_comment?: string | null;
  amended_content?: Record<string, any> | null;
  history: Record<string, any>[];
  created_at: string;
  updated_at: string;
  expires_at?: string | null;
  responded_at?: string | null;
}

export interface HitlSettingsResponse {
  enabled: boolean;
  counter_total: number;
  counter_remaining: number;
  locked: boolean;
}

// Project Types (inferred from API patterns)
export type ProjectStatus = 'active' | 'completed' | 'paused' | 'failed';

export interface Project {
  id: string;
  name: string;
  description?: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  priority?: 'low' | 'medium' | 'high';
  budget_limit?: number;
  estimated_duration?: number;
  tags?: string[];
  progress?: number;
  agent_config?: {
    max_agents: number;
    agent_types: string[];
  };
}

export interface ProjectStatusResponse {
  project_id: string;
  tasks: Task[];
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
}

export interface CreateTaskRequest {
  agent_type: AgentType;
  instructions: string;
  context_ids?: string[];
}

export interface CreateTaskResponse {
  task_id: string;
  celery_task_id: string;
  status: string;
}

// Context and Artifact Types
export type ContextArtifactType =
  | 'user_input'
  | 'project_plan'
  | 'software_specification'
  | 'implementation_plan'
  | 'source_code'
  | 'test_results'
  | 'deployment_log'
  | 'agent_output';

export interface ContextArtifact {
  context_id: string;
  project_id: string;
  source_agent: string;
  artifact_type: ContextArtifactType;
  content: Record<string, any>;
  artifact_metadata: {
    version?: string;
    confidence_score?: number;
    validation_status?: 'validated' | 'pending' | 'failed';
    tags?: string[];
    related_artifacts?: string[];
  };
  created_at: string;
  updated_at: string;
}

// WebSocket Event Types
export type WebSocketEventType =
  | 'agent_status_changed'
  | 'task_progress_updated'
  | 'hitl_request_created'
  | 'artifact_generated'
  | 'error_notification'
  | 'agent_chat_message'
  | 'safety_alert'
  | 'policy_violation';

export interface WebSocketEvent {
  event_type: WebSocketEventType;
  project_id?: string;
  data: Record<string, any>;
  timestamp?: string;
}

export interface AgentStatusChangedEvent extends WebSocketEvent {
  event_type: 'agent_status_changed';
  project_id: string;
  agent_type: AgentType;
  data: {
    status: AgentStatus;
    current_task_id?: string;
    timestamp: string;
  };
}

export interface TaskProgressUpdatedEvent extends WebSocketEvent {
  event_type: 'task_progress_updated';
  project_id: string;
  task_id: string;
  data: {
    status: TaskStatus;
    progress_percentage: number;
    message: string;
    timestamp: string;
  };
}

export interface HitlRequestCreatedEvent extends WebSocketEvent {
  event_type: 'hitl_request_created';
  project_id: string;
  data: {
    request_id: string;
    question: string;
    urgency: 'low' | 'medium' | 'high';
    expires_at?: string;
  };
}

export interface ArtifactGeneratedEvent extends WebSocketEvent {
  event_type: 'artifact_generated';
  project_id: string;
  data: {
    artifact_id: string;
    artifact_type: ContextArtifactType;
    source_agent: string;
    title: string;
    timestamp: string;
  };
}

export interface ErrorNotificationEvent extends WebSocketEvent {
  event_type: 'error_notification';
  project_id: string;
  data: {
    severity: 'warning' | 'error' | 'critical';
    message: string;
    task_id?: string;
    agent_type?: string;
    error_code?: string;
    timestamp: string;
  };
}

export interface AgentChatMessageEvent extends WebSocketEvent {
  event_type: 'agent_chat_message';
  project_id: string;
  data: {
    agent_type: string;
    message: string;
    message_type: 'info' | 'question' | 'response' | 'thinking';
    requires_response: boolean;
    timestamp: string;
  };
}

export interface PolicyViolationEvent extends WebSocketEvent {
  event_type: 'policy_violation';
  project_id: string;
  data: {
    reason_code: 'AGENT_NOT_ALLOWED' | 'PROMPT_MISALIGNED';
    message: string;
    current_phase: string;
    allowed_agents: AgentType[];
    timestamp: string;
  };
}

// Safety and HITL Safety Types
export interface HitlAgentApproval {
  id: string;
  project_id: string;
  task_id: string;
  agent_type: string;
  request_type: 'PRE_EXECUTION' | 'RESPONSE_APPROVAL';
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  estimated_tokens: number;
  estimated_cost: number;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

export interface EmergencyStop {
  id: string;
  project_id: string;
  reason: string;
  triggered_by: string;
  triggered_at: string;
  status: 'ACTIVE' | 'RESOLVED';
}

// Health and System Status Types
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface SystemHealth {
  status: HealthStatus;
  timestamp: string;
  components: {
    database: HealthStatus;
    redis: HealthStatus;
    celery: HealthStatus;
    llm_providers: HealthStatus;
    hitl_safety: HealthStatus;
  };
  details?: Record<string, any>;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
  request_id?: string;
}

export interface ApiError {
  status: number;
  message: string;
  details?: any;
}

// Pagination Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

// Request/Response Helpers
export type ApiEndpoint = string;
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

export interface RequestConfig {
  method: HttpMethod;
  url: string;
  data?: any;
  params?: Record<string, any>;
  timeout?: number;
  retries?: number;
}
