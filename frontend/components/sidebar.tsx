"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  LayoutDashboard,
  FileText,
  Settings,
  Bot,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  DraftingCompass,
  Code,
  Beaker,
  Rocket,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Separator } from "@/components/ui/separator"
import { SystemHealthIndicator } from "./system-health-indicator"
import { ServicesStatus } from "./services-status"
import { ConnectionStatus } from "./connection-status"

interface SidebarProps {
  activeView: string
  onViewChange: (view: string) => void
}

const processNavigation = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard, alert: false },
  { name: 'Requirements', path: '/requirements', icon: ClipboardList, alert: true },
  { name: 'Design', path: '/design', icon: DraftingCompass, alert: false },
  { name: 'Dev', path: '/dev', icon: Code, alert: true },
  { name: 'Test', path: '/test', icon: Beaker, alert: false },
  { name: 'Deploy', path: '/deploy', icon: Rocket, alert: false },
  { name: 'Logs', path: '/logs', icon: FileText, alert: false },
  { name: 'Settings', path: '/settings', icon: Settings, alert: false },
]

export function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const pathname = usePathname()

  return (
    <div
      className={cn(
        "flex flex-col bg-card border-r border-border transition-all duration-300",
        isCollapsed ? "w-16" : "w-64",
      )}
    >
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg">
                <Bot className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-foreground">BotArmy</h1>
                <p className="text-xs text-muted-foreground">Process View</p>
              </div>
            </div>
          )}
          <Button variant="ghost" size="sm" onClick={() => setIsCollapsed(!isCollapsed)} className="h-8 w-8 p-0" aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}>
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-2">
        <div className="space-y-1">
          {processNavigation.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.path

            return (
              <Link key={item.name} href={item.path}>
                <Button
                  variant={isActive ? "secondary" : "ghost"}
                  className={cn(
                    "w-full justify-start h-10 relative",
                    isCollapsed ? "px-2" : "px-3",
                    isActive && "bg-primary/10 text-primary hover:bg-primary/15",
                  )}
                  onClick={() => onViewChange(item.name)}
                >
                  <Icon className={cn("w-4 h-4", !isCollapsed && "mr-3")} />
                  {!isCollapsed && <span>{item.name}</span>}
                  {!isCollapsed && item.alert && (
                      <div className="absolute right-3 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-destructive"></div>
                  )}
                </Button>
              </Link>
            )
          })}
        </div>
      </nav>

      {/* System Health & Services Section - Moved above the fold, right under navigation */}
      {!isCollapsed && (
        <div className="p-4 border-t border-border space-y-3"> {/* Changed: Moved from bottom, reduced spacing to space-y-3 */}
          <div className="space-y-2"> {/* Added wrapper with tighter spacing */}
            <SystemHealthIndicator />
            <ServicesStatus />
            <ConnectionStatus />
          </div>
        </div>
      )}

      {/* Spacer to push any remaining content to bottom if needed */}
      <div className="flex-1"></div>
    </div>
  )
}
