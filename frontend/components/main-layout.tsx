"use client";

import type React from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { useHITLStore } from "@/lib/stores/hitl-store";
import { Header } from "./layout/header";
import { ConsoleLoggerProvider } from "./console-logger-provider";
import { RequirementsGatheringInterface } from "./chat/requirements-gathering-interface";

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const { requests } = useHITLStore();
  const [isClient, setIsClient] = useState(false);
  const seenApprovalsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    setIsClient(true);
  }, []);

  const pendingRequests = useMemo(
    () => requests.filter((request) => request.status === "pending"),
    [requests]
  );

  useEffect(() => {
    if (!isClient) {
      return;
    }

    const seenApprovals = seenApprovalsRef.current;
    const activeApprovalIds = new Set<string>();

    pendingRequests.forEach((request) => {
      const approvalId =
        (request.context?.approvalId as string | undefined) ?? request.id;
      if (!approvalId) {
        return;
      }

      activeApprovalIds.add(approvalId);

      if (seenApprovals.has(approvalId)) {
        return;
      }

      seenApprovals.add(approvalId);

      const description =
        request.decision?.trim() || "Agent action pending approval.";

      toast(`${request.agentName} requests approval`, {
        description,
        duration: 8000,
      });
    });

    // Allow future toasts if approvals resolve and resurface later.
    seenApprovals.forEach((approvalId) => {
      if (!activeApprovalIds.has(approvalId)) {
        seenApprovals.delete(approvalId);
      }
    });
  }, [pendingRequests, isClient]);

  return (
    <ConsoleLoggerProvider>
      <div className="min-h-screen bg-background flex flex-col">
        <Header />
        <main className="flex-1 overflow-auto">{children}</main>
        <RequirementsGatheringInterface />
      </div>
    </ConsoleLoggerProvider>
  );
}
