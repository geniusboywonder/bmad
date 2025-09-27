import { create } from 'zustand';

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
  type: 'user' | 'agent' | 'system' | 'error' | 'hitl_request';
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

export interface AppState {
  connection: {
    connected: boolean;
    reconnecting: boolean;
  };
  agents: Record<string, Agent>;
  logs: Log[];
  conversation: Message[];
  agentFilter: string | null;
  setConnectionStatus: (status: { connected: boolean; reconnecting: boolean }) => void;
  updateAgent: (agent: Agent) => void;
  addLog: (log: Omit<Log, 'timestamp'>) => void;
  addMessage: (message: Message) => void;
  updateMessage: (approvalId: string, updates: Partial<Message>) => void;
  setAgentFilter: (agentName: string | null) => void;
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
    set((state) => ({
      ...state,
      conversation: [...state.conversation, message],
    })),

  updateMessage: (approvalId, updates) =>
    set((state) => ({
      ...state,
      conversation: state.conversation.map((message) =>
        message.approvalId === approvalId
          ? { ...message, ...updates }
          : message
      ),
    })),

  setAgentFilter: (agentName) =>
    set((state) => ({ ...state, agentFilter: agentName })),
}));
