import { create } from 'zustand';

export interface RequirementQuestion {
  id: string;
  text: string;
}

interface InteractiveSessionState {
  questions: RequirementQuestion[];
  answers: Record<string, string>;
  isAwaitingApproval: boolean;
  setQuestions: (questions: RequirementQuestion[]) => void;
  updateAnswer: (questionId: string, answer: string) => void;
  setAwaitingApproval: (isAwaiting: boolean) => void;
  clearSession: () => void;
}

export const useInteractiveSessionStore = create<InteractiveSessionState>((set) => ({
  questions: [],
  answers: {},
  isAwaitingApproval: false,
  setQuestions: (questions) => set({ questions, answers: {} }), // Reset answers when new questions arrive
  updateAnswer: (questionId, answer) =>
    set((state) => ({
      answers: {
        ...state.answers,
        [questionId]: answer,
      },
    })),
  setAwaitingApproval: (isAwaiting) => set({ isAwaitingApproval: isAwaiting }),
  clearSession: () => set({ questions: [], answers: {}, isAwaitingApproval: false }),
}));
