"use client"

import { useState, useEffect, useRef, memo } from "react"
import { useAppStore } from "@/lib/stores/app-store"
import { useWebSocket } from "@/hooks/use-websocket"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Loader2, Bot, User, CheckCircle, Wifi, WifiOff } from "lucide-react"
import { cn } from "@/lib/utils"

const MessageItem = memo(({ message }) => {
  const getMessageIcon = () => {
    if (message.type === "user") return <User className="w-4 h-4 text-blue-500" />
    if (message.type === "system") return <CheckCircle className="w-4 h-4 text-green-500" />
    return <Bot className="w-4 h-4 text-gray-500" />
  }

  return (
    <div className="p-2 rounded border-b">
      <div className="flex items-center space-x-2">
        {getMessageIcon()}
        <span className="font-semibold text-sm">{message.agent}</span>
      </div>
      <p className="pt-2 pl-6 text-sm">{message.content}</p>
    </div>
  )
})

MessageItem.displayName = "MessageItem"

export function EnhancedChatInterface() {
  const [message, setMessage] = useState("")
  const { connection, conversation, addMessage } = useAppStore()
  const { startProject, isConnected, isReconnecting } = useWebSocket()
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [conversation])

  const handleSendMessage = () => {
    if (!message.trim() || !isConnected) return

    addMessage({ type: "user", agent: "User", content: message })
    startProject(message)
    setMessage("")
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const getConnectionStatusIcon = () => {
    if (isConnected) return <Wifi className="w-4 h-4 text-green-500" />
    if (isReconnecting) return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />
    return <WifiOff className="w-4 h-4 text-red-500" />
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Agent Chat</span>
          {getConnectionStatusIcon()}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-0">
        <ScrollArea className="h-full" ref={scrollAreaRef}>
          <div className="space-y-2 p-4">
            {conversation.map((msg, index) => (
              <MessageItem key={index} message={msg} />
            ))}
          </div>
        </ScrollArea>
        <div className="p-4 border-t">
          <div className="flex items-center space-x-2">
            <Input
              placeholder="Type your message..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={!isConnected}
            />
            <Button onClick={handleSendMessage} disabled={!isConnected || !message.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
