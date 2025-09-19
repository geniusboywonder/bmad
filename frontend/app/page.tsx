"use client"

import { useAppStore } from "@/lib/stores/app-store"
import { MainLayout } from "@/components/main-layout"
import { Button } from "@/components/ui/button"
import { Zap } from "lucide-react"
import { EnhancedProcessSummaryMockup } from "@/components/mockups/enhanced-process-summary"
import { EnhancedChatInterface } from "@/components/chat/enhanced-chat-interface"
import { RecentActivities } from "@/components/mockups/recent-activities"
import CopilotChat from "@/components/chat/copilot-chat"

export default function HomePage() {
  const { addMessage } = useAppStore()

  const handleStartProject = () => {
    console.log("Starting new project...")
    // For now, we will just add a message to the conversation.
    addMessage({ type: "system", agent: "System", content: "New project started!" })
  }

  return (
    <MainLayout>
      <div className="p-6 space-y-8">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-foreground">BotArmy Agentic Builder</h1>
              <p className="text-lg text-muted-foreground">
                An workflow overview with process tracking, agent communication, and activity monitoring.
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Button 
                onClick={handleStartProject}
                className="bg-primary hover:bg-primary/90"
              >
                <Zap className="w-4 h-4 mr-2" />
                Start New Project
              </Button>
            </div>
          </div>
        </div>

        <div className="grid gap-8 grid-cols-1 xl:grid-cols-2">
          <div className="min-h-[500px]">
            <EnhancedProcessSummaryMockup />
          </div>
          
          <div className="min-h-[500px]">
            <CopilotChat />
          </div>
        </div>

        <div className="space-y-4">
          <div className="border-t border-border pt-8">
            <h2 className="text-xl font-semibold text-foreground mb-4">Activity Timeline</h2>
            <RecentActivities />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
