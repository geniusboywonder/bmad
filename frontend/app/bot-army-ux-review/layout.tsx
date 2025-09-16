"use client"

import type React from "react"
import { Header } from "@/components/layout/header"
import { EnhancedSidebarMockup } from "@/components/mockups/enhanced-sidebar"
import { ConsoleLoggerProvider } from "@/components/console-logger-provider"

interface MockupLayoutProps {
  children: React.ReactNode
}

export default function MockupLayout({ children }: MockupLayoutProps) {
  return (
    <ConsoleLoggerProvider>
      <div className="min-h-screen bg-background flex flex-col">
        <Header />
        <div className="flex flex-1">
          {/* We will use our enhanced sidebar mockup here */}
          <EnhancedSidebarMockup />
          <main className="flex-1 overflow-auto p-6">{children}</main>
        </div>
      </div>
    </ConsoleLoggerProvider>
  )
}
