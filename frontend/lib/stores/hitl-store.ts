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
  action?: 'approve' | 'reject' | 'amend';
}

interface HitlSettings {
  enabled: boolean;
  counterTotal: number;
  counterRemaining: number;
  locked: boolean;
}

interface HITLStore {
  requests: HITLRequest[];
  activeRequest: HITLRequest | null;
  safetyAlerts: SafetyAlert[];
  settings: Record<string, HitlSettings>;

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

  // Settings helpers
  loadSettings: (projectId: string) => Promise<void>;
  applyServerSettings: (
    projectId: string,
    payload: { counter_total: number; counter_remaining: number; hitl_enabled: boolean; locked?: boolean },
    reason?: string
  ) => void;
  setHitlEnabled: (projectId: string, enabled: boolean) => Promise<void>;
  updateCounterLimit: (projectId: string, counter: number, reset?: boolean) => Promise<void>;
  continueAutoApprovals: (projectId: string, counter?: number) => Promise<void>;
  stopAutoApprovals: (projectId: string) => Promise<void>;

  // Cleanup methods
  clearAllRequests: () => void;
  removeResolvedRequests: () => void;
  removeExpiredRequests: () => void;
}

export const useHITLStore = create<HITLStore>()(
  persist(
    (set, get) => {
      const updateCounterMessage = (projectId: string, settings: HitlSettings, reason?: string) => {
        if (typeof window === 'undefined') return;
        const appStore = (window as any).useAppStore;
        if (!appStore) return;

        const { updateMessage } = appStore.getState();
        updateMessage(`hitl-counter-${projectId}`, {
          metadata: {
            projectId,
            counterTotal: settings.counterTotal,
            counterRemaining: settings.counterRemaining,
            hitlEnabled: settings.enabled,
            locked: settings.locked,
            reason,
          },
        });
      };

      return {
      requests: [],
      activeRequest: null,
      safetyAlerts: [],
      settings: {},

      addRequest: (request) => {
        // Ensure context is an object and approvalId is present
        const context = request.context || {};
        const approvalId = context.approvalId || `auto-approval-${Date.now()}-${Math.random()}`;

        if (approvalId) {
          const existingRequest = get().requests.find(req =>
            req.context?.approvalId === approvalId && req.status === 'pending'
          );
          if (existingRequest) {
            console.log('[HITLStore] Duplicate request detected, skipping:', approvalId);
            return;
          }
        }

        const newRequest: HITLRequest = {
          ...request,
          id: `hitl-${Date.now()}-${Math.random()}`,
          timestamp: new Date(),
          status: 'pending',
          action: undefined,
          context: {
            ...context,
            approvalId: approvalId
          }
        };
        set((state) => ({ requests: [...state.requests, newRequest] }));
      },

      resolveRequest: async (id, status, response) => {
        const request = get().requests.find((req) => req.id === id);
        if (!request) {
          console.warn(`[HITLStore] Request ${id} not found in store`);
          return;
        }

        const actionMap: Record<'approved' | 'rejected' | 'modified', 'approve' | 'reject' | 'amend'> = {
          approved: 'approve',
          rejected: 'reject',
          modified: 'amend'
        };

        const selectedAction = actionMap[status];

        // Update request status in store instead of removing
        const updateRequestStatus = (newStatus: 'approved' | 'rejected' | 'modified', responseText?: string) => {
          set((state) => ({
            requests: state.requests.map((req) =>
              req.id === id
                ? { ...req, status: newStatus, response: responseText, action: actionMap[newStatus] }
                : req
            ),
            activeRequest: state.activeRequest?.id === id ? null : state.activeRequest,
          }));

          // Acknowledge related safety alert
          const relatedAlertId = `hitl_${id}`;
          safetyEventHandler.acknowledgeAlert(relatedAlertId);

          // Update corresponding chat message in app store
          if (typeof window !== 'undefined' && (window as any).useAppStore) {
            const approvalId = request.context?.approvalId;
            if (approvalId) {
              const { updateMessage } = (window as any).useAppStore.getState();
              updateMessage(approvalId, { hitlStatus: newStatus });
              console.log(`[HITLStore] Updated chat message status for approval ${approvalId} to ${newStatus}`);
            }
          }
        };

        // Remove stale requests only
        const removeFromStore = () => {
          set((state) => ({
            requests: state.requests.filter((req) => req.id !== id),
            activeRequest: state.activeRequest?.id === id ? null : state.activeRequest,
          }));

          const relatedAlertId = `hitl_${id}`;
          safetyEventHandler.acknowledgeAlert(relatedAlertId);
        };

        const approvalId = request.context?.approvalId;

        // Helper to validate UUID format
        const isValidUUID = (value: string | undefined | null) => {
          if (typeof value !== 'string') return false;
          const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
          return uuidRegex.test(value);
        };

        try {
          if (!approvalId || !isValidUUID(approvalId)) {
            console.warn(`[HITLStore] Approval ${approvalId ?? 'unknown'} is not a valid UUID. Marking request as ${status} locally.`);
            updateRequestStatus(status, response || `Request ${status} (local-only)`);
            return;
          }

          // Check if approval still exists before trying to resolve
          const checkResponse = await fetch(`http://localhost:8000/api/v1/hitl/status/${approvalId}`);

          if (!checkResponse.ok) {
            if (checkResponse.status === 404) {
              console.warn(`[HITLStore] Approval ${approvalId} no longer exists. Removing stale request.`);
              removeFromStore();
              return;
            }
          } else {
            const approvalData = await checkResponse.json();
            if (approvalData.status !== 'PENDING') {
              console.warn(`[HITLStore] Approval ${approvalId} already ${approvalData.status}. Removing stale request.`);
              removeFromStore();
              return;
            }
          }

          const apiResponse = await fetch(`http://localhost:8000/api/v1/hitl/approve/${approvalId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              action: selectedAction,
              response: response || `Request ${status}`
            }),
          });

          if (!apiResponse.ok) {
            const errorText = await apiResponse.text();

            // Handle stale requests gracefully
            if (apiResponse.status === 404) {
              console.warn(`[HITLStore] Approval ${approvalId} not found (expired/processed). Removing from store.`);
              removeFromStore();
              return;
            }

            if (apiResponse.status === 400) {
              // Check if it's a stale request
              if (errorText.includes('expired') || errorText.includes('not pending') || errorText.includes('already')) {
                console.warn(`[HITLStore] Approval ${approvalId} is stale: ${errorText}. Removing from store.`);
                removeFromStore();
                return;
              }
              throw new Error(`API error: ${errorText}`);
            }

            throw new Error(`API failed: ${apiResponse.status} ${apiResponse.statusText}`);
          }

          console.log(`[HITLStore] Successfully resolved approval ${approvalId} with status ${status}`);
          updateRequestStatus(status, response || `Request ${status}`);

        } catch (error) {
          console.error(`[HITLStore] Failed to resolve request ${id}:`, error);

          // Only remove from store if it's a stale request error
          if (error instanceof Error) {
            const isStaleError = error.message.includes('404') ||
                                error.message.includes('expired') ||
                                error.message.includes('not pending');

            if (isStaleError) {
              console.warn(`[HITLStore] Removing stale request ${id} after error`);
              removeFromStore();
              return;
            }
          }

          // For other errors, keep in store and rethrow
          throw error;
        }
      },

      getRequestsByAgent: (agentName) => {
        return get().requests.filter((req) => req.agentName === agentName);
      },

      getPendingCount: () => {
        // Also filter out expired requests when counting
        const now = new Date();
        return get().requests.filter((req) => {
          if (req.status !== 'pending') return false;
          
          // Check if request has expired (assuming 30 minute expiration)
          const requestAge = now.getTime() - new Date(req.timestamp).getTime();
          const THIRTY_MINUTES = 30 * 60 * 1000;
          
          if (requestAge > THIRTY_MINUTES) {
            console.warn(`[HITLStore] Request ${req.id} has expired, excluding from pending count`);
            return false;
          }
          
          return true;
        }).length;
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

      removeExpiredRequests: () => {
        const now = new Date();
        const THIRTY_MINUTES = 30 * 60 * 1000;
        
        set((state) => {
          const validRequests = state.requests.filter((req) => {
            const requestAge = now.getTime() - new Date(req.timestamp).getTime();
            const isExpired = requestAge > THIRTY_MINUTES;
            
            if (isExpired) {
              console.log(`[HITLStore] Removing expired request ${req.id}`);
            }
            
            return !isExpired;
          });
          
          const expiredCount = state.requests.length - validRequests.length;
          if (expiredCount > 0) {
            console.log(`[HITLStore] Removed ${expiredCount} expired HITL requests`);
          }
          
          return {
            requests: validRequests,
            activeRequest: validRequests.find(r => r.id === state.activeRequest?.id) || null,
          };
        });
      },
      loadSettings: async (projectId) => {
        if (!projectId) return;
        try {
          const response = await hitlService.getSettings(projectId);
          if (response.success && response.data) {
            const normalized: HitlSettings = {
              enabled: response.data.enabled,
              counterTotal: response.data.counter_total,
              counterRemaining: response.data.counter_remaining,
              locked: response.data.locked,
            };
            set((state) => ({
              settings: {
                ...state.settings,
                [projectId]: normalized,
              },
            }));
            updateCounterMessage(projectId, normalized, 'settings_load');
          }
        } catch (error) {
          console.error('[HITLStore] Failed to load settings', error);
        }
      },

      applyServerSettings: (projectId, payload, reason) => {
        const normalized: HitlSettings = {
          enabled: payload.hitl_enabled,
          counterTotal: payload.counter_total,
          counterRemaining: payload.counter_remaining,
          locked: payload.locked ?? payload.counter_remaining <= 0,
        };
        set((state) => ({
          settings: {
            ...state.settings,
            [projectId]: normalized,
          },
        }));
        updateCounterMessage(projectId, normalized, reason);
      },

      setHitlEnabled: async (projectId, enabled) => {
        try {
          const response = await hitlService.toggleSettings(projectId, enabled);
          const payload = response.data?.data;
          if (response.success && payload) {
            const normalized: HitlSettings = {
              enabled: payload.enabled,
              counterTotal: payload.counter_total,
              counterRemaining: payload.counter_remaining,
              locked: payload.locked,
            };
            set((state) => ({
              settings: {
                ...state.settings,
                [projectId]: normalized,
              },
            }));
            updateCounterMessage(projectId, normalized, 'toggle');
          }
        } catch (error) {
          console.error('[HITLStore] Failed to toggle HITL', error);
          throw error;
        }
      },

      updateCounterLimit: async (projectId, counter, reset = true) => {
        try {
          const response = await hitlService.updateCounterLimit(projectId, counter, reset);
          const payload = response.data?.data;
          if (response.success && payload) {
            const normalized: HitlSettings = {
              enabled: payload.enabled,
              counterTotal: payload.counter_total,
              counterRemaining: payload.counter_remaining,
              locked: payload.locked,
            };
            set((state) => ({
              settings: {
                ...state.settings,
                [projectId]: normalized,
              },
            }));
            updateCounterMessage(projectId, normalized, 'counter_update');
          }
        } catch (error) {
          console.error('[HITLStore] Failed to update HITL counter', error);
          throw error;
        }
      },

      continueAutoApprovals: async (projectId, counter) => {
        try {
          const response = await hitlService.continueAutoApprovals(projectId, counter);
          const payload = response.data?.data;
          if (response.success && payload) {
            const normalized: HitlSettings = {
              enabled: payload.enabled,
              counterTotal: payload.counter_total,
              counterRemaining: payload.counter_remaining,
              locked: payload.locked,
            };
            set((state) => ({
              settings: {
                ...state.settings,
                [projectId]: normalized,
              },
            }));
            updateCounterMessage(projectId, normalized, 'counter_continue');
          }
        } catch (error) {
          console.error('[HITLStore] Failed to continue auto approvals', error);
          throw error;
        }
      },

      stopAutoApprovals: async (projectId) => {
        try {
          const response = await hitlService.stopAutoApprovals(projectId);
          const payload = response.data?.data;
          if (response.success && payload) {
            const normalized: HitlSettings = {
              enabled: payload.enabled,
              counterTotal: payload.counter_total,
              counterRemaining: payload.counter_remaining,
              locked: payload.locked,
            };
            set((state) => ({
              settings: {
                ...state.settings,
                [projectId]: normalized,
              },
            }));
            updateCounterMessage(projectId, normalized, 'counter_stop');
          }
        } catch (error) {
          console.error('[HITLStore] Failed to stop auto approvals', error);
          throw error;
        }
      },
    };
    },
    {
      name: 'hitl-store',
      storage: createJSONStorage(() => createSafeStorage()),
      partialize: (state) => ({
        requests: state.requests,
        settings: state.settings,
        // Don't persist activeRequest as it's a UI state
      }),
      version: 1,
    }
  )
);

// Auto-cleanup expired requests every 5 minutes
if (typeof window !== 'undefined') {
  (window as any).useHITLStore = useHITLStore;
  
  // Run cleanup on page load
  useHITLStore.getState().removeExpiredRequests();
  
  // Also verify all remaining requests with backend on startup
  setTimeout(async () => {
    const pendingRequests = useHITLStore.getState().requests.filter(r => r.status === 'pending');
    
    for (const request of pendingRequests) {
      const approvalId = request.context?.approvalId;
      if (!approvalId) continue;
      
      try {
        const response = await fetch(`http://localhost:8000/api/v1/hitl-safety/approvals/${approvalId}`);
        const data = !response.ok ? null : await response.json();
        
        if (!response.ok || data?.status !== 'PENDING') {
          console.log(`[HITLStore] Startup cleanup: Removing stale request ${request.id}`);
          useHITLStore.setState((state) => ({
            requests: state.requests.filter(r => r.id !== request.id)
          }));
        }
      } catch (error) {
        console.warn(`[HITLStore] Failed to verify request ${request.id}:`, error);
      }
    }
  }, 2000); // Wait 2s after page load for backend to be ready
  
  // Set up periodic cleanup
  setInterval(() => {
    useHITLStore.getState().removeExpiredRequests();
  }, 5 * 60 * 1000); // Every 5 minutes
}
