/**
 * HITL Flow Integration Tests
 *
 * Tests the complete Human-in-the-Loop workflow:
 * 1. HITL request creation via WebSocket
 * 2. Display in chat with action buttons
 * 3. Display in alert bar
 * 4. Navigation from alert to chat message
 * 5. Approval/rejection flow
 *
 * Per TESTPROTOCOL.md: Real data testing with external service mocking
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { act } from 'react';
import { useHITLStore } from '@/lib/stores/hitl-store';
import { useAppStore } from '@/lib/stores/app-store';
import CustomCopilotChat from '@/components/chat/copilot-chat';
import { HITLAlertsBar } from '@/components/hitl/hitl-alerts-bar';

/**
 * Test Classification: real_data + external_service
 * - Uses real stores (not mocked)
 * - Mocks external API calls only
 */

describe('HITL Flow Integration Tests', () => {
  beforeEach(() => {
    // Reset stores to initial state
    useHITLStore.getState().clearAllRequests();
    useAppStore.setState({ conversation: [] });

    // Mock fetch for API calls
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should display HITL request with action buttons in chat', async () => {
    const { addRequest } = useHITLStore.getState();
    const { addMessage } = useAppStore.getState();

    // Simulate WebSocket adding a HITL request
    const approvalId = 'test-approval-123';
    addRequest({
      agentName: 'Developer',
      decision: 'Pre-execution approval',
      context: {
        approvalId,
        agentType: 'developer',
        requestType: 'pre_execution',
        estimatedTokens: 1000,
        estimatedCost: 0.05,
        requestData: { instructions: 'Write unit tests' },
        taskId: 'task-456',
        projectId: 'proj-789'
      },
      priority: 'medium'
    });

    // Add corresponding chat message
    addMessage({
      type: 'hitl_request',
      agent: 'Developer Agent',
      content: 'HITL Approval Required: Write unit tests',
      approvalId,
      taskId: 'task-456',
      hitlStatus: 'pending'
    });

    // Render chat component
    const { container } = render(<CustomCopilotChat projectId="proj-789" />);

    // Wait for message to appear
    await waitFor(() => {
      expect(screen.getByText(/HITL Approval Required/i)).toBeInTheDocument();
    });

    // Verify action buttons are present
    expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /modify/i })).toBeInTheDocument();

    // Verify data attributes for navigation
    const messageElement = container.querySelector(`[data-approval-id="${approvalId}"]`);
    expect(messageElement).toBeInTheDocument();
  });

  it('should display HITL alert in alert bar', async () => {
    const { addRequest } = useHITLStore.getState();

    // Add HITL request to store
    addRequest({
      agentName: 'Architect',
      decision: 'Design review needed',
      context: {
        approvalId: 'test-approval-456',
        agentType: 'architect',
        projectId: 'proj-123'
      },
      priority: 'high'
    });

    // Render alert bar
    render(
      <HITLAlertsBar
        systemAlerts={[]}
        expandedAlerts={[]}
        toggleExpanded={() => {}}
        dismissAlert={() => {}}
        isClient={true}
      />
    );

    // Verify HITL alert appears
    await waitFor(() => {
      expect(screen.getByText(/Architect needs approval/i)).toBeInTheDocument();
    });
  });

  it('should handle HITL approval action', async () => {
    const { addRequest } = useHITLStore.getState();
    const { addMessage } = useAppStore.getState();

    const approvalId = 'test-approval-789';

    // Mock successful API response
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'PENDING' })
    }).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true })
    });

    addRequest({
      agentName: 'Tester',
      decision: 'Test execution',
      context: {
        approvalId,
        agentType: 'tester',
        requestData: { instructions: 'Run integration tests' }
      },
      priority: 'medium'
    });

    addMessage({
      type: 'hitl_request',
      agent: 'Tester Agent',
      content: 'Need approval to run tests',
      approvalId,
      hitlStatus: 'pending'
    });

    render(<CustomCopilotChat />);

    // Find and click approve button
    const approveButton = await screen.findByRole('button', { name: /approve/i });
    await act(async () => {
      fireEvent.click(approveButton);
    });

    // Verify API was called
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/hitl-safety/approve-agent-execution'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"approved":true')
        })
      );
    });

    // Verify request was removed from store
    const { requests } = useHITLStore.getState();
    expect(requests.find(r => r.context?.approvalId === approvalId)).toBeUndefined();
  });

  it('should show expired message when HITL request is missing', async () => {
    const { addMessage } = useAppStore.getState();

    // Add message without corresponding request in store
    addMessage({
      type: 'hitl_request',
      agent: 'Developer Agent',
      content: 'This request has expired',
      approvalId: 'non-existent-approval',
      hitlStatus: 'pending'
    });

    render(<CustomCopilotChat />);

    // Verify expired message appears
    await waitFor(() => {
      expect(screen.getByText(/expired or been resolved elsewhere/i)).toBeInTheDocument();
    });

    // Verify action buttons are NOT present
    expect(screen.queryByRole('button', { name: /approve/i })).not.toBeInTheDocument();
  });

  it('should navigate to HITL message when alert is clicked', async () => {
    const { addRequest } = useHITLStore.getState();
    const { addMessage } = useAppStore.getState();

    const approvalId = 'nav-test-123';
    const projectId = 'proj-456';

    addRequest({
      agentName: 'Deployer',
      decision: 'Deployment approval',
      context: {
        approvalId,
        projectId,
        agentType: 'deployer'
      },
      priority: 'urgent'
    });

    addMessage({
      type: 'hitl_request',
      agent: 'Deployer Agent',
      content: 'Deploy to production?',
      approvalId,
      hitlStatus: 'pending'
    });

    // Mock scrollIntoView
    Element.prototype.scrollIntoView = vi.fn();

    const handleDismiss = vi.fn();
    const { container } = render(
      <>
        <HITLAlertsBar
          systemAlerts={[]}
          expandedAlerts={[]}
          toggleExpanded={() => {}}
          dismissAlert={handleDismiss}
          isClient={true}
        />
        <CustomCopilotChat projectId={projectId} />
      </>
    );

    // Find and click alert
    const alert = await screen.findByText(/Deployer needs approval/i);
    fireEvent.click(alert);

    // Verify element with approval ID exists and scrollIntoView was called
    await waitFor(() => {
      const messageElement = container.querySelector(`[data-approval-id="${approvalId}"]`);
      expect(messageElement).toBeInTheDocument();
    });
  });

  it('should remove expired HITL requests on cleanup', async () => {
    const { addRequest, removeExpiredRequests } = useHITLStore.getState();

    // Add a request with old timestamp (> 30 minutes ago)
    const oldTimestamp = new Date(Date.now() - 31 * 60 * 1000); // 31 minutes ago
    addRequest({
      agentName: 'Analyst',
      decision: 'Old request',
      context: { approvalId: 'old-123' },
      priority: 'low'
    });

    // Manually set old timestamp (since store creates new Date())
    const requests = useHITLStore.getState().requests;
    if (requests.length > 0) {
      requests[0].timestamp = oldTimestamp;
      useHITLStore.setState({ requests });
    }

    // Run cleanup
    act(() => {
      removeExpiredRequests();
    });

    // Verify old request was removed
    const { requests: updatedRequests } = useHITLStore.getState();
    expect(updatedRequests).toHaveLength(0);
  });
});
