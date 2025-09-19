import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import type { ProcessStage, ProcessFlow, Task, Artifact, HITLRequest } from '@/lib/types'

interface ProcessState {
  // Current process flow
  currentFlow: ProcessFlow | null
  
  // Stages data
  stages: ProcessStage[]
  currentStageId: string | null
  
  // HITL requests
  hitlRequests: HITLRequest[]
  
  // Loading states
  isLoading: boolean
  error: string | null
}

interface ProcessActions {
  // Process flow actions
  setCurrentFlow: (flow: ProcessFlow) => void
  updateFlowStatus: (status: ProcessFlow['status']) => void
  
  // Stage actions
  setStages: (stages: ProcessStage[]) => void
  updateStage: (stageId: string, updates: Partial<ProcessStage>) => void
  setCurrentStage: (stageId: string) => void
  getStageByName: (name: string) => ProcessStage | undefined
  getStageById: (id: string) => ProcessStage | undefined
  
  // Task actions
  updateTask: (stageId: string, taskId: string, updates: Partial<Task>) => void
  addTask: (stageId: string, task: Task) => void
  removeTask: (stageId: string, taskId: string) => void
  
  // Artifact actions
  updateArtifact: (stageId: string, artifactId: string, updates: Partial<Artifact>) => void
  addArtifact: (stageId: string, artifact: Artifact) => void
  removeArtifact: (stageId: string, artifactId: string) => void
  
  // HITL actions
  addHITLRequest: (request: HITLRequest) => void
  respondToHITL: (requestId: string, response: any) => void
  removeHITLRequest: (requestId: string) => void
  
  // Control actions
  pauseStage: (stageId: string) => void
  resumeStage: (stageId: string) => void
  
  // Loading and error actions
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  
  // Utility actions
  reset: () => void
  
  // SDLC workflow integration actions
  updateStageFromTask: (agentName: string, taskName: string, status: string) => void
  updateStageProgress: (stageName: string, current: number, total: number) => void
}

type ProcessStore = ProcessState & ProcessActions


const initialState: ProcessState = {
  currentFlow: null,
  stages: [],
  currentStageId: null,
  hitlRequests: [],
  isLoading: false,
  error: null
}

export const useProcessStore = create<ProcessStore>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,

    // Process flow actions
    setCurrentFlow: (flow) => set({ currentFlow: flow }),
    
    updateFlowStatus: (status) => set((state) => ({
      currentFlow: state.currentFlow ? { ...state.currentFlow, status } : null
    })),

    // Stage actions
    setStages: (stages) => set({ stages }),
    
    updateStage: (stageId, updates) => set((state) => ({
      stages: state.stages.map(stage => 
        stage.id === stageId ? { ...stage, ...updates } : stage
      )
    })),
    
    setCurrentStage: (stageId) => set({ currentStageId: stageId }),
    
    getStageByName: (name) => get().stages.find(stage => 
      stage.name.toLowerCase() === name.toLowerCase()
    ),
    
    getStageById: (id) => get().stages.find(stage => stage.id === id),

    // Task actions
    updateTask: (stageId, taskId, updates) => set((state) => ({
      stages: state.stages.map(stage => 
        stage.id === stageId 
          ? {
              ...stage,
              tasks: stage.tasks.map(task =>
                task.id === taskId ? { ...task, ...updates } : task
              )
            }
          : stage
      )
    })),
    
    addTask: (stageId, task) => set((state) => ({
      stages: state.stages.map(stage => 
        stage.id === stageId 
          ? { ...stage, tasks: [...stage.tasks, task] }
          : stage
      )
    })),
    
    removeTask: (stageId, taskId) => set((state) => ({
      stages: state.stages.map(stage => 
        stage.id === stageId 
          ? { ...stage, tasks: stage.tasks.filter(task => task.id !== taskId) }
          : stage
      )
    })),

    // Artifact actions
    updateArtifact: (stageId, artifactId, updates) => set((state) => ({
      stages: state.stages.map(stage => 
        stage.id === stageId 
          ? {
              ...stage,
              artifacts: stage.artifacts.map(artifact =>
                artifact.id === artifactId ? { ...artifact, ...updates } : artifact
              )
            }
          : stage
      )
    })),
    
    addArtifact: (stageId, artifact) => set((state) => ({
      stages: state.stages.map(stage => 
        stage.id === stageId 
          ? { ...stage, artifacts: [...stage.artifacts, artifact] }
          : stage
      )
    })),
    
    removeArtifact: (stageId, artifactId) => set((state) => ({
      stages: state.stages.map(stage => 
        stage.id === stageId 
          ? { ...stage, artifacts: stage.artifacts.filter(artifact => artifact.id !== artifactId) }
          : stage
      )
    })),

    // HITL actions
    addHITLRequest: (request) => set((state) => ({
      hitlRequests: [...state.hitlRequests, request]
    })),
    
    respondToHITL: (requestId, response) => set((state) => ({
      hitlRequests: state.hitlRequests.map(request =>
        request.id === requestId 
          ? { ...request, status: 'responded', response, respondedAt: new Date().toISOString() }
          : request
      )
    })),
    
    removeHITLRequest: (requestId) => set((state) => ({
      hitlRequests: state.hitlRequests.filter(request => request.id !== requestId)
    })),

    // Control actions
    pauseStage: (stageId) => set((state) => ({
      stages: state.stages.map(stage => 
        stage.id === stageId ? { ...stage, status: 'waiting' as const } : stage
      )
    })),
    
    resumeStage: (stageId) => set((state) => ({
      stages: state.stages.map(stage => 
        stage.id === stageId ? { ...stage, status: 'wip' as const } : stage
      )
    })),

    // Loading and error actions
    setLoading: (loading) => set({ isLoading: loading }),
    setError: (error) => set({ error }),

    // Utility actions
    reset: () => set(initialState),

    // SDLC workflow integration actions
    updateStageFromTask: (agentName, taskName, status) => set((state) => {
      // Find stage that matches the agent name
      const stage = state.stages.find(s => 
        s.name.toLowerCase() === agentName.toLowerCase() ||
        s.id.toLowerCase() === agentName.toLowerCase()
      );
      
      if (!stage) return state;
      
      // Map workflow status to stage status
      const stageStatus = status === 'working' || status === 'wip' ? 'wip' as const :
                         status === 'completed' ? 'completed' as const :
                         status === 'error' ? 'error' as const :
                         'pending' as const;
      
      return {
        stages: state.stages.map(s => 
          s.id === stage.id 
            ? { ...s, status: stageStatus, currentTask: taskName }
            : s
        )
      };
    }),
    
    updateStageProgress: (stageName, current, total) => set((state) => {
      // Find stage by name
      const stage = state.stages.find(s => 
        s.name.toLowerCase() === stageName.toLowerCase() ||
        s.id.toLowerCase() === stageName.toLowerCase()
      );
      
      if (!stage) return state;
      
      return {
        stages: state.stages.map(s => 
          s.id === stage.id 
            ? { ...s, progress: { current, total, percentage: Math.round((current / total) * 100) } }
            : s
        )
      };
    })
  }))
)

// The store now starts with an empty stage list.
// It will be populated dynamically based on the selected process.
