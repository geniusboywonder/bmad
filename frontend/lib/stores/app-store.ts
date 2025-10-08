import { create } from 'zustand';
import type { AgentType } from '@/lib/services/api/types';

// --- TYPE DEFINITIONS ---

export interface Agent {
  name: string;
  status: string;
  task: string;
}

export interface Log {
  agent: string;
  message: string;
  level: 'info' | 'error';
  timestamp: string;
}

export interface Message {
  type: 'user' | 'agent' | 'system' | 'error' | 'hitl_request' | 'hitl_counter';
  agent: string;
  content: string;
  timestamp?: Date;
  requiresApproval?: boolean;
  estimatedCost?: number;
  estimatedTime?: string;
  taskId?: string;
  requestId?: string;
  approvalId?: string;
  hitlStatus?: 'pending' | 'approved' | 'rejected';
  urgency?: string;
  metadata?: {
    requestId?: string;
    priority?: 'low' | 'medium' | 'high' | 'urgent';
    [key: string]: any;
  };
}

export interface PolicyGuidance {
  status: 'denied' | 'needs_clarification';
  reasonCode: string;
  message: string;
  currentPhase?: string;
  allowedAgents: AgentType[];
  timestamp: string;
}

export interface AppState {
  connection: {
    connected: boolean;
    reconnecting: boolean;
  };
  agents: Record<string, Agent>;
  logs: Log[];
  conversation: Message[];
  agentFilter: string | null;
  policyGuidance: PolicyGuidance | null;
  setConnectionStatus: (status: { connected: boolean; reconnecting: boolean }) => void;
  updateAgent: (agent: Agent) => void;
  addLog: (log: Omit<Log, 'timestamp'>) => void;
  addMessage: (message: Message) => void;
  updateMessage: (approvalId: string, updates: Partial<Message>) => void;
  setAgentFilter: (agentName: string | null) => void;
  setPolicyGuidance: (guidance: PolicyGuidance | null) => void;
}

// --- CENTRALIZED APP STORE ---

export const useAppStore = create<AppState>((set) => ({
  connection: {
    connected: false,
    reconnecting: false,
  },
  agents: {},
  logs: [],
  conversation: [],
  agentFilter: null,
  policyGuidance: null,

  setConnectionStatus: (status) =>
    set((state) => ({ ...state, connection: status })),

  updateAgent: (agent) =>
    set((state) => ({
      ...state,
      agents: { ...state.agents, [agent.name]: agent },
    })),

  addLog: (log) =>
    set((state) => ({
      ...state,
      logs: [...state.logs, { ...log, timestamp: new Date().toISOString() }],
    })),

  addMessage: (message) =>
    set((state) => {
      // Prevent duplicate HITL messages based on approvalId
      if (message.approvalId) {
        const exists = state.conversation.some(
          (msg) => msg.approvalId === message.approvalId
        );
        if (exists) {
          console.log(`[AppStore] Skipping duplicate message for approval ${message.approvalId}`);
          return state;
        }
      }

      return {
        ...state,
        conversation: [...state.conversation, message],
      };
    }),

  updateMessage: (approvalId, updates) =>
    set((state) => ({
      ...state,
      conversation: state.conversation.map((message) => {
        if (message.approvalId !== approvalId) {
          return message;
        }

        const mergedMetadata = updates.metadata
          ? { ...(message.metadata || {}), ...updates.metadata }
          : message.metadata;

        const { metadata, ...rest } = updates;

        return {
          ...message,
          ...rest,
          metadata: mergedMetadata,
        };
      }),
    })),

  setAgentFilter: (agentName) =>
    set((state) => ({ ...state, agentFilter: agentName })),

  setPolicyGuidance: (guidance) =>
    set((state) => ({ ...state, policyGuidance: guidance })),
}));

// Make store globally accessible for cross-store updates
if (typeof window !== 'undefined') {
  (window as any).useAppStore = useAppStore;
}
