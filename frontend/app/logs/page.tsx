"use client"

import { MainLayout } from "@/components/main-layout"
import { JSONLLogViewer } from "@/components/logs/jsonl-log-viewer"
import { useWebSocket } from "@/hooks/use-websocket"
import { websocketService } from "@/lib/websocket/websocket-service"
import { Button } from "@/components/ui/button"
import { useLogStore } from "@/lib/stores/log-store"

export default function LogsPage() {
  // Use the hook to manage WebSocket connection
  useWebSocket(true) // auto-connect for real-time logs

  const { clearLogs, addLog } = useLogStore()

  const handleTestBackend = () => {
    // Add a test log entry directly (remove duplicate from websocket service)
    addLog({
      agent: "System", 
      level: "info",
      message: "🔧 Backend connection test initiated",
      source: "user",
      category: "test"
    })
    
    // Trigger the websocket test (this will send the actual command)
    websocketService.testBackendConnection()
  }

  const handleTestOpenAI = () => {
    // Add a test log entry directly (remove duplicate from websocket service)
    addLog({
      agent: "System", 
      level: "info", 
      message: "🤖 OpenAI connection test initiated",
      source: "user",
      category: "test"
    })
    
    // Trigger the websocket test (this will send the actual command)
    websocketService.testOpenAI()
  }

  const handleTestConsoleLog = () => {
    // Add various test log entries to demonstrate JSONL formatting
    const testLogs = [
      {
        agent: "Frontend",
        level: "info" as const,
        message: "Frontend console log test message",
        source: "system" as const,
        category: "test",
        metadata: { testType: "console", component: "LogsPage" }
      },
      {
        agent: "Analyst",
        level: "success" as const,
        message: "Agent task completed successfully",
        source: "agent" as const,
        task: "requirements_analysis",
        category: "agent_task",
        duration: 1500,
        metadata: { confidence: 0.95, tokens_used: 240 }
      },
      {
        agent: "WebSocket",
        level: "warning" as const,
        message: "Connection briefly interrupted, reconnecting...",
        source: "websocket" as const,
        category: "connection",
        metadata: { attempt: 2, delay: "1000ms" }
      },
      {
        agent: "System",
        level: "error" as const,
        message: "Sample error message for testing error display",
        source: "system" as const,
        category: "error_test",
        severity: 4,
        metadata: { 
          error_code: "TEST_001",
          stack_trace: "Sample stack trace for testing",
          component: "TestRunner"
        }
      }
    ]

    testLogs.forEach((log, index) => {
      setTimeout(() => addLog(log), index * 200)
    })
  }

  const handleForceRefresh = () => {
    // Force refresh the log store to sync filteredLogs with logs
    const store = useLogStore.getState()
    store.clearFilters() // This should sync filteredLogs = logs
  }

  return (
    <MainLayout>
      <div className="p-6 flex flex-col gap-6 h-full">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">System Logs</h1>
            <p className="text-muted-foreground">
              Real-time system messages in JSONL format
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={handleForceRefresh} variant="secondary" size="sm">
              Refresh View
            </Button>
            <Button onClick={handleTestConsoleLog} variant="outline" size="sm">
              Test Logs
            </Button>
            <Button onClick={handleTestBackend} variant="outline" size="sm">
              Test Backend
            </Button>
            <Button onClick={handleTestOpenAI} variant="outline" size="sm">
              Test OpenAI
            </Button>
            <Button onClick={clearLogs} variant="destructive" size="sm">
              Clear Logs
            </Button>
          </div>
        </div>

        {/* JSONL Log Viewer - Full height */}
        <div className="flex-1 min-h-0">
          <JSONLLogViewer maxHeight="calc(100vh - 200px)" />
        </div>
      </div>
    </MainLayout>
  )
}