import { create } from "zustand"

export interface Task {
  id: string
  name: string
  agent: string
  status: "pending" | "in-progress" | "completed" | "failed"
  priority: "low" | "medium" | "high"
  progress: number
  startTime: Date
  estimatedCompletion?: Date
  dependencies?: string[]
}

interface TaskStore {
  tasks: Task[]
  addTask: (task: Omit<Task, "id">) => void
  updateTask: (id: string, updates: Partial<Task>) => void
  removeTask: (id: string) => void
  getTasksByAgent: (agent: string) => Task[]
  getTasksByStatus: (status: Task["status"]) => Task[]
  clearTasks: () => void
  initializeEmptyTasks: () => void
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [], // Start with empty tasks array
  
  addTask: (task) =>
    set((state) => ({
      tasks: [...state.tasks, { ...task, id: Date.now().toString() }],
    })),
    
  updateTask: (id, updates) =>
    set((state) => ({
      tasks: state.tasks.map((task) => (task.id === id ? { ...task, ...updates } : task)),
    })),
    
  removeTask: (id) =>
    set((state) => ({
      tasks: state.tasks.filter((task) => task.id !== id),
    })),
    
  getTasksByAgent: (agent) => get().tasks.filter((task) => task.agent === agent),
  
  getTasksByStatus: (status) => get().tasks.filter((task) => task.status === status),
  
  clearTasks: () => set({ tasks: [] }),
  
  initializeEmptyTasks: () => set({ tasks: [] })
}))

// Initialize with empty tasks
useTaskStore.getState().initializeEmptyTasks()
