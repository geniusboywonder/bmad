"use client"

import { BaseStagePage } from "@/components/stages/base-stage-page"
import { useProcessStore } from "@/lib/stores/process-store"

export default function DeployPage() {
  const stage = useProcessStore((state) => state.getStageByName("Deployment"))

  if (!stage) {
    return <div className="p-8">Deployment stage not found.</div>
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
