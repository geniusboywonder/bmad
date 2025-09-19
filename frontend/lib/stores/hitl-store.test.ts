import { describe, it, expect, beforeEach } from 'vitest';
import { useHITLStore } from './hitl-store';

describe('useHITLStore', () => {
  beforeEach(() => {
    // Reset the store before each test
    useHITLStore.setState({
      requests: [],
      activeRequest: null,
    });
  });

  it('should add a new HITL request', () => {
    const request = {
      agentName: 'Analyst',
      decision: 'Proceed with analysis?',
      context: { data: 'some-data' },
      priority: 'medium' as const,
    };
    useHITLStore.getState().addRequest(request);
    const { requests } = useHITLStore.getState();
    expect(requests).toHaveLength(1);
    expect(requests[0].agentName).toBe('Analyst');
    expect(requests[0].status).toBe('pending');
  });

  it('should resolve a HITL request', () => {
    const request = {
      agentName: 'Analyst',
      decision: 'Proceed with analysis?',
      context: { data: 'some-data' },
      priority: 'medium' as const,
    };
    useHITLStore.getState().addRequest(request);
    const { requests: initialRequests } = useHITLStore.getState();
    const requestId = initialRequests[0].id;
    useHITLStore.getState().resolveRequest(requestId, 'approved', 'Looks good');
    const { requests: updatedRequests } = useHITLStore.getState();
    expect(updatedRequests[0].status).toBe('approved');
    expect(updatedRequests[0].response).toBe('Looks good');
  });

  it('should get requests by agent', () => {
    useHITLStore.getState().addRequest({ agentName: 'Analyst', decision: 'd1', context: {}, priority: 'low' });
    useHITLStore.getState().addRequest({ agentName: 'Developer', decision: 'd2', context: {}, priority: 'high' });
    useHITLStore.getState().addRequest({ agentName: 'Analyst', decision: 'd3', context: {}, priority: 'medium' });
    const analystRequests = useHITLStore.getState().getRequestsByAgent('Analyst');
    expect(analystRequests).toHaveLength(2);
  });

  it('should get the pending request count', () => {
    useHITLStore.getState().addRequest({ agentName: 'Analyst', decision: 'd1', context: {}, priority: 'low' });
    useHITLStore.getState().addRequest({ agentName: 'Developer', decision: 'd2', context: {}, priority: 'high' });
    expect(useHITLStore.getState().getPendingCount()).toBe(2);
    const { requests } = useHITLStore.getState();
    useHITLStore.getState().resolveRequest(requests[0].id, 'approved');
    expect(useHITLStore.getState().getPendingCount()).toBe(1);
  });

  it('should navigate to a request', () => {
    useHITLStore.getState().addRequest({ agentName: 'Analyst', decision: 'd1', context: {}, priority: 'low' });
    const { requests } = useHITLStore.getState();
    useHITLStore.getState().navigateToRequest(requests[0].id);
    const { activeRequest } = useHITLStore.getState();
    expect(activeRequest).not.toBeNull();
    expect(activeRequest?.id).toBe(requests[0].id);
  });
});
