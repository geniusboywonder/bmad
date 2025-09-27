/**
 * Artifacts Service - Backend Integration
 * Handles artifact fetching and management for projects
 */

import { apiClient } from './client';
import { ApiResponse } from './types';

export interface ArtifactSummary {
  project_id: string;
  project_name: string;
  artifact_count: number;
  generated_at: string;
  download_available: boolean;
  artifacts: ProjectArtifact[];
}

export interface ProjectArtifact {
  id: string;
  name: string;
  type: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  file_path?: string;
  size?: number;
  agent?: string;
}

export interface ArtifactGenerationRequest {
  force_regenerate?: boolean;
  include_source?: boolean;
}

export interface ArtifactGenerationResponse {
  message: string;
  project_id: string;
  status: string;
  artifact_count: number;
  generated_files: string[];
}

export class ArtifactsService {
  /**
   * Get artifact summary for a project
   */
  async getProjectArtifacts(projectId: string): Promise<ApiResponse<ArtifactSummary>> {
    return await apiClient.get<ArtifactSummary>(`/api/v1/artifacts/${projectId}/summary`);
  }

  /**
   * Generate artifacts for a project
   */
  async generateProjectArtifacts(
    projectId: string,
    options: ArtifactGenerationRequest = {}
  ): Promise<ApiResponse<ArtifactGenerationResponse>> {
    return await apiClient.post<ArtifactGenerationResponse>(`/api/v1/artifacts/${projectId}/generate`, options);
  }

  /**
   * Download project artifacts as ZIP
   */
  async downloadProjectArtifacts(projectId: string): Promise<ApiResponse<Blob>> {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/artifacts/${projectId}/download`);

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      const blob = await response.blob();
      return { success: true, data: blob };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to download project artifacts'
      };
    }
  }

  /**
   * Cleanup old artifacts (admin function)
   */
  async cleanupOldArtifacts(maxAgeHours: number = 24): Promise<ApiResponse<{ message: string }>> {
    return await apiClient.post<{ message: string }>('/api/v1/artifacts/cleanup-old', { max_age_hours: maxAgeHours });
  }
}

export const artifactsService = new ArtifactsService();