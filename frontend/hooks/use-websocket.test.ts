import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useWebSocket } from './use-websocket';
import { websocketService, type ConnectionStatus } from '../lib/websocket/websocket-service';

// Mock the websocketService
vi.mock('../lib/websocket/websocket-service', () => ({
  websocketService: {
    getConnectionStatus: vi.fn(),
    onStatusChange: vi.fn(),
    enableAutoConnect: vi.fn(),
    disconnect: vi.fn(),
    startProject: vi.fn(),
  },
}));

describe('useWebSocket Hook', () => {
  let mockStatusCallback: (status: ConnectionStatus) => void;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock the initial status
    (websocketService.getConnectionStatus as vi.Mock).mockReturnValue({
      connected: false,
      reconnecting: false,
    });

    // Mock the onStatusChange to capture the callback
    (websocketService.onStatusChange as vi.Mock).mockImplementation((callback) => {
      mockStatusCallback = callback;
      // Return a mock unsubscribe function
      return vi.fn();
    });
  });

  it('should return the initial connection status', () => {
    // Arrange & Act
    const { result } = renderHook(() => useWebSocket());

    // Assert
    expect(result.current.isConnected).toBe(false);
    expect(result.current.isReconnecting).toBe(false);
  });

  it('should subscribe to status changes and update its state', () => {
    // Arrange
    const { result } = renderHook(() => useWebSocket());

    // Assert initial state
    expect(result.current.isConnected).toBe(false);

    // Act: Simulate a status change from the service
    act(() => {
      mockStatusCallback({ connected: true, reconnecting: false });
    });

    // Assert updated state
    expect(result.current.isConnected).toBe(true);
    expect(result.current.isReconnecting).toBe(false);
  });

  it('should call enableAutoConnect on initial render if autoConnect is true', () => {
    // Arrange & Act
    renderHook(() => useWebSocket(true));

    // Assert
    expect(websocketService.enableAutoConnect).toHaveBeenCalledOnce();
  });

  it('should not call enableAutoConnect if autoConnect is false', () => {
    // Arrange & Act
    renderHook(() => useWebSocket(false));

    // Assert
    expect(websocketService.enableAutoConnect).not.toHaveBeenCalled();
  });

  it('should call disconnect on the service when its disconnect function is called', () => {
    // Arrange
    const { result } = renderHook(() => useWebSocket());

    // Act
    act(() => {
        result.current.disconnect();
    });

    // Assert
    expect(websocketService.disconnect).toHaveBeenCalledOnce();
  });
});
