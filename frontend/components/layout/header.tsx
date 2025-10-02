"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import {
  Bell,
  MessageSquare,
  Search,
  User as UserIcon,
  Bot,
  AlertTriangle,
  X,
  ChevronDown,
  Settings,
} from "lucide-react"
import { useNotificationStore } from "@/lib/stores/notification-store"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { SystemHealthIndicator } from "@/components/system-health-indicator"
import { useHITLStore } from "@/lib/stores/hitl-store"

export function Header() {
    const { alerts, dismissAlert } = useNotificationStore()
    const { addRequest } = useHITLStore()
    const [expandedAlerts, setExpandedAlerts] = useState<string[]>([])
    const [isClient, setIsClient] = useState(false)

    const visibleAlerts = alerts.slice(0, 2)

    useEffect(() => {
      setIsClient(true)
    }, [])

    const toggleExpanded = (alertId: string) => {
      const alert = alerts.find(a => a.id === alertId)
      
      // Check if this is a HITL-related alert that should create a HITL request
      if (alert && alertId.startsWith('hitl-')) {
        // Create a HITL request based on the alert
        const agentName = alert.stage === 'Design' ? 'Architect' : 
                         alert.stage === 'Validate' ? 'Tester' : 
                         'Developer'
        
        addRequest({
          agentName,
          decision: alert.message,
          context: { 
            alertId: alertId,
            stage: alert.stage,
            originalAlert: true 
          },
          priority: alert.priority as 'low' | 'medium' | 'high' | 'urgent'
        })
        return
      }
      
      // Regular alert expansion
      setExpandedAlerts(prev => 
        prev.includes(alertId) 
          ? prev.filter(id => id !== alertId)
          : [...prev, alertId]
      )
    }

  return (
    <>
        <header className="bg-card border-b">
          {/* Main Header */}
          <div className="flex h-14 items-center px-6">
        
        {/* Site Title / Logo - Fixed width */}
        <div className="flex items-center gap-2 flex-shrink-0 w-32">
            <Link href="/" className="flex items-center gap-2">
                <Bot className="h-6 w-6 flex-shrink-0" />
                <span className="text-lg font-semibold hidden md:block whitespace-nowrap">BotArmy</span>
            </Link>
        </div>

        {/* Search Bar - Center with fixed width */}
        <div className="flex-1 px-8 max-w-lg mx-auto">
            <div className="relative w-full">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground flex-shrink-0" />
                <Input
                    type="search"
                    placeholder="Search tasks, artifacts..."
                    className="pl-10 text-sm w-full"
                />
            </div>
        </div>


        {/* Actions - Right Side with better spacing and fixed overlapping */}
        <div className="flex items-center gap-2 flex-shrink-0 min-w-0">

            {/* Notifications Button */}
            <Button
              variant="ghost"
              size="icon"
              className="flex-shrink-0"
              title="Notifications"
            >
                <Bell className="h-5 w-5" />
                <span className="sr-only">Notifications</span>
            </Button>

            {/* Settings Button */}
            <Link href="/settings">
              <Button
                variant="ghost"
                size="icon"
                className="flex-shrink-0"
                title="Settings"
              >
                  <Settings className="h-5 w-5" />
                  <span className="sr-only">Settings</span>
              </Button>
            </Link>

            {/* System Health Indicator - Better responsive handling */}
            <div className="hidden md:flex items-center flex-shrink-0">
                <SystemHealthIndicator />
            </div>

            {/* User Menu - Improved spacing */}
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="rounded-full flex-shrink-0"
                    >
                        <Avatar className="h-8 w-8">
                            <AvatarImage src="/placeholder-user.jpg" alt="@username" />
                            <AvatarFallback>U</AvatarFallback>
                        </Avatar>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuLabel>My Account</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>Settings</DropdownMenuItem>
                    <DropdownMenuItem>Support</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>Logout</DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        </header>
    </>
  )
}