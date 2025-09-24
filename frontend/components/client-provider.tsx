"use client"

import { useEffect } from 'react';
import { ThemeProvider } from "@/components/theme-provider"
import { ErrorBoundary } from "@/components/error-boundary"
import { WebSocketProvider } from "@/lib/context/websocket-provider"
import { CopilotKit } from "@copilotkit/react-core"
import { useProjectStore } from '@/lib/stores/project-store';
import type React from "react"

export function ClientProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    useProjectStore.getState().reset();
  }, []);

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
          <WebSocketProvider>
            <CopilotKit
              publicApiKey="ck_pub_5a0060a610ccaa24d3effed3e350a6f6"
              onError={(errorEvent) => {
                console.error("[CopilotKit Error]", {
                  type: errorEvent.type,
                  timestamp: new Date(errorEvent.timestamp).toISOString(),
                  context: errorEvent.context,
                  error: errorEvent.error,
                });
              }}
            >
              {children}
            </CopilotKit>
          </WebSocketProvider>
        </ErrorBoundary>
      </ThemeProvider>
    </div>
  )
}
