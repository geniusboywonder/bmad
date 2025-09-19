"use client"

import { BaseStagePage } from "@/components/stages/base-stage-page"
import { useProcessStore } from "@/lib/stores/process-store"

export default function DevPage() {
  const stage = useProcessStore((state) => state.getStageByName("Development"))

  if (!stage) {
    return <div className="p-8">Development stage not found.</div>
  }

  return (
    <BaseStagePage
      stageName={stage.name}
      agentName={stage.agentName}
      currentTask={stage.currentTask}
      hitlRequired={stage.hitlRequired}
      tasks={stage.tasks}
      artifacts={stage.artifacts}
    />
  )
}
