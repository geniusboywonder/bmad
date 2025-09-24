/**
 * Projects Service - Project lifecycle operations
 * Handles project creation, status tracking, and task management
 */

import { apiClient } from './client';
import {
  Project,
  CreateProjectRequest,
  ProjectStatusResponse,
  CreateTaskRequest,
  CreateTaskResponse,
  Task,
  ApiResponse,
} from './types';

export class ProjectsService {
  private readonly baseUrl = '/api/v1/projects';

  /**
   * Create a new project
   */
  async createProject(data: CreateProjectRequest): Promise<ApiResponse<Project>> {
    return apiClient.post<Project>(this.baseUrl, data);
  }

  /**
   * Get all projects
   */
  async getProjects(): Promise<ApiResponse<Project[]>> {
    return apiClient.get<Project[]>(this.baseUrl);
  }

  /**
   * Get project by ID
   */
  async getProject(projectId: string): Promise<ApiResponse<Project>> {
    return apiClient.get<Project>(`${this.baseUrl}/${projectId}`);
  }

  /**
   * Update project
   */
  async updateProject(
    projectId: string,
    data: Partial<CreateProjectRequest>
  ): Promise<ApiResponse<Project>> {
    return apiClient.put<Project>(`${this.baseUrl}/${projectId}`, data);
  }

  /**
   * Delete project
   */
  async deleteProject(projectId: string): Promise<ApiResponse<void>> {
    return apiClient.delete<void>(`${this.baseUrl}/${projectId}`);
  }

  /**
   * Get project status with all tasks
   */
  async getProjectStatus(projectId: string): Promise<ApiResponse<ProjectStatusResponse>> {
    return apiClient.get<ProjectStatusResponse>(`${this.baseUrl}/${projectId}/status`);
  }

  /**
   * Create a new task for a project
   */
  async createTask(
    projectId: string,
    data: CreateTaskRequest
  ): Promise<ApiResponse<CreateTaskResponse>> {
    return apiClient.post<CreateTaskResponse>(`${this.baseUrl}/${projectId}/tasks`, data);
  }

  /**
   * Get all tasks for a project
   */
  async getProjectTasks(projectId: string): Promise<ApiResponse<Task[]>> {
    return apiClient.get<Task[]>(`${this.baseUrl}/${projectId}/tasks`);
  }

  /**
   * Get specific task details
   */
  async getTask(projectId: string, taskId: string): Promise<ApiResponse<Task>> {
    return apiClient.get<Task>(`${this.baseUrl}/${projectId}/tasks/${taskId}`);
  }

  /**
   * Update task status or details
   */
  async updateTask(
    projectId: string,
    taskId: string,
    data: Partial<Task>
  ): Promise<ApiResponse<Task>> {
    return apiClient.put<Task>(`${this.baseUrl}/${projectId}/tasks/${taskId}`, data);
  }

  /**
   * Cancel a task
   */
  async cancelTask(projectId: string, taskId: string): Promise<ApiResponse<void>> {
    return apiClient.delete<void>(`${this.baseUrl}/${projectId}/tasks/${taskId}`);
  }

  /**
   * Start project execution
   */
  async startProject(projectId: string, brief?: string): Promise<ApiResponse<void>> {
    return apiClient.post<void>(`${this.baseUrl}/${projectId}/start`, { brief });
  }

  /**
   * Pause project execution
   */
  async pauseProject(projectId: string): Promise<ApiResponse<void>> {
    return apiClient.post<void>(`${this.baseUrl}/${projectId}/pause`);
  }

  /**
   * Resume project execution
   */
  async resumeProject(projectId: string): Promise<ApiResponse<void>> {
    return apiClient.post<void>(`${this.baseUrl}/${projectId}/resume`);
  }

  /**
   * Complete project
   */
  async completeProject(projectId: string): Promise<ApiResponse<void>> {
    return apiClient.post<void>(`${this.baseUrl}/${projectId}/complete`);
  }
}

export const projectsService = new ProjectsService();