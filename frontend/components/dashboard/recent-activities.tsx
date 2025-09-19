"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { getStatusBadgeClasses, getAgentBadgeClasses } from "@/lib/utils/badge-utils"
import {
  CheckCircle,
  Clock,
  User,
  AlertTriangle,
  ClipboardCheck,
  DraftingCompass,
  Construction,
  TestTube2,
  Rocket,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useActivities } from "@/hooks/use-activities"

const getRoleIcon = (role: string, size = "w-4 h-4") => {
  const roleLower = role.toLowerCase()
  if (roleLower.includes('analyst')) return <ClipboardCheck className={`${size} text-analyst`} />
  if (roleLower.includes('architect')) return <DraftingCompass className={`${size} text-architect`} />
  if (roleLower.includes('developer')) return <Construction className={`${size} text-developer`} />
  if (roleLower.includes('tester')) return <TestTube2 className={`${size} text-tester`} />
  if (roleLower.includes('deployer')) return <Rocket className={`${size} text-deployer`} />
  if (roleLower === 'human' || roleLower === 'user') return <User className={`${size} text-user`} />
  return <CheckCircle className={`${size} text-muted-foreground`} />
}

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'completed': return <CheckCircle className="w-3 h-3 text-tester" />
    case 'approved': return <CheckCircle className="w-3 h-3 text-analyst" />
    case 'waiting': return <Clock className="w-3 h-3 text-amber" />
    case 'alert': return <AlertTriangle className="w-3 h-3 text-developer" />
    default: return <Clock className="w-3 h-3 text-muted-foreground" />
  }
}

export function RecentActivities() {
  const { activities: recentActivities, loading: activitiesLoading, error: activitiesError } = useActivities()
  return (
    <Card className="h-full shadow-sm border-2 border-border/50 bg-gradient-to-br from-card to-card/90">
      <CardHeader className="pb-4 border-b border-border/50">
        <CardTitle className="text-lg font-bold flex items-center gap-2">
          <div className="w-1 h-6 bg-teal rounded-full"></div>
          Recent Activities
          <Badge variant="outline" className="ml-auto text-xs text-muted-foreground border-muted-foreground/30">
            {recentActivities.length} items
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {activitiesError && (
          <div className="p-4 text-red-500 text-sm">
            Error loading activities: {activitiesError}
          </div>
        )}
        {activitiesLoading ? (
          <div className="p-4 space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4 p-3 rounded-lg">
                <div className="w-6 h-6 bg-gray-200 rounded-full animate-pulse"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4"></div>
                  <div className="h-3 bg-gray-200 rounded animate-pulse w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        ) : recentActivities.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground">
            No recent activities found
          </div>
        ) : (
          <ScrollArea className="h-80">
            <div className="p-4 space-y-4">
              {recentActivities.map((activity, index) => (
              <div key={activity.id} className={cn(
                "group relative flex items-start space-x-4 p-3 rounded-lg transition-all duration-200",
                "hover:bg-secondary/50 hover:shadow-sm hover:border-l-4 hover:border-l-teal",
                index < 3 ? "bg-secondary/20 border border-border/30" : "hover:bg-secondary/30",
                index >= 5 && "opacity-70"
              )}>
                {/* Enhanced Timeline dot with gradient */}
                <div className="flex flex-col items-center flex-shrink-0">
                  <div className={cn(
                    "flex items-center justify-center rounded-full border-2 border-background shadow-sm transition-all group-hover:scale-110",
                    index < 3 ? "w-8 h-8 bg-gradient-to-br from-teal/20 to-teal/10" : "w-6 h-6 bg-gradient-to-br from-secondary to-card",
                    index < 3 ? "ring-2 ring-teal/30" : "ring-1 ring-border/50"
                  )}>
                    {getActivityIcon(activity.type)}
                  </div>
                  {/* Connecting line for items except the last */}
                  {index < recentActivities.length - 1 && (
                    <div className={cn(
                      "w-px bg-gradient-to-b transition-all duration-300",
                      index < 2 ? "h-12 from-teal/40 via-teal/20 to-border/50" : "h-10 from-border/50 to-transparent"
                    )}></div>
                  )}
                </div>

                {/* Activity content with enhanced layout */}
                <div className="flex-1 min-w-0 pt-0.5">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <Badge variant="muted" size="sm" className={getAgentBadgeClasses(activity.actor)}>
                      {getRoleIcon(activity.actor, "w-2.5 h-2.5 mr-0.5")}
                      {activity.actor}
                    </Badge>
                    <Badge variant="muted" size="sm" className={getStatusBadgeClasses(activity.type)}>
                      {activity.type.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm text-foreground group-hover:text-teal-700 dark:group-hover:text-teal-300 transition-colors leading-relaxed">
                      {activity.action}
                    </p>
                    <span className="text-xs text-muted-foreground font-mono whitespace-nowrap">
                      {activity.time}
                    </span>
                  </div>
                </div>
              </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}