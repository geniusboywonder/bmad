import { create } from "zustand"

export interface ArtifactNode {
  name: string
  path: string
  type: "file" | "folder"
  children?: ArtifactNode[]
  size?: number
}

export interface Artifacts {
  [category: string]: ArtifactNode[]
}

interface ArtifactStore {
  artifacts: Artifacts
  setArtifacts: (artifacts: Artifacts) => void
  clearArtifacts: () => void
}

export const useArtifactStore = create<ArtifactStore>((set) => ({
  artifacts: {},
  setArtifacts: (artifacts) => set({ artifacts }),
  clearArtifacts: () => set({ artifacts: {} }),
}))
