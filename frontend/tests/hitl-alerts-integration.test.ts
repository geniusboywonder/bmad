/**
 * HITL Alerts Bar Integration Tests
 * 
 * Tests the complete HITL alert lifecycle including:
 * - Alert creation and display
 * - Navigation to HITL messages
 * - Approval/rejection workflows
 * - Error handling for expired/stale requests
 * - Store cleanup after resolution
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useHITLStore } from '@/lib/stores/hitl-store';
import { useProjectStore } from '@/lib/stores/project-store';
import { useNavigationStore } from '@/lib/stores/navigation-store';

// Mock fetch for API calls
global.fetch = vi.fn();

describe('HITL Alerts Bar Integration Tests', () => {
  beforeEach(() => {
    // Clear all stores before each test
    useHITLStore.getState().clearAllRequests();
    vi.clearAllMocks();
    
    // Reset fetch mock
    (global.fetch as any).mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Alert Lifecycle Management', () => {
    it('should add HITL request and display in alerts bar', () => {
      const { result } = renderHook(() => useHITLStore());

      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Requires approval',
          context: {
            projectId: 'test-project-123',
            taskId: 'test-task-456',
            approvalId: 'test-approval-789'
          },
          priority: 'high'
        });
      });

      expect(result.current.requests).toHaveLength(1);
      expect(result.current.requests[0].status).toBe('pending');
      expect(result.current.getPendingCount()).toBe(1);
    });

    it('should successfully resolve HITL request with backend API call', async () => {
      const { result } = renderHook(() => useHITLStore());
      
      // Mock successful API response
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          approval_id: 'test-approval-789',
          status: 'APPROVED',
          message: 'Agent execution approved'
        })
      });

      // Add request
      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Requires approval',
          context: {
            projectId: 'test-project-123',
            taskId: 'test-task-456',
            approvalId: 'test-approval-789'
          },
          priority: 'high'
        });
      });

      const requestId = result.current.requests[0].id;

      // Resolve request
      await act(async () => {
        await result.current.resolveRequest(requestId, 'approved', 'Test approval');
      });

      // Wait for state update
      await waitFor(() => {
        expect(result.current.requests).toHaveLength(0);
      });

      // Verify API was called correctly
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/hitl-safety/approve-agent-execution/test-approval-789',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('"approved":true')
        })
      );
    });

    it('should handle 404 error for expired/missing approval gracefully', async () => {
      const { result } = renderHook(() => useHITLStore());
      
      // Mock 404 response
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => 'Approval request not found'
      });

      // Add request
      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Requires approval',
          context: {
            projectId: 'test-project-123',
            taskId: 'test-task-456',
            approvalId: 'expired-approval-123'
          },
          priority: 'high'
        });
      });

      const requestId = result.current.requests[0].id;

      // Resolve request (should handle 404 gracefully)
      await act(async () => {
        await result.current.resolveRequest(requestId, 'approved', 'Test approval');
      });

      // Wait for state update - request should be removed even with 404
      await waitFor(() => {
        expect(result.current.requests).toHaveLength(0);
      });
    });

    it('should handle 400 error for already processed approval gracefully', async () => {
      const { result } = renderHook(() => useHITLStore());
      
      // Mock 400 response for already processed
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () => 'Approval request is not pending (current status: APPROVED)'
      });

      // Add request
      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Requires approval',
          context: {
            projectId: 'test-project-123',
            taskId: 'test-task-456',
            approvalId: 'processed-approval-456'
          },
          priority: 'high'
        });
      });

      const requestId = result.current.requests[0].id;

      // Resolve request (should handle 400 gracefully for already processed)
      await act(async () => {
        await result.current.resolveRequest(requestId, 'approved', 'Test approval');
      });

      // Wait for state update - request should be removed
      await waitFor(() => {
        expect(result.current.requests).toHaveLength(0);
      });
    });

    it('should auto-remove expired requests older than 30 minutes', () => {
      const { result } = renderHook(() => useHITLStore());

      // Add old request (31 minutes ago)
      const oldTimestamp = new Date(Date.now() - 31 * 60 * 1000);
      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Requires approval',
          context: {
            projectId: 'test-project-123',
            taskId: 'test-task-456',
            approvalId: 'old-approval-789'
          },
          priority: 'high'
        });
        
        // Manually set old timestamp
        const store = useHITLStore.getState();
        store.requests[0].timestamp = oldTimestamp;
      });

      // Run cleanup
      act(() => {
        result.current.removeExpiredRequests();
      });

      expect(result.current.requests).toHaveLength(0);
    });
  });

  describe('Navigation and Alert Bar Integration', () => {
    it('should navigate to project when clicking HITL alert', async () => {
      const { result: hitlStore } = renderHook(() => useHITLStore());
      const { result: navStore } = renderHook(() => useNavigationStore());
      const { result: projectStore } = renderHook(() => useProjectStore());

      // Add mock project
      act(() => {
        projectStore.current.setCurrentProject({
          id: 'test-project-123',
          name: 'Test Project',
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        } as any);
      });

      // Add HITL request
      act(() => {
        hitlStore.current.addRequest({
          agentName: 'Analyst',
          decision: 'Requires approval',
          context: {
            projectId: 'test-project-123',
            taskId: 'test-task-456',
            approvalId: 'test-approval-789'
          },
          priority: 'high'
        });
      });

      const requestId = hitlStore.current.requests[0].id;

      // Navigate to request
      act(() => {
        hitlStore.current.navigateToRequest(requestId);
      });

      expect(hitlStore.current.activeRequest?.id).toBe(requestId);
    });

    it('should filter pending requests correctly', () => {
      const { result } = renderHook(() => useHITLStore());

      // Add multiple requests with different statuses
      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Requires approval',
          context: { projectId: '1', approvalId: 'a1' },
          priority: 'high'
        });
        result.current.addRequest({
          agentName: 'Architect',
          decision: 'Requires approval',
          context: { projectId: '1', approvalId: 'a2' },
          priority: 'medium'
        });
      });

      expect(result.current.getPendingCount()).toBe(2);

      // Mock resolve one request
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'APPROVED' })
      });

      // Resolve first request
      const firstRequestId = result.current.requests[0].id;
      act(async () => {
        await result.current.resolveRequest(firstRequestId, 'approved');
      });

      // Should have only 1 pending request now
      waitFor(() => {
        expect(result.current.getPendingCount()).toBe(1);
      });
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle missing approval ID gracefully', async () => {
      const { result } = renderHook(() => useHITLStore());

      // Add request without approval ID
      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Requires approval',
          context: {
            projectId: 'test-project-123',
            taskId: 'test-task-456'
            // No approvalId
          },
          priority: 'high'
        });
      });

      const requestId = result.current.requests[0].id;

      // Try to resolve (should handle gracefully without API call)
      await act(async () => {
        await result.current.resolveRequest(requestId, 'approved');
      });

      // Should still remove from store
      await waitFor(() => {
        expect(result.current.requests).toHaveLength(0);
      });

      // API should not have been called
      expect(global.fetch).not.toHaveBeenCalled();
    });

    it('should handle network errors during resolution', async () => {
      const { result } = renderHook(() => useHITLStore());

      // Mock network error
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Requires approval',
          context: {
            projectId: 'test-project-123',
            approvalId: 'test-approval-789'
          },
          priority: 'high'
        });
      });

      const requestId = result.current.requests[0].id;

      // Try to resolve (should throw)
      await expect(async () => {
        await act(async () => {
          await result.current.resolveRequest(requestId, 'approved');
        });
      }).rejects.toThrow('Network error');

      // Request should still be in store
      expect(result.current.requests).toHaveLength(1);
    });

    it('should handle 500 internal server errors', async () => {
      const { result } = renderHook(() => useHITLStore());

      // Mock 500 response
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'Database connection failed'
      });

      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Requires approval',
          context: {
            projectId: 'test-project-123',
            approvalId: 'test-approval-789'
          },
          priority: 'high'
        });
      });

      const requestId = result.current.requests[0].id;

      // Try to resolve (should throw)
      await expect(async () => {
        await act(async () => {
          await result.current.resolveRequest(requestId, 'approved');
        });
      }).rejects.toThrow('API call failed');

      // Request should still be in store for 500 errors
      expect(result.current.requests).toHaveLength(1);
    });
  });

  describe('Store Cleanup Methods', () => {
    it('should clear all requests', () => {
      const { result } = renderHook(() => useHITLStore());

      // Add multiple requests
      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Test 1',
          context: {},
          priority: 'high'
        });
        result.current.addRequest({
          agentName: 'Architect',
          decision: 'Test 2',
          context: {},
          priority: 'medium'
        });
      });

      expect(result.current.requests).toHaveLength(2);

      // Clear all
      act(() => {
        result.current.clearAllRequests();
      });

      expect(result.current.requests).toHaveLength(0);
      expect(result.current.activeRequest).toBeNull();
    });

    it('should remove only resolved requests', async () => {
      const { result } = renderHook(() => useHITLStore());

      // Mock successful API
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'APPROVED' })
      });

      // Add requests
      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Test 1',
          context: { approvalId: 'a1' },
          priority: 'high'
        });
        result.current.addRequest({
          agentName: 'Architect',
          decision: 'Test 2',
          context: { approvalId: 'a2' },
          priority: 'medium'
        });
      });

      // Resolve first request
      const firstId = result.current.requests[0].id;
      await act(async () => {
        await result.current.resolveRequest(firstId, 'approved');
      });

      // Should have 1 pending request remaining
      await waitFor(() => {
        expect(result.current.requests).toHaveLength(1);
        expect(result.current.getPendingCount()).toBe(1);
      });
    });
  });

  describe('localStorage Persistence', () => {
    it('should persist requests to localStorage', () => {
      const { result } = renderHook(() => useHITLStore());

      act(() => {
        result.current.addRequest({
          agentName: 'Analyst',
          decision: 'Test persistence',
          context: { projectId: 'test-123' },
          priority: 'high'
        });
      });

      // Check localStorage
      const stored = localStorage.getItem('hitl-store');
      expect(stored).toBeTruthy();
      
      const parsed = JSON.parse(stored!);
      expect(parsed.state.requests).toHaveLength(1);
      expect(parsed.state.requests[0].agentName).toBe('Analyst');
    });

    it('should handle localStorage quota exceeded gracefully', () => {
      const { result } = renderHook(() => useHITLStore());

      // Mock localStorage setItem to throw quota exceeded error
      const originalSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = vi.fn(() => {
        const error = new DOMException('QuotaExceededError');
        (error as any).code = 22;
        throw error;
      });

      // Should not throw even with quota error
      expect(() => {
        act(() => {
          result.current.addRequest({
            agentName: 'Analyst',
            decision: 'Test quota',
            context: {},
            priority: 'high'
          });
        });
      }).not.toThrow();

      // Restore original
      Storage.prototype.setItem = originalSetItem;
    });
  });
});
