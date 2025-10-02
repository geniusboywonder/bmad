/**
 * Workflows Service - Workflow definition and deliverables operations
 * Handles fetching workflow definitions and expected deliverables
 */

import { apiClient } from './client';
import { ApiResponse } from './types';

export interface WorkflowDeliverable {
  name: string;
  agent: string;
  description: string;
  optional: boolean;
}

export interface WorkflowDeliverablesResponse {
  workflow_id: string;
  workflow_name: string;
  deliverables: {
    analyze: WorkflowDeliverable[];
    design: WorkflowDeliverable[];
    build: WorkflowDeliverable[];
    validate: WorkflowDeliverable[];
    launch: WorkflowDeliverable[];
  };
}

export class WorkflowsService {
  private readonly baseUrl = '/api/v1/workflows';

  /**
   * Get expected deliverables for a workflow
   */
  async getWorkflowDeliverables(
    workflowId: string
  ): Promise<ApiResponse<WorkflowDeliverablesResponse>> {
    return apiClient.get<WorkflowDeliverablesResponse>(
      `${this.baseUrl}/${workflowId}/deliverables`
    );
  }
}

export const workflowsService = new WorkflowsService();
