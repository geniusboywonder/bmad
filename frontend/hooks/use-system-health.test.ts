import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useSystemHealth } from './use-system-health';
import { websocketService } from '@/lib/services/websocket/websocket-service';
import { useAgentStore } from '@/lib/stores/agent-store';
import { useLogStore } from '@/lib/stores/log-store';

// Mock the entire websocket service
vi.mock('@/lib/services/websocket/websocket-service', () => ({
  websocketService: {
    getConnectionStatus: vi.fn(),
    getMetrics: vi.fn(),
  },
}));

// Mock the Zustand stores
vi.mock('@/lib/stores/agent-store');
vi.mock('@/lib/stores/log-store');

// Mock global fetch
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('useSystemHealth Hook', () => {
  const mockGetSystemHealth = vi.fn();
  const mockGetRecentLogs = vi.fn();
  const mockGetErrorLogs = vi.fn();

  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();

    // Setup mock implementations for the stores
    (useAgentStore as vi.Mock).mockReturnValue({
        getSystemHealth: mockGetSystemHealth.mockReturnValue({ percentage: 100, total: 5, healthy: 5 }),
        agents: [{ id: '1', status: 'active' }],
    });

    (useLogStore as vi.Mock).mockReturnValue({
        getRecentLogs: mockGetRecentLogs.mockReturnValue([]),
        getErrorLogs: mockGetErrorLogs.mockReturnValue([]),
        metrics: { totalErrors: 0, totalLogs: 100 },
    });

    // Correctly mock the return value for getConnectionStatus
    (websocketService.getConnectionStatus as vi.Mock).mockReturnValue('connected');
    (websocketService.getMetrics as vi.Mock).mockReturnValue({ latency: 100, uptime: 99.9 });

    // Mock a successful fetch response for the backend health check
    mockFetch.mockImplementation(async (url: string) => {
        if (url.includes('/api/health')) {
            return {
                ok: true,
                json: async () => ({ status: 'healthy' }),
            };
        }
        return {
            ok: false,
            status: 404,
            statusText: 'Not Found'
        };
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should start monitoring automatically and perform an initial health check', async () => {
    // Arrange & Act
    const { result } = renderHook(() => useSystemHealth({ autoStart: true, services: ['backend'] }));

    // Assert
    await waitFor(() => {
      expect(result.current.isMonitoring).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith('/api/health', expect.any(Object));
      expect(result.current.health.overall).toBe('healthy');
      expect(result.current.health.services[0].status).toBe('healthy');
    });
  });

  it('should update health status based on service checks', async () => {
    // Arrange
    mockFetch.mockImplementationOnce(async (url: string) => {
        if (url.includes('/api/health')) {
            return {
                ok: false,
                status: 500,
                statusText: 'Internal Server Error',
                json: async () => ({})
            };
        }
        return { ok: false, status: 404, statusText: 'Not Found' };
    });

    (websocketService.getConnectionStatus as vi.Mock).mockReturnValue('disconnected');

    const { result } = renderHook(() => useSystemHealth({ autoStart: false, services: ['backend', 'websocket'] }));

    // Act
    act(() => {
        result.current.startMonitoring();
    });

    // Assert
    await waitFor(() => {
      expect(result.current.health.overall).toBe('unhealthy');
    });

    const backendService = result.current.health.services.find(s => s.name === 'Backend API');
    const wsService = result.current.health.services.find(s => s.name === 'WebSocket');

    expect(backendService?.status).toBe('unhealthy');
    expect(wsService?.status).toBe('unhealthy');
  });

  it('should perform health checks at the specified interval', async () => {
    // Arrange
    const { result } = renderHook(() => useSystemHealth({ autoStart: true, refreshInterval: 5000, services: ['backend'] }));

    // Assert initial check
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    // Act: Advance time to trigger the next interval
    act(() => {
      vi.advanceTimersByTime(5000);
    });

    // Assert next check
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });
});
