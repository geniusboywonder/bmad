"use client"

import { useEffect } from "react"
import { consoleLogger } from "@/lib/utils/console-logger"

export function ConsoleLoggerProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Initialize console logger on mount
    consoleLogger.init()

    // Cleanup on unmount
    return () => {
      // Keep console logger active - don't disable on unmount
      // consoleLogger.disable()
    }
  }, [])

  return <>{children}</>
}