"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Bot,
  User,
  CheckCircle,
  ChevronDown,
  ChevronsRightLeft,
  Send,
  Loader,
  X,
  Wifi,
  GripHorizontal,
  ClipboardCheck,
  DraftingCompass,
  Construction,
  TestTube2,
  Rocket,
} from "lucide-react"
import { cn } from "@/lib/utils"

// --- Mock Data and Types ---
type MessageType = "user" | "agent" | "system"

// --- Role-based Icon Mapping ---
const getRoleIcon = (sender: string) => {
  const senderLower = sender.toLowerCase()
  if (senderLower.includes('analyst')) return <ClipboardCheck className="w-4 h-4" />
  if (senderLower.includes('architect')) return <DraftingCompass className="w-4 h-4" />
  if (senderLower.includes('developer')) return <Construction className="w-4 h-4" />
  if (senderLower.includes('tester')) return <TestTube2 className="w-4 h-4" />
  if (senderLower.includes('deployer')) return <Rocket className="w-4 h-4" />
  
  // Fallbacks
  if (sender === 'User') return <User className="w-4 h-4" />
  if (sender === 'System') return <CheckCircle className="w-4 h-4" />
  return <Bot className="w-4 h-4" /> // Default for any other agents
}
interface ChatMessage {
  id: string
  type: MessageType
  sender: string
  content: string | React.ReactNode
  timestamp: string
  collapsed?: boolean
}

const mockMessages: ChatMessage[] = [
  { id: "1", type: "user", sender: "User", content: "Create a todo application with React frontend", timestamp: "15:32", collapsed: true },
  { id: "2", type: "system", sender: "System", content: "Starting new project workflow...", timestamp: "15:33" },
  { id: "3", type: "agent", sender: "Analyst", content: (
    <ul className="list-disc list-inside space-y-1">
      <li>I'll analyze your requirements...</li>
      <li>- User authentication needed</li>
      <li>- CRUD operations for todos</li>
      <li>- React frontend preference noted</li>
    </ul>
  ), timestamp: "15:33" },
  { id: "4", type: "user", sender: "User", content: "Also add user preferences and themes", timestamp: "15:34" },
  { id: "5", type: "agent", sender: "Analyst", content: "✅ Analysis complete. Key features identified.", timestamp: "15:35", collapsed: true },
  { id: "6", type: "agent", sender: "Architect", content: "⚡ Currently designing system architecture...", timestamp: "15:36" },
  { id: "7", type: "agent", sender: "Developer", content: "Setting up project structure with Create React App...", timestamp: "15:37" },
  { id: "8", type: "user", sender: "User", content: "Can we use TypeScript instead?", timestamp: "15:38" },
  { id: "9", type: "agent", sender: "Developer", content: "Absolutely! Converting to TypeScript setup now.", timestamp: "15:39" },
  { id: "10", type: "system", sender: "System", content: "Project scaffolding complete", timestamp: "15:40" },
  { id: "11", type: "agent", sender: "Tester", content: "Writing initial test cases for core functionality", timestamp: "15:41" },
  { id: "12", type: "agent", sender: "Deployer", content: "Preparing deployment configuration...", timestamp: "15:42" },
]

// --- Multi-Corner Resizable Hook ---
const useMultiResizable = (initialWidth = 400, initialHeight = 400) => {
  const getInitialDimensions = () => {
    if (typeof window === 'undefined') return { width: initialWidth, height: initialHeight, x: 0, y: 0 }
    const isMobile = window.innerWidth < 768
    return { 
      width: isMobile ? 300 : initialWidth,
      height: isMobile ? 300 : initialHeight,
      x: 0,
      y: 0
    }
  }
  
  const [dimensions, setDimensions] = useState(getInitialDimensions)
  const containerRef = useRef<HTMLDivElement>(null)

  const createResizeHandler = useCallback((corner: 'nw' | 'ne' | 'sw' | 'se') => {
    return (e: React.MouseEvent) => {
      e.preventDefault()
      e.stopPropagation()
      
      const startX = e.clientX
      const startY = e.clientY
      const startWidth = dimensions.width
      const startHeight = dimensions.height
      const startPosX = dimensions.x
      const startPosY = dimensions.y

      const handleMouseMove = (moveEvent: MouseEvent) => {
        moveEvent.preventDefault()
        
        const deltaX = moveEvent.clientX - startX
        const deltaY = moveEvent.clientY - startY
        
        let newWidth = startWidth
        let newHeight = startHeight
        let newX = startPosX
        let newY = startPosY

        // Handle resizing based on corner
        if (corner === 'nw') {
          // Northwest: resize from top-left, move position and adjust size
          newWidth = startWidth - deltaX
          newHeight = startHeight - deltaY
          newX = startPosX + deltaX
          newY = startPosY + deltaY
        } else if (corner === 'ne') {
          // Northeast: resize from top-right, move Y position only
          newWidth = startWidth + deltaX
          newHeight = startHeight - deltaY
          newY = startPosY + deltaY
        } else if (corner === 'sw') {
          // Southwest: resize from bottom-left, move X position only
          newWidth = startWidth - deltaX
          newHeight = startHeight + deltaY
          newX = startPosX + deltaX
        } else if (corner === 'se') {
          // Southeast: resize from bottom-right, no position change
          newWidth = startWidth + deltaX
          newHeight = startHeight + deltaY
        }

        // Apply constraints - prevent resizing beyond screen bounds
        const maxWidth = Math.min(window.innerWidth - 40, 1200)
        const maxHeight = Math.min(window.innerHeight - 120, 800)
        const minWidth = 250
        const minHeight = 200

        // Adjust for minimum sizes and position corrections
        if (newWidth < minWidth) {
          if (corner.includes('w')) {
            newX = newX - (minWidth - newWidth)
          }
          newWidth = minWidth
        }
        if (newWidth > maxWidth) {
          if (corner.includes('w')) {
            newX = newX + (newWidth - maxWidth)
          }
          newWidth = maxWidth
        }

        if (newHeight < minHeight) {
          if (corner.includes('n')) {
            newY = newY - (minHeight - newHeight)
          }
          newHeight = minHeight
        }
        if (newHeight > maxHeight) {
          if (corner.includes('n')) {
            newY = newY + (newHeight - maxHeight)
          }
          newHeight = maxHeight
        }

        // Use requestAnimationFrame for smoother updates
        requestAnimationFrame(() => {
          setDimensions({ width: newWidth, height: newHeight, x: newX, y: newY })
        })
      }

      const handleMouseUp = () => {
        document.removeEventListener("mousemove", handleMouseMove)
        document.removeEventListener("mouseup", handleMouseUp)
      }

      document.addEventListener("mousemove", handleMouseMove)
      document.addEventListener("mouseup", handleMouseUp)
    }
  }, [dimensions])

  return { 
    dimensions, 
    containerRef,
    createResizeHandler
  }
}

// --- Message Component ---
const MessageItem = ({ message, onToggleCollapse }: { message: ChatMessage; onToggleCollapse: (id: string) => void }) => {
  const getMessageIcon = () => {
    if (message.type === 'user') return <User className="w-4 h-4" />
    if (message.type === 'system') return <CheckCircle className="w-4 h-4" />
    return getRoleIcon(message.sender) // Use role-based icon for agents
  }
  const colors = {
    user: "bg-user/10 border-user/20 text-user",
    agent: "bg-secondary border-border text-foreground", 
    system: "bg-system/10 border-system/20 text-system",
  }

  return (
    <div className={cn("p-2 rounded-lg border", colors[message.type])}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getMessageIcon()}
          <span className="font-semibold text-sm">{message.sender}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-700">{message.timestamp}</span>
          <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => onToggleCollapse(message.id)}>
            <ChevronDown className={cn("w-4 h-4 transition-transform", !message.collapsed && "rotate-180")} />
          </Button>
        </div>
      </div>
      {!message.collapsed && (
        <div className="pt-2 pl-6 text-sm whitespace-pre-wrap text-current">{message.content}</div>
      )}
    </div>
  )
}

// --- Inline Status Component ---
const InlineStatus = ({ onDismiss }: { onDismiss: () => void }) => {
  return (
    <div className="flex items-center space-x-2 bg-user/10 border-user/20 text-user px-3 py-1 rounded-full">
      <Loader className="w-4 h-4 animate-spin text-user" />
      <div className="flex items-center space-x-1">
        <span className="text-sm font-medium">Architect is thinking...</span>
        <span className="text-xs opacity-70">ETA: 30s</span>
      </div>
      <Button size="icon" variant="ghost" className="h-5 w-5 text-user hover:bg-user/10" onClick={onDismiss}>
        <X className="w-3 h-3" />
      </Button>
    </div>
  )
}

// --- Main Chat Interface Mockup ---
export function EnhancedChatInterfaceMockup() {
  const { 
    dimensions, 
    containerRef,
    createResizeHandler
  } = useMultiResizable(500, 400)
  const [messages, setMessages] = useState(mockMessages)
  const [showOverlay, setShowOverlay] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Show overlay for demonstration
    const timer = setTimeout(() => setShowOverlay(true), 2000)
    return () => clearTimeout(timer)
  }, [])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [messages])

  const toggleCollapse = (id: string) => {
    setMessages(msgs =>
      msgs.map(msg => (msg.id === id ? { ...msg, collapsed: !msg.collapsed } : msg))
    )
  }

  return (
    <Card 
      ref={containerRef}
      style={{ 
        width: `${dimensions.width}px`,
        height: `${dimensions.height}px`,
        transform: `translate(${dimensions.x}px, ${dimensions.y}px)`,
      }} 
      className="flex flex-col relative overflow-hidden border-2 shadow-lg"
    >
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Bot className="w-5 h-5" />
            <span>Agent Chat</span>
          </CardTitle>
          <div className="flex-1 flex justify-center">
            {showOverlay && <InlineStatus onDismiss={() => setShowOverlay(false)} />}
          </div>
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <Wifi className="w-4 h-4 text-tester" />
            <span>Connected</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
        <div className="flex-1 relative min-h-0">
          <ScrollArea className="h-full w-full" ref={scrollAreaRef}>
            <div className="p-4 space-y-4">
              {messages.map(msg => (
                <MessageItem key={msg.id} message={msg} onToggleCollapse={toggleCollapse} />
              ))}
            </div>
          </ScrollArea>
        </div>

        <div className="p-4 border-t flex-shrink-0">
          <div className="flex items-center space-x-2">
            <Input 
              placeholder="Type your message..." 
              className="flex-1 ring-2 ring-teal/60 focus:ring-teal/80 border-teal/20" 
            />
            <Button className="bg-teal hover:bg-teal/90 text-white">
              <Send className="w-4 h-4 mr-2" />
              Send
            </Button>
          </div>
        </div>
      </CardContent>

      {/* Corner Resize Handles - properly positioned at card corners */}
      {/* Top-left corner */}
      <div
        onMouseDown={createResizeHandler('nw')}
        className="absolute top-0 left-0 w-4 h-4 cursor-nw-resize bg-user/30 hover:bg-user/50 border border-user transition-colors z-30"
        style={{ transform: 'translate(-2px, -2px)' }}
      >
        <div className="absolute top-0.5 left-0.5 w-2 h-2 border-l border-t border-user"></div>
      </div>
      
      {/* Top-right corner */}
      <div
        onMouseDown={createResizeHandler('ne')}
        className="absolute top-0 right-0 w-4 h-4 cursor-ne-resize bg-user/30 hover:bg-user/50 border border-user transition-colors z-30"
        style={{ transform: 'translate(2px, -2px)' }}
      >
        <div className="absolute top-0.5 right-0.5 w-2 h-2 border-r border-t border-user"></div>
      </div>
      
      {/* Bottom-left corner */}
      <div
        onMouseDown={createResizeHandler('sw')}
        className="absolute bottom-0 left-0 w-4 h-4 cursor-sw-resize bg-user/30 hover:bg-user/50 border border-user transition-colors z-30"
        style={{ transform: 'translate(-2px, 2px)' }}
      >
        <div className="absolute bottom-0.5 left-0.5 w-2 h-2 border-l border-b border-user"></div>
      </div>
      
      {/* Bottom-right corner */}
      <div
        onMouseDown={createResizeHandler('se')}
        className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize bg-user/30 hover:bg-user/50 border border-user transition-colors z-30"
        style={{ transform: 'translate(2px, 2px)' }}
      >
        <div className="absolute bottom-0.5 right-0.5 w-2 h-2 border-r border-b border-user"></div>
        <ChevronsRightLeft className="w-2 h-2 absolute bottom-0 right-0 text-user" />
      </div>
    </Card>
  )
}
