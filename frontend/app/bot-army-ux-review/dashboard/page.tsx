"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertTriangle, Bot, Clock } from "lucide-react"
import { EnhancedProcessSummaryMockup } from "@/components/mockups/enhanced-process-summary"
import { EnhancedChatInterfaceMockup } from "@/components/mockups/enhanced-chat-interface"
import { RecentActivities } from "@/components/mockups/recent-activities"




export default function DashboardMockupPage() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Dashboard Overview</h1>
        <p className="text-lg text-gray-600">
          Comprehensive workflow dashboard with process tracking, agent communication, and activity monitoring.
        </p>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid gap-8 grid-cols-1 xl:grid-cols-2">
        {/* Process Summary */}
        <div className="min-h-[500px]">
          <EnhancedProcessSummaryMockup />
        </div>
        
        {/* Agent Chat Interface */}
        <div className="min-h-[500px]">
          <EnhancedChatInterfaceMockup />
        </div>
      </div>

      {/* Recent Activities Section */}
      <div className="space-y-4">
        <div className="border-t border-gray-200 pt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Activity Timeline</h2>
          <RecentActivities />
        </div>
      </div>
    </div>
  )
}
