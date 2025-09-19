"use client"

import { useState, useEffect, useRef, memo } from "react"
import { useLogStore } from "@/lib/stores/log-store"
import { useAgentStore } from "@/lib/stores/agent-store"
import { websocketService } from "@/lib/websocket/websocket-service"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TypingIndicator } from "@/components/ui/typing-indicator"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Loader2, Bot, User, AlertCircle, CheckCircle, Clock, Activity, Wifi, WifiOff } from "lucide-react"
import { cn } from "@/lib/utils"

export interface ChatMessage {
  id: string
  type: 'user' | 'agent' | 'system' | 'error'
  agent?: string
  content: string
  timestamp: Date
  metadata?: Record<string, any>
}

const placeholders = [
  "e.g., Create a Python script to scrape weather data from a website.",
  "e.g., Build a simple todo app with React and a Flask backend.",
  "e.g., Design a database schema for a social media platform.",
  "e.g., Write unit tests for an existing Django application.",
  "e.g., Create a REST API for managing user accounts.",
  "e.g., Build a real-time chat application with WebSockets.",
]

const getMessageIcon = (log: any) => {
  if (log.agent === "User") return <User className="w-4 h-4 text-blue-600" />
  if (log.level === "error") return <AlertCircle className="w-4 h-4 text-red-500" />
  if (log.agent === "System") return <CheckCircle className="w-4 h-4 text-green-500" />
  if (log.metadata?.thinking) return <Activity className="w-4 h-4 text-yellow-500 animate-pulse" />
  return <Bot className="w-4 h-4 text-purple-600" />
}

const getMessageSeverityColor = (level: string, agent: string) => {
  if (agent === "User") return 'bg-blue-50 border-blue-200 text-blue-900'
  if (level === 'error') return 'bg-red-50 border-red-200 text-red-900'
  if (level === 'warn') return 'bg-yellow-50 border-yellow-200 text-yellow-900'
  if (level === 'info') return 'bg-green-50 border-green-200 text-green-900'
  return 'bg-gray-50 border-gray-200 text-gray-900'
}

const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

interface MessageItemProps {
  log: any
  index: number
}

const MessageItem = memo(({ log, index }: MessageItemProps) => {
  return (
    <div className="px-4 py-2">
<<<<<<< HEAD
<<<<<<< HEAD
      <div 
=======
      <div
>>>>>>> origin/feature/add-test-framework
=======
      <div 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
        className={cn(
          "flex items-start space-x-3 p-3 rounded-lg border transition-all duration-200 hover:shadow-sm",
          getMessageSeverityColor(log.level, log.agent)
        )}
      >
        {/* Message Icon */}
        <div className="flex-shrink-0 mt-0.5">
          {getMessageIcon(log)}
        </div>

        {/* Message Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-sm">{log.agent}</span>
              {log.level === 'error' && (
                <Badge variant="destructive" className="text-xs">Error</Badge>
              )}
              {log.metadata?.type === 'user_input' && (
                <Badge variant="outline" className="text-xs">Input</Badge>
              )}
              {log.metadata?.thinking && (
                <Badge variant="secondary" className="text-xs">Thinking</Badge>
              )}
              {log.metadata?.progress && (
                <Badge variant="default" className="text-xs">
                  {Math.round(log.metadata.progress * 100)}%
                </Badge>
              )}
            </div>
            <span className="text-xs opacity-70">
              {formatTimestamp(log.timestamp)}
            </span>
          </div>

          <div className="text-sm whitespace-pre-wrap leading-relaxed">
            {log.message}
          </div>

          {/* Progress indicator for agent tasks */}
          {log.metadata?.progress && (
            <div className="mt-2">
              <div className="w-full bg-gray-200 rounded-full h-1.5">
<<<<<<< HEAD
<<<<<<< HEAD
                <div 
=======
                <div
>>>>>>> origin/feature/add-test-framework
=======
                <div 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
                  className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${log.metadata.progress * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Show task details if available */}
          {log.metadata?.task && (
            <div className="mt-2 p-2 bg-white rounded border text-xs">
              <span className="font-medium">Task: </span>
              {log.metadata.task}
            </div>
          )}
        </div>
      </div>
    </div>
  )
})

MessageItem.displayName = "MessageItem"

interface EnhancedChatInterfaceProps {
  initialMessage?: string
}

export function EnhancedChatInterface({ initialMessage = "" }: EnhancedChatInterfaceProps) {
  const [message, setMessage] = useState(initialMessage)
  const [isLoading, setIsLoading] = useState(false)
  const [placeholder, setPlaceholder] = useState(placeholders[0])
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const { logs, addLog } = useLogStore()
  const { agents } = useAgentStore()

  const isAgentThinking = agents.some(agent => agent.is_thinking)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')

  useEffect(() => {
    setMessage(initialMessage)
  }, [initialMessage])

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholder(placeholders[Math.floor(Math.random() * placeholders.length)])
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  // Monitor WebSocket connection status
  useEffect(() => {
    const checkConnection = () => {
      try {
        setConnectionStatus(websocketService.getConnectionStatus())
      } catch (error) {
        setConnectionStatus('disconnected')
      }
    }

    checkConnection()
    const interval = setInterval(checkConnection, 1000)
    return () => clearInterval(interval)
  }, [])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [logs])

  const handleSendMessage = async () => {
    if (!message.trim() || isLoading || message.length < 10 || message.length > 1000) return
    if (connectionStatus !== 'connected') {
      addLog({
        id: `error-${Date.now()}`,
        agent: "System",
        level: "error",
        message: "❌ Cannot send message: Not connected to server",
        timestamp: new Date().toISOString(),
        metadata: { type: 'connection_error' }
      })
      return
    }

    const userMessage = message.trim()
    setMessage("")
    setIsLoading(true)

    // Add user message to chat
    addLog({
      id: `user-${Date.now()}`,
      agent: "User",
      level: "info",
      message: userMessage,
      timestamp: new Date().toISOString(),
      metadata: { type: 'user_input' }
    })

    // Add a loading message
    addLog({
      id: `system-${Date.now()}`,
      agent: "System",
      level: "info",
      message: "Initializing agents...",
      timestamp: new Date().toISOString(),
      metadata: { thinking: true }
    })

    try {
      // Send project start command
      await websocketService.startProject(userMessage)
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
      
      // Add confirmation message
      addLog({
        id: `system-${Date.now()}`,
        agent: "System", 
<<<<<<< HEAD
=======

      // Add confirmation message
      addLog({
        id: `system-${Date.now()}`,
        agent: "System",
>>>>>>> origin/feature/add-test-framework
=======
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
        level: "info",
        message: "🚀 Project started! Agents are beginning work...",
        timestamp: new Date().toISOString(),
        metadata: { type: 'system_confirmation' }
      })

    } catch (error: any) {
      console.error("Failed to send message:", error)
<<<<<<< HEAD
<<<<<<< HEAD
      
=======

>>>>>>> origin/feature/add-test-framework
=======
      
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
      // Add error message to chat
      addLog({
        id: `error-${Date.now()}`,
        agent: "System",
        level: "error",
        message: `❌ Failed to start project: ${error.message || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        metadata: { type: 'error', error: error.message }
      })
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

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Wifi className="w-4 h-4 text-green-500" />
      case 'connecting':
        return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />
      default:
        return <WifiOff className="w-4 h-4 text-red-500" />
    }
  }

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected'
      case 'connecting':
        return 'Connecting...'
      default:
        return 'Disconnected'
    }
  }

  const isInputDisabled = isLoading || connectionStatus !== 'connected'
  const canSend = message.trim() && message.length >= 10 && message.length <= 1000 && !isInputDisabled

  return (
    <Card className="min-h-[600px] flex-1 flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5" />
            Agent Chat
          </div>
          <div className="flex items-center gap-2 text-sm font-normal">
            {getConnectionStatusIcon()}
            <span className={cn(
              "text-xs",
              connectionStatus === 'connected' ? 'text-green-600' :
              connectionStatus === 'connecting' ? 'text-yellow-600' : 'text-red-600'
            )}>
              {getConnectionStatusText()}
            </span>
          </div>
        </CardTitle>
      </CardHeader>
<<<<<<< HEAD
<<<<<<< HEAD
      
=======

>>>>>>> origin/feature/add-test-framework
=======
      
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
      <CardContent className="flex-1 flex flex-col p-0">
        {/* Chat Messages Area */}
        <div className="flex-1">
          {logs.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">Welcome to BotArmy!</p>
              <p>Enter your project description below to get started.</p>
              <p className="text-sm mt-2">
                Status: <span className={cn(
                  connectionStatus === 'connected' ? 'text-green-600' : 'text-red-600'
                )}>
                  {getConnectionStatusText()}
                </span>
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[400px]" ref={scrollAreaRef}>
              {logs.map((log, index) => (
                <MessageItem key={log.id || index} log={log} index={index} />
              ))}
              {isAgentThinking && (
                <div className="flex items-center space-x-3 p-3 mx-4">
                  <Bot className="w-4 h-4" />
                  <TypingIndicator />
                  <span className="text-sm text-muted-foreground">Agents are working...</span>
                </div>
              )}
            </ScrollArea>
          )}
        </div>
<<<<<<< HEAD
<<<<<<< HEAD
        
        <Separator />
        
=======

        <Separator />

>>>>>>> origin/feature/add-test-framework
=======
        
        <Separator />
        
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
        {/* Message Input Area */}
        <div className="p-4">
          <div className="relative">
            <Input
              placeholder={connectionStatus === 'connected' ? placeholder : "Connect to server to send messages..."}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isInputDisabled}
              className={cn(
                "flex-1 pr-20",
                connectionStatus !== 'connected' && "opacity-50"
              )}
              maxLength={1000}
            />
            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
              <span className={cn(
                "text-xs",
<<<<<<< HEAD
<<<<<<< HEAD
                message.length > 900 ? "text-red-500" : 
=======
                message.length > 900 ? "text-red-500" :
>>>>>>> origin/feature/add-test-framework
=======
                message.length > 900 ? "text-red-500" : 
>>>>>>> 888a13e8888c2a85282e3309ece813befd8c920e
                message.length > 700 ? "text-yellow-500" : "text-muted-foreground"
              )}>
                {message.length} / 1000
              </span>
            </div>
          </div>
          <div className="flex justify-between items-center mt-2">
            <p className="text-xs text-muted-foreground">
              {message.length < 10 && message.length > 0 && (
                <span className="text-yellow-600">Minimum 10 characters • </span>
              )}
              Press Enter to send • Shift+Enter for new line
            </p>
            <Button
              onClick={handleSendMessage}
              disabled={!canSend}
              size="sm"
              className={cn(
                !canSend && "opacity-50 cursor-not-allowed"
              )}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Send
                </>
              )}
            </Button>
          </div>
          {connectionStatus !== 'connected' && (
            <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
              ⚠️ Waiting for connection to server...
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}