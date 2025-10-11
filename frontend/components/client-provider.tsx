"use client"

import { useEffect, useMemo } from 'react';
import { ThemeProvider } from "@/components/theme-provider";
import { ErrorBoundary } from "@/components/error-boundary";
import { WebSocketProvider } from "@/lib/context/websocket-provider";
import { AgentProvider, useAgent } from "@/lib/context/agent-context";
import { CopilotKit } from "@copilotkit/react-core";
import { useProjectStore } from "@/lib/stores/project-store";
import { Toaster } from "@/components/ui/sonner";
import type React from "react";

function CopilotKitWrapper({ children }: { children: React.ReactNode }) {
  const { selectedAgent, projectId } = useAgent();

  // Use project ID for policy enforcement, fall back to agent thread if no project
  // Format: {projectId}-agent-{agentType}-thread for policy-aware execution
  const threadId = useMemo(() => {
    if (projectId) {
      return `${projectId}-agent-${selectedAgent}-thread`;
    }
    return `agent-${selectedAgent}-thread`;
  }, [projectId, selectedAgent]);

  return (
    <CopilotKit
      key={threadId} // Force remount when thread changes to show only that agent's messages
      publicApiKey={process.env.NEXT_PUBLIC_COPILOTKIT_API_KEY}
      runtimeUrl="/api/copilotkit"
      agent={selectedAgent}
      threadId={threadId}
      onError={(errorEvent) => {
        // Filter out empty error objects - these are not actual errors
        const hasRealError = errorEvent?.error?.message ||
                            errorEvent?.error?.name ||
                            (errorEvent?.error && Object.keys(errorEvent.error).length > 0);

        // Only log actual errors with meaningful content
        if (errorEvent?.type || hasRealError) {
          console.error("[CopilotKit Error]", {
            type: errorEvent.type,
            agent: selectedAgent,
            threadId: threadId,
            projectId: projectId,
            runtimeUrl: "/api/copilotkit",
            timestamp: errorEvent.timestamp ? new Date(errorEvent.timestamp).toISOString() : new Date().toISOString(),
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
              <Toaster />
            </AgentProvider>
          </WebSocketProvider>
        </ErrorBoundary>
      </ThemeProvider>
    </div>
  );
}
