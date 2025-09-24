/**
 * Health Service - System health monitoring
 * Handles health checks, system status, and component monitoring
 */

import { apiClient } from './client';
import { SystemHealth, ApiResponse } from './types';

export class HealthService {
  private readonly baseUrl = '/health';

  /**
   * Get basic health status
   */
  async getHealth(): Promise<ApiResponse<{ status: string }>> {
    return apiClient.get<{ status: string }>(this.baseUrl);
  }

  /**
   * Get detailed health status with component information
   */
  async getDetailedHealth(): Promise<ApiResponse<SystemHealth>> {
    return apiClient.get<SystemHealth>(`${this.baseUrl}/detailed`);
  }

  /**
   * Get health status for Kubernetes/container orchestration
   */
  async getHealthZ(): Promise<ApiResponse<{ status: string }>> {
    return apiClient.get<{ status: string }>(`${this.baseUrl}/z`);
  }

  /**
   * Get readiness status
   */
  async getReadiness(): Promise<ApiResponse<{ status: string; ready: boolean }>> {
    return apiClient.get<{ status: string; ready: boolean }>(`${this.baseUrl}/ready`);
  }

  /**
   * Get liveness status
   */
  async getLiveness(): Promise<ApiResponse<{ status: string; alive: boolean }>> {
    return apiClient.get<{ status: string; alive: boolean }>(`${this.baseUrl}/live`);
  }

  /**
   * Check database connectivity
   */
  async checkDatabase(): Promise<ApiResponse<{
    status: string;
    connected: boolean;
    latency_ms?: number
  }>> {
    return apiClient.get(`${this.baseUrl}/database`);
  }

  /**
   * Check Redis connectivity
   */
  async checkRedis(): Promise<ApiResponse<{
    status: string;
    connected: boolean;
    latency_ms?: number
  }>> {
    return apiClient.get(`${this.baseUrl}/redis`);
  }

  /**
   * Check Celery worker status
   */
  async checkCelery(): Promise<ApiResponse<{
    status: string;
    workers_active: number;
    queue_length: number
  }>> {
    return apiClient.get(`${this.baseUrl}/celery`);
  }

  /**
   * Check LLM provider connectivity
   */
  async checkLLMProviders(): Promise<ApiResponse<{
    status: string;
    providers: {
      openai: string;
      anthropic: string;
      google: string;
    };
  }>> {
    return apiClient.get(`${this.baseUrl}/llm-providers`);
  }

  /**
   * Check HITL safety system status
   */
  async checkHITLSafety(): Promise<ApiResponse<{
    status: string;
    safety_controls_active: boolean;
    emergency_stops_count: number;
    pending_approvals: number;
  }>> {
    return apiClient.get(`${this.baseUrl}/hitl-safety`);
  }

  /**
   * Get system metrics
   */
  async getMetrics(): Promise<ApiResponse<{
    uptime_seconds: number;
    memory_usage_mb: number;
    cpu_usage_percent: number;
    active_connections: number;
    requests_per_minute: number;
  }>> {
    return apiClient.get(`${this.baseUrl}/metrics`);
  }

  /**
   * Check all components and return comprehensive status
   */
  async checkAllComponents(): Promise<{
    overall: SystemHealth;
    components: {
      database: ApiResponse<any>;
      redis: ApiResponse<any>;
      celery: ApiResponse<any>;
      llm_providers: ApiResponse<any>;
      hitl_safety: ApiResponse<any>;
    };
  }> {
    try {
      // Run all health checks in parallel
      const [overall, database, redis, celery, llm_providers, hitl_safety] = await Promise.allSettled([
        this.getDetailedHealth(),
        this.checkDatabase(),
        this.checkRedis(),
        this.checkCelery(),
        this.checkLLMProviders(),
        this.checkHITLSafety(),
      ]);

      return {
        overall: overall.status === 'fulfilled' ? overall.value.data! : {
          status: 'unhealthy',
          timestamp: new Date().toISOString(),
          components: {
            database: 'unhealthy',
            redis: 'unhealthy',
            celery: 'unhealthy',
            llm_providers: 'unhealthy',
            hitl_safety: 'unhealthy',
          }
        },
        components: {
          database: database.status === 'fulfilled' ? database.value : { success: false, error: { code: 'HEALTH_CHECK_FAILED', message: 'Database health check failed' }, timestamp: new Date().toISOString() },
          redis: redis.status === 'fulfilled' ? redis.value : { success: false, error: { code: 'HEALTH_CHECK_FAILED', message: 'Redis health check failed' }, timestamp: new Date().toISOString() },
          celery: celery.status === 'fulfilled' ? celery.value : { success: false, error: { code: 'HEALTH_CHECK_FAILED', message: 'Celery health check failed' }, timestamp: new Date().toISOString() },
          llm_providers: llm_providers.status === 'fulfilled' ? llm_providers.value : { success: false, error: { code: 'HEALTH_CHECK_FAILED', message: 'LLM providers health check failed' }, timestamp: new Date().toISOString() },
          hitl_safety: hitl_safety.status === 'fulfilled' ? hitl_safety.value : { success: false, error: { code: 'HEALTH_CHECK_FAILED', message: 'HITL safety health check failed' }, timestamp: new Date().toISOString() },
        },
      };
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  /**
   * Get simplified health status for UI components
   */
  async getSimpleStatus(): Promise<{
    overall: 'healthy' | 'degraded' | 'unhealthy';
    backend: 'connected' | 'disconnected' | 'error';
    database: 'connected' | 'disconnected' | 'error';
    lastChecked: string;
  }> {
    try {
      const healthResponse = await this.getDetailedHealth();

      if (!healthResponse.success) {
        return {
          overall: 'unhealthy',
          backend: 'disconnected',
          database: 'disconnected',
          lastChecked: new Date().toISOString(),
        };
      }

      const health = healthResponse.data!;

      return {
        overall: health.status,
        backend: health.status === 'unhealthy' ? 'error' : 'connected',
        database: health.components.database === 'unhealthy' ? 'error' : 'connected',
        lastChecked: health.timestamp,
      };
    } catch (error) {
      console.error('Simple health check failed:', error);
      return {
        overall: 'unhealthy',
        backend: 'error',
        database: 'error',
        lastChecked: new Date().toISOString(),
      };
    }
  }
}

export const healthService = new HealthService();