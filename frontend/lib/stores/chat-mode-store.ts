import { create } from 'zustand';

type ChatMode = 'general' | 'project';

interface ProjectContext {
  id: string;
  description: string;
  activeAgents: string[];
  artifacts: any[];
}

interface ChatModeState {
  mode: ChatMode;
  awaitingBrief: boolean;
  projectContext: ProjectContext | null;
  setMode: (mode: ChatMode) => void;
  setAwaitingBrief: (awaiting: boolean) => void;
  setProjectContext: (context: ProjectContext | null) => void;
  switchToProjectMode: (context: ProjectContext) => void;
  switchToGeneralMode: () => void;
}

export const useChatModeStore = create<ChatModeState>((set) => ({
  mode: 'general',
  awaitingBrief: false,
  projectContext: null,
  setMode: (mode) => set({ mode }),
  setAwaitingBrief: (awaiting) => set({ awaitingBrief: awaiting }),
  setProjectContext: (context) => set({ projectContext: context }),
  switchToProjectMode: (context) => set({ mode: 'project', projectContext: context, awaitingBrief: false }),
  switchToGeneralMode: () => set({ mode: 'general', projectContext: null, awaitingBrief: false }),
}));
