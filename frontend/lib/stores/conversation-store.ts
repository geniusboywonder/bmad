import { create } from "zustand"
import { subscribeWithSelector, persist, createJSONStorage } from "zustand/middleware"

export interface ChatMessage {
  id: string
  type: 'user' | 'agent' | 'system' | 'error'
  agent?: string
  content: string
  timestamp: Date
  metadata?: Record<string, any>
  collapsed?: boolean
}

interface ConversationStore {
  messages: ChatMessage[]
  isTyping: boolean
  currentProject: string | null
  conversationId: string | null
  
  // Core message management
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void
  removeMessage: (id: string) => void
  clearMessages: () => void
  toggleMessageCollapse: (id: string) => void
  
  // Conversation management
  startNewConversation: (projectDescription?: string) => void
  setCurrentProject: (project: string) => void
  setTyping: (isTyping: boolean) => void
  
  // Message utilities
  getMessagesByType: (type: ChatMessage['type']) => ChatMessage[]
  getMessagesByAgent: (agent: string) => ChatMessage[]
  getLastMessage: () => ChatMessage | null
  
  // Persistence utilities
  exportConversation: () => string
  importConversation: (data: string) => void
}

// Helper to generate unique message IDs
const generateMessageId = () => {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// Helper to generate conversation IDs
const generateConversationId = () => {
  return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

export const useConversationStore = create<ConversationStore>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        messages: [],
        isTyping: false,
        currentProject: null,
        conversationId: null,

        // Core message management
        addMessage: (messageData) => {
          const message: ChatMessage = {
            ...messageData,
            id: generateMessageId(),
            timestamp: new Date(), // Always use current time to avoid corruption
          }
          
          set((state) => ({
            messages: [...state.messages, message]
          }))
        },

        updateMessage: (id, updates) => {
          set((state) => ({
            messages: state.messages.map((message) =>
              message.id === id 
                ? { ...message, ...updates }
                : message
            )
          }))
        },

        removeMessage: (id) => {
          set((state) => ({
            messages: state.messages.filter((message) => message.id !== id)
          }))
        },

        clearMessages: () => {
          set({
            messages: [],
            isTyping: false
          })
        },

        toggleMessageCollapse: (id) => {
          set((state) => ({
            messages: state.messages.map((message) =>
              message.id === id 
                ? { ...message, collapsed: !message.collapsed }
                : message
            )
          }))
        },

        // Conversation management
        startNewConversation: (projectDescription) => {
          const conversationId = generateConversationId()
          
          set({
            messages: [],
            isTyping: false,
            conversationId,
            currentProject: projectDescription || null
          })

          // Add welcome message if starting fresh
          if (projectDescription) {
            get().addMessage({
              type: 'system',
              agent: 'System',
              content: `Starting new project: "${projectDescription}"`
            })
          }
        },

        setCurrentProject: (project) => {
          set({ currentProject: project })
        },

        setTyping: (isTyping) => {
          set({ isTyping })
        },

        // Message utilities
        getMessagesByType: (type) => {
          return get().messages.filter((message) => message.type === type)
        },

        getMessagesByAgent: (agent) => {
          return get().messages.filter((message) => 
            message.agent?.toLowerCase() === agent.toLowerCase()
          )
        },

        getLastMessage: () => {
          const messages = get().messages
          return messages.length > 0 ? messages[messages.length - 1] : null
        },

        // Persistence utilities
        exportConversation: () => {
          const { messages, currentProject, conversationId } = get()
          return JSON.stringify({ 
            messages, 
            currentProject, 
            conversationId,
            exportDate: new Date() 
          }, null, 2)
        },

        importConversation: (data) => {
          try {
            const parsed = JSON.parse(data)
            if (parsed.messages) {
              set({
                messages: parsed.messages.map((msg: any) => ({
                  ...msg,
                  timestamp: new Date(msg.timestamp)
                })),
                currentProject: parsed.currentProject || null,
                conversationId: parsed.conversationId || generateConversationId()
              })
            }
          } catch (error) {
            console.error('Failed to import conversation:', error)
          }
        }
      }),
      {
        name: 'conversation-store',
        storage: createJSONStorage(() => sessionStorage), // Changed to sessionStorage
        partialize: (state) => ({
          messages: state.messages,
          currentProject: state.currentProject,
          conversationId: state.conversationId
        }),
        version: 1,
        // Custom serialization to handle Date objects
        serialize: (state) => {
          return JSON.stringify({
            state: {
              ...state,
              messages: state.messages.map(msg => ({
                ...msg,
                timestamp: msg.timestamp instanceof Date ? msg.timestamp.toISOString() : msg.timestamp
              }))
            }
          })
        },
        deserialize: (str) => {
          try {
            const { state } = JSON.parse(str)
            return {
              ...state,
              messages: (state.messages || []).map((msg: any) => ({
                ...msg,
                timestamp: typeof msg.timestamp === 'string' ? new Date(msg.timestamp) : msg.timestamp
              }))
            }
          } catch (error) {
            console.error('Failed to deserialize conversation state:', error)
            return {
              messages: [],
              currentProject: null,
              conversationId: null
            }
          }
        }
      }
    )
  )
)
