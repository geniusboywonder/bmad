"use client"

import { EnhancedProcessSummaryMockup } from "@/components/mockups/enhanced-process-summary"

export default function ProcessSummaryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Enhanced Process Summary</h1>
        <p className="text-muted-foreground">
          A detailed view of the simplified process summary with expandable cards and parallel workflows.
        </p>
      </div>
      <div className="max-w-4xl mx-auto">
        <EnhancedProcessSummaryMockup />
      </div>
    </div>
  )
}
