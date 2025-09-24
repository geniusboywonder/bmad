/**
 * HITL Service - Human-in-the-Loop approval workflows
 * Handles HITL requests, responses, and safety controls
 */

import { apiClient } from './client';
import {
  HitlRequest,
  HitlRequestResponse,
  HitlResponse,
  HitlAction,
  HitlAgentApproval,
  EmergencyStop,
  ApiResponse,
} from './types';

export class HITLService {
  private readonly baseUrl = '/api/v1/hitl';
  private readonly safetyUrl = '/api/v1/hitl-safety';

  /**
   * Get all HITL requests for a project
   */
  async getProjectRequests(projectId: string): Promise<ApiResponse<HitlRequestResponse[]>> {
    return apiClient.get<HitlRequestResponse[]>(`${this.baseUrl}/project/${projectId}`);
  }

  /**
   * Get specific HITL request
   */
  async getRequest(requestId: string): Promise<ApiResponse<HitlRequestResponse>> {
    return apiClient.get<HitlRequestResponse>(`${this.baseUrl}/requests/${requestId}`);
  }

  /**
   * Respond to HITL request
   */
  async respondToRequest(
    requestId: string,
    response: {
      action: HitlAction;
      response?: string;
      amended_content?: Record<string, any>;
      comment?: string;
    }
  ): Promise<ApiResponse<{ status: string; message: string }>> {
    return apiClient.post(`${this.baseUrl}/requests/${requestId}/respond`, response);
  }

  /**
   * Get all pending HITL requests across all projects
   */
  async getPendingRequests(): Promise<ApiResponse<HitlRequestResponse[]>> {
    return apiClient.get<HitlRequestResponse[]>(`${this.baseUrl}/pending`);
  }

  /**
   * Get HITL request history
   */
  async getRequestHistory(
    projectId?: string,
    limit: number = 50
  ): Promise<ApiResponse<HitlRequestResponse[]>> {
    const params = projectId ? { project_id: projectId, limit } : { limit };
    return apiClient.get<HitlRequestResponse[]>(`${this.baseUrl}/history`, params);
  }

  /**
   * Cancel/expire a HITL request
   */
  async cancelRequest(requestId: string): Promise<ApiResponse<void>> {
    return apiClient.delete<void>(`${this.baseUrl}/requests/${requestId}`);
  }

  /**
   * Update HITL request (extend deadline, change priority, etc.)
   */
  async updateRequest(
    requestId: string,
    updates: {
      expires_at?: string;
      question?: string;
      options?: string[];
    }
  ): Promise<ApiResponse<HitlRequestResponse>> {
    return apiClient.patch<HitlRequestResponse>(`${this.baseUrl}/requests/${requestId}`, updates);
  }

  // HITL Safety Controls

  /**
   * Get all agent approval requests
   */
  async getAgentApprovals(projectId?: string): Promise<ApiResponse<HitlAgentApproval[]>> {
    const params = projectId ? { project_id: projectId } : {};
    return apiClient.get<HitlAgentApproval[]>(`${this.safetyUrl}/approvals`, params);
  }

  /**
   * Approve agent execution
   */
  async approveAgentExecution(
    approvalId: string,
    approved: boolean,
    comment?: string
  ): Promise<ApiResponse<void>> {
    return apiClient.post(`${this.safetyUrl}/approvals/${approvalId}/approve`, {
      approved,
      comment,
    });
  }

  /**
   * Get budget controls for a project
   */
  async getBudgetControls(projectId: string): Promise<ApiResponse<{
    project_id: string;
    daily_token_limit: number;
    session_token_limit: number;
    current_daily_usage: number;
    current_session_usage: number;
    budget_exceeded: boolean;
    emergency_stop_threshold: number;
  }>> {
    return apiClient.get(`${this.safetyUrl}/budget/${projectId}`);
  }

  /**
   * Update budget controls
   */
  async updateBudgetControls(
    projectId: string,
    controls: {
      daily_token_limit?: number;
      session_token_limit?: number;
      emergency_stop_threshold?: number;
    }
  ): Promise<ApiResponse<void>> {
    return apiClient.put(`${this.safetyUrl}/budget/${projectId}`, controls);
  }

  /**
   * Trigger emergency stop
   */
  async triggerEmergencyStop(
    projectId: string,
    reason: string
  ): Promise<ApiResponse<EmergencyStop>> {
    return apiClient.post<EmergencyStop>(`${this.safetyUrl}/emergency-stop`, {
      project_id: projectId,
      reason,
    });
  }

  /**
   * Get emergency stops for a project
   */
  async getEmergencyStops(projectId: string): Promise<ApiResponse<EmergencyStop[]>> {
    return apiClient.get<EmergencyStop[]>(`${this.safetyUrl}/emergency-stops/${projectId}`);
  }

  /**
   * Resolve emergency stop
   */
  async resolveEmergencyStop(
    stopId: string,
    resolution: string
  ): Promise<ApiResponse<void>> {
    return apiClient.post(`${this.safetyUrl}/emergency-stops/${stopId}/resolve`, {
      resolution,
    });
  }

  /**
   * Get safety system status
   */
  async getSafetyStatus(): Promise<ApiResponse<{
    safety_controls_active: boolean;
    total_approvals_pending: number;
    emergency_stops_active: number;
    budget_violations: number;
    last_safety_check: string;
  }>> {
    return apiClient.get(`${this.safetyUrl}/status`);
  }

  /**
   * Configure HITL triggers for a project
   */
  async configureHITLTriggers(
    projectId: string,
    config: {
      oversight_level: 'low' | 'medium' | 'high';
      auto_approve_threshold: number;
      require_approval_for: string[];
      emergency_contact: string;
    }
  ): Promise<ApiResponse<void>> {
    return apiClient.put(`${this.safetyUrl}/configure/${projectId}`, config);
  }

  /**
   * Get HITL configuration for a project
   */
  async getHITLConfiguration(projectId: string): Promise<ApiResponse<{
    project_id: string;
    oversight_level: 'low' | 'medium' | 'high';
    auto_approve_threshold: number;
    require_approval_for: string[];
    emergency_contact: string;
    last_updated: string;
  }>> {
    return apiClient.get(`${this.safetyUrl}/configure/${projectId}`);
  }

  /**
   * Get HITL dashboard summary
   */
  async getHITLSummary(): Promise<{
    pending_requests: number;
    pending_approvals: number;
    active_emergency_stops: number;
    budget_violations: number;
    average_response_time_minutes: number;
    requests_by_priority: {
      low: number;
      medium: number;
      high: number;
    };
  }> {
    try {
      const [requests, approvals, emergencyStops, safetyStatus] = await Promise.allSettled([
        this.getPendingRequests(),
        this.getAgentApprovals(),
        this.getSafetyStatus(),
        this.getRequestHistory(undefined, 100),
      ]);

      const pendingRequests = requests.status === 'fulfilled' && requests.value.success
        ? requests.value.data!.length : 0;

      const pendingApprovals = approvals.status === 'fulfilled' && approvals.value.success
        ? approvals.value.data!.filter(a => a.status === 'PENDING').length : 0;

      let activeEmergencyStops = 0;
      let budgetViolations = 0;

      if (emergencyStops.status === 'fulfilled' && emergencyStops.value.success) {
        const safety = emergencyStops.value.data!;
        activeEmergencyStops = safety.emergency_stops_active;
        budgetViolations = safety.budget_violations;
      }

      // Calculate average response time and priority distribution
      let averageResponseTime = 0;
      const priorityCount = { low: 0, medium: 0, high: 0 };

      if (safetyStatus.status === 'fulfilled' && safetyStatus.value.success) {
        const history = safetyStatus.value.data!;
        // This would need to be calculated from actual response times
        // For now, return a placeholder
        averageResponseTime = 15; // 15 minutes average
      }

      return {
        pending_requests: pendingRequests,
        pending_approvals: pendingApprovals,
        active_emergency_stops: activeEmergencyStops,
        budget_violations: budgetViolations,
        average_response_time_minutes: averageResponseTime,
        requests_by_priority: priorityCount,
      };
    } catch (error) {
      console.error('Failed to get HITL summary:', error);
      return {
        pending_requests: 0,
        pending_approvals: 0,
        active_emergency_stops: 0,
        budget_violations: 0,
        average_response_time_minutes: 0,
        requests_by_priority: { low: 0, medium: 0, high: 0 },
      };
    }
  }
}

export const hitlService = new HITLService();