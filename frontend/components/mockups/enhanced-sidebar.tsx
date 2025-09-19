"use client"

import { useState, useEffect } from "react"
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
  ClipboardCheck,
  DraftingCompass,
  Construction,
  TestTube2,
  Rocket,
  AlertCircle,
  CheckCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { SystemHealthIndicator } from "@/components/system-health-indicator"

const enhancedNavigation = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Plan', path: '/requirements', icon: ClipboardCheck, alerts: { ready: 3 } },
  { name: 'Design', path: '/design', icon: DraftingCompass, alerts: { hitl: 2 } },
  { name: 'Build', path: '/dev', icon: Construction, alerts: { error: 1 } },
  { name: 'Validate', path: '/test', icon: TestTube2 },
  { name: 'Launch', path: '/deploy', icon: Rocket },
  { name: 'Logs', path: '/logs', icon: FileText },
  { name: 'Settings', path: '/settings', icon: Settings },
]

const AlertBadge = ({ alerts }) => {
  if (!alerts) return null
  if (alerts.hitl) {
    return <Badge className="bg-amber text-background hover:bg-amber/90">{alerts.hitl} HITL</Badge>
  }
  if (alerts.error) {
    return <Badge className="bg-destructive text-destructive-foreground hover:bg-destructive/90">{alerts.error} Error</Badge>
  }
  if (alerts.ready) {
    return <Badge className="bg-tester text-background hover:bg-tester/90">{alerts.ready} Ready</Badge>
  }
  return null
}

export function EnhancedSidebarMockup() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const pathname = usePathname()

  useEffect(() => {
    const handleResize = () => {
      setIsCollapsed(window.innerWidth < 768)
    }
    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div
      className={cn(
        "flex flex-col bg-card border-r border-border transition-all duration-300 h-full",
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
          <Button variant="ghost" size="sm" onClick={() => setIsCollapsed(!isCollapsed)} className="h-8 w-8 p-0">
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-2 flex-1 overflow-y-auto">
        <div className="space-y-1">
          {enhancedNavigation.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.path

            return (
              <Link key={item.name} href={item.path}>
                <Button
                  variant={isActive ? "secondary" : "ghost"}
                  className={cn(
                    "w-full justify-start h-12 relative",
                    isCollapsed ? "px-2" : "px-3",
                    isActive && "bg-primary/10 text-primary hover:bg-primary/20",
                    !isActive && "hover:bg-secondary/80"
                  )}
                >
                  <Icon className={cn("w-4 h-4", !isCollapsed && "mr-3")} />
                  {!isCollapsed && <span>{item.name}</span>}
                  {!isCollapsed && item.alerts && (
                    <div className="absolute right-2 top-1/2 -translate-y-1/2">
                      <AlertBadge alerts={item.alerts} />
                    </div>
                  )}
                </Button>
              </Link>
            )
          })}
        </div>
      </nav>

      {/* System Health Section */}
      <div className="p-4 border-t border-border flex-shrink-0">
        {!isCollapsed && (
           <div className="space-y-2">
             <h4 className="text-sm font-semibold">System Health</h4>
             <SystemHealthIndicator />
           </div>
        )}
      </div>
    </div>
  )
}
