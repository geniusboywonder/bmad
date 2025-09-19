"use client"

import { ThemeProvider } from "@/components/theme-provider"
import { ErrorBoundary } from "@/components/error-boundary"
import { WebSocketProvider } from "@/lib/context/websocket-provider"
import { CopilotKit } from "@copilotkit/react-core"
import type React from "react"

export function ClientProvider({ children }: { children: React.ReactNode }) {
  return (
    <div className="dark">
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem={false}
        forcedTheme="dark"
        disableTransitionOnChange
      >
        <ErrorBoundary>
          <CopilotKit
            publicApiKey="ck_pub_5a0060a610ccaa24d3effed3e350a6f6"
          >
            <WebSocketProvider>
              {children}
            </WebSocketProvider>
          </CopilotKit>
        </ErrorBoundary>
      </ThemeProvider>
    </div>
  )
}
