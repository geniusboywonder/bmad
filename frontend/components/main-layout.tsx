"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Header } from "./layout/header"
import { ConsoleLoggerProvider } from "./console-logger-provider"
import { RequirementsGatheringInterface } from "./chat/requirements-gathering-interface"
import { HITLAlertsBar } from "./hitl/hitl-alerts-bar"

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const [systemAlerts, setSystemAlerts] = useState<{id: string; message: string; stage?: string}[]>([])
  const [expandedAlerts, setExpandedAlerts] = useState<string[]>([])
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  const toggleExpanded = (id: string) => {
    setExpandedAlerts(prev =>
      prev.includes(id)
        ? prev.filter(alertId => alertId !== id)
        : [...prev, id]
    )
  }

  const dismissAlert = (id: string) => {
    setSystemAlerts(prev => prev.filter(alert => alert.id !== id))
  }

  return (
    <ConsoleLoggerProvider>
      <div className="min-h-screen bg-background flex flex-col">
        <Header />
        <HITLAlertsBar
          systemAlerts={systemAlerts}
          expandedAlerts={expandedAlerts}
          toggleExpanded={toggleExpanded}
          dismissAlert={dismissAlert}
          isClient={isClient}
        />
        <main className="flex-1 overflow-auto">{children}</main>
        <RequirementsGatheringInterface />
      </div>
    </ConsoleLoggerProvider>
  )
}