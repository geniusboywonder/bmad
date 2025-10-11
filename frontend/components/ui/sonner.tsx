"use client";

import { Toaster as SonnerToaster } from "sonner";

/**
 * Global toast container using shadcn/ui's Sonner integration.
 * Positioned top-right with styling that matches the design system.
 */
export function Toaster() {
  return (
    <SonnerToaster
      position="top-right"
      richColors
      closeButton
      toastOptions={{
        classNames: {
          toast: "bg-background border border-border text-foreground shadow-lg",
          title: "text-sm font-semibold",
          description: "text-xs text-muted-foreground",
          actionButton: "bg-primary text-primary-foreground",
          cancelButton: "bg-muted text-muted-foreground",
        },
      }}
    />
  );
}
