"use client"

import { EnhancedChatInterfaceMockup } from "@/components/mockups/enhanced-chat-interface"

export default function ChatInterfacePage() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Enhanced Chat Interface</h1>
        <p className="text-lg text-gray-600">
          Interactive chat interface with resizable panels, collapsible messages, and real-time agent status overlays.
        </p>
      </div>
      
      {/* Main Content */}
      <div className="min-h-[500px] flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200 p-6">
        <div className="w-full max-w-5xl">
          <EnhancedChatInterfaceMockup />
        </div>
      </div>
    </div>
  )
}
