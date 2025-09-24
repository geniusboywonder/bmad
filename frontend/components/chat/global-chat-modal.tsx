"use client"

import { useState, useEffect, useRef, memo, useMemo } from "react"
import { useConversationStore } from "@/lib/stores/conversation-store"
import { useAgentStore } from "@/lib/stores/agent-store"
import { websocketService } from "@/lib/services/websocket/websocket-service"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog"
import { TypingIndicator } from "@/components/ui/typing-indicator"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Loader2, Bot, User, CheckCircle, Wifi, WifiOff, MessageSquare } from "lucide-react"
import { cn } from "@/lib/utils"

// Re-using the ChatMessage type and helper functions from enhanced-chat-interface
export interface ChatMessage {
  id: string
  type: 'user' | 'agent' | 'system' | 'error'
  agent?: string
  content: string
  timestamp: Date
  metadata?: Record<string, any>
}

const getMessageIcon = (message: ChatMessage) => {
  if (message.type === "user") return <User className="w-4 h-4 text-blue-600" />
  if (message.type === "system") return <CheckCircle className="w-4 h-4 text-green-500" />
  return <Bot className="w-4 h-4 text-purple-600" />
}

const getMessageSeverityColor = (type: ChatMessage['type']) => {
  if (type === "user") return 'bg-blue-50 border-blue-200 text-blue-900'
  if (type === "system") return 'bg-green-50 border-green-200 text-green-900'
  return 'bg-gray-50 border-gray-200 text-gray-900'
}

const formatTimestamp = (timestamp: Date | string) => {
  try {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp)
    if (isNaN(date.getTime())) return "00:00:00"
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return "00:00:00"
  }
}

const MessageItem = memo(({ message }: { message: ChatMessage }) => {
  const safeTimestamp = useMemo(() => {
    try {
      if (message.timestamp instanceof Date) return message.timestamp
      if (typeof message.timestamp === 'string') {
        const date = new Date(message.timestamp)
        if (!isNaN(date.getTime())) return date
      }
      return new Date()
    } catch { return new Date() }
  }, [message.timestamp])

  return (
    <div className="px-4 py-2">
      <div className={cn("flex items-start space-x-3 p-3 rounded-lg border", getMessageSeverityColor(message.type))}>
        <div className="flex-shrink-0 mt-0.5">{getMessageIcon(message)}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold text-sm">{message.agent}</span>
            <span className="text-xs opacity-70">{formatTimestamp(safeTimestamp)}</span>
          </div>
          <div className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</div>
        </div>
      </div>
    </div>
  )
})
MessageItem.displayName = "MessageItem"

interface GlobalChatModalProps {
  isOpen: boolean
  onOpenChange: (isOpen: boolean) => void
}

export function GlobalChatModal({ isOpen, onOpenChange }: GlobalChatModalProps) {
  const [message, setMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const { messages, addMessage } = useConversationStore()
  const { agents } = useAgentStore()

  const isAgentThinking = agents.some(agent => agent.status === 'thinking' || agent.status === 'active')

  useEffect(() => {
    const checkConnection = () => {
      try {
        const status = websocketService.getConnectionStatus()
        setConnectionStatus(status.connected ? 'connected' : status.reconnecting ? 'connecting' : 'disconnected')
      } catch { setConnectionStatus('disconnected') }
    }
    checkConnection()
    const interval = setInterval(checkConnection, 1000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) scrollContainer.scrollTop = scrollContainer.scrollHeight
    }
  }, [messages])

  const handleSendMessage = async () => {
    if (!message.trim() || isLoading || connectionStatus !== 'connected') return

    const userMessage = message.trim()
    setMessage("")
    setIsLoading(true)
    addMessage({ agent: "User", type: "user", content: userMessage })

    try {
      websocketService.sendChatMessage(userMessage)
    } catch (error: any) {
      addMessage({ agent: "System", type: "system", content: `❌ Error: ${error.message || 'Unknown error'}` })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const isInputDisabled = isLoading || connectionStatus !== 'connected'
  const canSend = message.trim() && !isInputDisabled

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[625px] flex flex-col h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="w-5 h-5" />
            Global Agent Chat
          </DialogTitle>
          <DialogDescription>
            Communicate with the agent team in real-time.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full" ref={scrollAreaRef}>
            {messages.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No messages yet. Send a message to start the conversation.</p>
              </div>
            ) : (
              messages.map((msg) => <MessageItem key={msg.id} message={msg} />)
            )}
            {isAgentThinking && (
              <div className="flex items-center space-x-3 p-3 mx-4">
                <Bot className="w-4 h-4" />
                <TypingIndicator />
                <span className="text-sm text-muted-foreground">Agents are working...</span>
              </div>
            )}
          </ScrollArea>
        </div>

        <DialogFooter className="flex-col gap-2">
           <div className="relative">
            <Input
              placeholder="Type your message here..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isInputDisabled}
              className="pr-20"
            />
          </div>
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                {connectionStatus === 'connected' ? <Wifi className="w-4 h-4 text-green-500" /> : <WifiOff className="w-4 h-4 text-red-500" />}
                <span>{connectionStatus}</span>
            </div>
            <Button onClick={handleSendMessage} disabled={!canSend} size="sm">
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span className="ml-2">Send</span>
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
