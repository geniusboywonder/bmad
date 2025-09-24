/**
 * Agents Service - Agent status and management
 * Handles real-time agent status tracking and management operations
 */

import { apiClient } from './client';
import {
  AgentStatusModel,
  AgentType,
  AgentStatus,
  ApiResponse,
} from './types';

export class AgentsService {
  private readonly baseUrl = '/api/v1/agents';

  /**
   * Get status of all agents
   */
  async getAllAgentStatus(): Promise<ApiResponse<AgentStatusModel[]>> {
    return apiClient.get<AgentStatusModel[]>(`${this.baseUrl}/status`);
  }

  /**
   * Get status of specific agent
   */
  async getAgentStatus(agentType: AgentType): Promise<ApiResponse<AgentStatusModel>> {
    return apiClient.get<AgentStatusModel>(`${this.baseUrl}/${agentType}/status`);
  }

  /**
   * Update agent status
   */
  async updateAgentStatus(
    agentType: AgentType,
    status: AgentStatus,
    taskId?: string,
    errorMessage?: string
  ): Promise<ApiResponse<AgentStatusModel>> {
    return apiClient.post<AgentStatusModel>(`${this.baseUrl}/${agentType}/status`, {
      status,
      current_task_id: taskId,
      error_message: errorMessage,
    });
  }

  /**
   * Get agent performance metrics
   */
  async getAgentMetrics(agentType: AgentType): Promise<ApiResponse<{
    agent_type: AgentType;
    tasks_completed: number;
    tasks_failed: number;
    average_task_duration: number;
    success_rate: number;
    last_activity: string;
  }>> {
    return apiClient.get(`${this.baseUrl}/${agentType}/metrics`);
  }

  /**
   * Get all agent performance metrics
   */
  async getAllAgentMetrics(): Promise<ApiResponse<{
    [agentType: string]: {
      agent_type: AgentType;
      tasks_completed: number;
      tasks_failed: number;
      average_task_duration: number;
      success_rate: number;
      last_activity: string;
    };
  }>> {
    return apiClient.get(`${this.baseUrl}/metrics`);
  }

  /**
   * Reset agent status (clear error state)
   */
  async resetAgent(agentType: AgentType): Promise<ApiResponse<AgentStatusModel>> {
    return apiClient.post<AgentStatusModel>(`${this.baseUrl}/${agentType}/reset`);
  }

  /**
   * Stop agent execution
   */
  async stopAgent(agentType: AgentType): Promise<ApiResponse<void>> {
    return apiClient.post<void>(`${this.baseUrl}/${agentType}/stop`);
  }

  /**
   * Get agent configuration
   */
  async getAgentConfig(agentType: AgentType): Promise<ApiResponse<{
    agent_type: AgentType;
    capabilities: string[];
    tools: string[];
    parameters: Record<string, any>;
    llm_provider: string;
    model: string;
  }>> {
    return apiClient.get(`${this.baseUrl}/${agentType}/config`);
  }

  /**
   * Update agent configuration
   */
  async updateAgentConfig(
    agentType: AgentType,
    config: {
      capabilities?: string[];
      tools?: string[];
      parameters?: Record<string, any>;
      llm_provider?: string;
      model?: string;
    }
  ): Promise<ApiResponse<void>> {
    return apiClient.put(`${this.baseUrl}/${agentType}/config`, config);
  }

  /**
   * Get agent activity history
   */
  async getAgentHistory(
    agentType: AgentType,
    limit: number = 50
  ): Promise<ApiResponse<{
    activities: Array<{
      timestamp: string;
      event: string;
      task_id?: string;
      status: AgentStatus;
      details?: Record<string, any>;
    }>;
    total: number;
  }>> {
    return apiClient.get(`${this.baseUrl}/${agentType}/history`, { limit });
  }

  /**
   * Check if agent is available for new tasks
   */
  async isAgentAvailable(agentType: AgentType): Promise<ApiResponse<{
    available: boolean;
    status: AgentStatus;
    current_task_id?: string;
    estimated_completion?: string;
  }>> {
    return apiClient.get(`${this.baseUrl}/${agentType}/availability`);
  }

  /**
   * Get real-time agent status summary for dashboard
   */
  async getAgentSummary(): Promise<{
    total_agents: number;
    active_agents: number;
    idle_agents: number;
    error_agents: number;
    agents: Record<AgentType, {
      status: AgentStatus;
      last_activity: string;
      current_task?: string;
      success_rate: number;
    }>;
  }> {
    try {
      const [statusResponse, metricsResponse] = await Promise.all([
        this.getAllAgentStatus(),
        this.getAllAgentMetrics(),
      ]);

      if (!statusResponse.success || !metricsResponse.success) {
        throw new Error('Failed to fetch agent data');
      }

      const statusData = statusResponse.data!;
      const metricsData = metricsResponse.data!;

      const agents: Record<AgentType, any> = {} as any;
      let active = 0, idle = 0, error = 0;

      statusData.forEach(agent => {
        const metrics = metricsData[agent.agent_type];

        agents[agent.agent_type] = {
          status: agent.status,
          last_activity: agent.last_activity,
          current_task: agent.current_task_id,
          success_rate: metrics?.success_rate || 0,
        };

        switch (agent.status) {
          case 'working':
          case 'waiting_for_hitl':
            active++;
            break;
          case 'idle':
            idle++;
            break;
          case 'error':
            error++;
            break;
        }
      });

      return {
        total_agents: statusData.length,
        active_agents: active,
        idle_agents: idle,
        error_agents: error,
        agents,
      };
    } catch (error) {
      console.error('Failed to get agent summary:', error);
      // Return default state
      return {
        total_agents: 6,
        active_agents: 0,
        idle_agents: 6,
        error_agents: 0,
        agents: {
          orchestrator: { status: 'idle', last_activity: new Date().toISOString(), success_rate: 0 },
          analyst: { status: 'idle', last_activity: new Date().toISOString(), success_rate: 0 },
          architect: { status: 'idle', last_activity: new Date().toISOString(), success_rate: 0 },
          coder: { status: 'idle', last_activity: new Date().toISOString(), success_rate: 0 },
          tester: { status: 'idle', last_activity: new Date().toISOString(), success_rate: 0 },
          deployer: { status: 'idle', last_activity: new Date().toISOString(), success_rate: 0 },
        },
      };
    }
  }
}

export const agentsService = new AgentsService();