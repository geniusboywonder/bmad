"use client"

import { useEffect, useMemo } from 'react';
import { ThemeProvider } from "@/components/theme-provider"
import { ErrorBoundary } from "@/components/error-boundary"
import { WebSocketProvider } from "@/lib/context/websocket-provider"
import { AgentProvider, useAgent } from "@/lib/context/agent-context"
import { CopilotKit } from "@copilotkit/react-core"
import { useProjectStore } from '@/lib/stores/project-store';
import type React from "react"

function CopilotKitWrapper({ children }: { children: React.ReactNode }) {
  const { selectedAgent } = useAgent();

  // Each agent gets its own thread ID to maintain separate conversation history
  const threadId = useMemo(() => `agent-${selectedAgent}-thread`, [selectedAgent]);

  return (
    <CopilotKit
      key={threadId} // Force remount when thread changes to show only that agent's messages
      publicApiKey={process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY}
      runtimeUrl="/api/copilotkit"
      agent={selectedAgent}
      threadId={threadId}
      onError={(errorEvent) => {
        // Only log actual errors, not empty objects
        if (errorEvent.error || errorEvent.type) {
          console.error("[CopilotKit Error]", {
            type: errorEvent.type,
            agent: selectedAgent,
            threadId: threadId,
            timestamp: new Date(errorEvent.timestamp).toISOString(),
            context: errorEvent.context,
            error: errorEvent.error,
            message: errorEvent.error?.message,
          });
        }
      }}
    >
      {children}
    </CopilotKit>
  );
}

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
            <AgentProvider>
              <CopilotKitWrapper>
                {children}
              </CopilotKitWrapper>
            </AgentProvider>
          </WebSocketProvider>
        </ErrorBoundary>
      </ThemeProvider>
    </div>
  )
}
