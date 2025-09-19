import { create } from 'zustand';

export interface ScaffoldedArtifact {
  id: string;
  name: string;
  stage: string;
  status: 'scaffolded' | 'in_progress' | 'completed' | 'error';
  progress: number;
  session_id: string;
}

interface ArtifactScaffoldingState {
  artifacts: Record<string, ScaffoldedArtifact>;
  setArtifacts: (artifacts: ScaffoldedArtifact[]) => void;
  createScaffold: (artifact: ScaffoldedArtifact) => void;
  updateProgress: (artifactId: string, progress: number) => void;
  updateStatus: (artifactId: string, status: ScaffoldedArtifact['status']) => void;
  clearArtifacts: () => void;
}

export const useArtifactScaffoldingStore = create<ArtifactScaffoldingState>((set) => ({
  artifacts: {},
  setArtifacts: (artifacts) => set({
      artifacts: artifacts.reduce((acc, artifact) => {
          acc[artifact.id] = artifact;
          return acc;
      }, {} as Record<string, ScaffoldedArtifact>)
  }),
  createScaffold: (artifact) =>
    set((state) => ({
      artifacts: {
        ...state.artifacts,
        [artifact.id]: { ...artifact, status: 'scaffolded', progress: 0 },
      },
    })),
  updateProgress: (artifactId, progress) =>
    set((state) => {
      const artifact = state.artifacts[artifactId];
      if (artifact) {
        const newStatus = progress >= 100 ? 'completed' : 'in_progress';
        return {
          artifacts: {
            ...state.artifacts,
            [artifactId]: { ...artifact, progress, status: newStatus },
          },
        };
      }
      return state;
    }),
    updateStatus: (artifactId, status) =>
    set((state) => {
      const artifact = state.artifacts[artifactId];
      if (artifact) {
        return {
          artifacts: {
            ...state.artifacts,
            [artifactId]: { ...artifact, status },
          },
        };
      }
      return state;
    }),
  clearArtifacts: () => set({ artifacts: {} }),
}));
