import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { safetyEventHandler, SafetyAlert } from '../services/safety/safety-event-handler';
import { hitlService } from '../services/api/hitl.service';

// Safe storage implementation with error handling
const createSafeStorage = () => {
  const storage = {
    getItem: (name: string): string | null => {
      try {
        if (typeof window === 'undefined') return null
        return window.localStorage.getItem(name)
      } catch (error) {
        console.warn(`Failed to read from localStorage: ${error}`)
        return null
      }
    },
    setItem: (name: string, value: string): void => {
      try {
        if (typeof window === 'undefined') return
        window.localStorage.setItem(name, value)
      } catch (error) {
        console.warn(`Failed to write to localStorage: ${error}`)
        if (error instanceof DOMException && error.code === 22) {
          try {
            window.localStorage.clear()
            window.localStorage.setItem(name, value)
          } catch (retryError) {
            console.error('localStorage completely unavailable:', retryError)
          }
        }
      }
    },
    removeItem: (name: string): void => {
      try {
        if (typeof window === 'undefined') return
        window.localStorage.removeItem(name)
      } catch (error) {
        console.warn(`Failed to remove from localStorage: ${error}`)
      }
    }
  }
  return storage
}

interface HITLRequest {
  id: string;
  agentName: string;
  decision: string;
  context: any;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  timestamp: Date;
  status: 'pending' | 'approved' | 'rejected' | 'modified';
  response?: string;
}

interface HITLStore {
  requests: HITLRequest[];
  activeRequest: HITLRequest | null;
  safetyAlerts: SafetyAlert[];

  addRequest: (request: Omit<HITLRequest, 'id' | 'timestamp' | 'status'>) => void;
  resolveRequest: (id: string, status: 'approved' | 'rejected' | 'modified', response?: string) => Promise<void>;
  getRequestsByAgent: (agentName: string) => HITLRequest[];
  getPendingCount: () => number;

  // Safety alerts integration
  setSafetyAlerts: (alerts: SafetyAlert[]) => void;
  acknowledgeSafetyAlert: (alertId: string) => void;

  // Navigation helpers
  navigateToRequest: (id: string) => void;
  filterChatByAgent: (agentName: string) => void;

  // Cleanup methods
  clearAllRequests: () => void;
  removeResolvedRequests: () => void;
}

export const useHITLStore = create<HITLStore>()(
  persist(
    (set, get) => ({
      requests: [],
      activeRequest: null,
      safetyAlerts: [],

      addRequest: (request) => {
        const newRequest: HITLRequest = {
          ...request,
          id: `hitl-${Date.now()}-${Math.random()}`,
          timestamp: new Date(),
          status: 'pending',
        };
        set((state) => ({ requests: [...state.requests, newRequest] }));
      },

      resolveRequest: async (id, status, response) => {
        const request = get().requests.find((req) => req.id === id);
        if (!request) return;

        try {
          // Get approval ID from context
          const approvalId = request.context?.approvalId;

          if (approvalId) {
            // Use the correct HITL safety API endpoint for agent approvals
            const approved = status === 'approved';
            const apiResponse = await fetch(`http://localhost:8000/api/v1/hitl-safety/approve-agent-execution/${approvalId}`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                approved: approved,
                response: response || `Request ${status}`,
                comment: response || `Request ${status}`
              }),
            });

            if (!apiResponse.ok) {
              throw new Error(`API call failed: ${apiResponse.status} ${apiResponse.statusText}`);
            }

            console.log(`[HITLStore] Successfully called HITL safety API for approval ${approvalId}`);
          } else {
            console.warn(`[HITLStore] No approval ID found in request context for ${id}`);
          }

          // Remove the request from the store completely when resolved
          set((state) => ({
            requests: state.requests.filter((req) => req.id !== id),
            activeRequest: state.activeRequest?.id === id ? null : state.activeRequest,
          }));

          // Acknowledge related safety alert if exists
          const relatedAlertId = `hitl_${id}`;
          safetyEventHandler.acknowledgeAlert(relatedAlertId);

          console.log(`[HITLStore] Resolved and removed request ${id} with status: ${status}`);
        } catch (error) {
          console.error(`[HITLStore] Failed to resolve request ${id}:`, error);
          throw error;
        }
      },

      getRequestsByAgent: (agentName) => {
        return get().requests.filter((req) => req.agentName === agentName);
      },

      getPendingCount: () => {
        return get().requests.filter((req) => req.status === 'pending').length;
      },

      // Safety alerts integration
      setSafetyAlerts: (alerts) => {
        set({ safetyAlerts: alerts });
      },

      acknowledgeSafetyAlert: (alertId) => {
        safetyEventHandler.acknowledgeAlert(alertId);
        set((state) => ({
          safetyAlerts: state.safetyAlerts.map(alert =>
            alert.id === alertId ? { ...alert, acknowledged: true } : alert
          )
        }));
      },

      navigateToRequest: (id) => {
        const request = get().requests.find((req) => req.id === id);
        if (request) {
          set({ activeRequest: request });
        }
      },

      // Chat filtering is handled by the chat component's agent filter state
      filterChatByAgent: (agentName) => {
        // This is handled by the chat component's useEffect that responds to activeRequest changes
        console.log(`Chat should filter by agent: ${agentName}`);
      },

      // Cleanup methods
      clearAllRequests: () => {
        set({ requests: [], activeRequest: null });
        console.log('[HITLStore] Cleared all HITL requests');
      },

      removeResolvedRequests: () => {
        set((state) => ({
          requests: state.requests.filter((req) => req.status === 'pending'),
          activeRequest: state.activeRequest?.status !== 'pending' ? null : state.activeRequest,
        }));
        console.log('[HITLStore] Removed all resolved HITL requests');
      },
    }),
    {
      name: 'hitl-store',
      storage: createJSONStorage(() => createSafeStorage()),
      partialize: (state) => ({
        requests: state.requests,
        // Don't persist activeRequest as it's a UI state
      }),
      version: 1,
    }
  )
);

if (typeof window !== 'undefined') {
  (window as any).useHITLStore = useHITLStore;
}