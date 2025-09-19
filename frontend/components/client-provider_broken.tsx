"use client"

import { ThemeProvider } from "@/components/theme-provider"
import { ErrorBoundary } from "@/components/error-boundary"
import type React from "react"

export function ClientProvider({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="light"
      enableSystem={false}
      disableTransitionOnChange
    >
      <ErrorBoundary>
        {children}
      </ErrorBoundary>
    </ThemeProvider>
  )
}
