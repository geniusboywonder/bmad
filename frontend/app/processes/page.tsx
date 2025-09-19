"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ProcessSelectorModal } from "@/components/process/ProcessSelectorModal"

export default function ProcessesPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleStartProcess = (process: string | File) => {
    console.log("Request to start process:", process)
    // In a real implementation, this would trigger a WebSocket message
    // to the backend to initiate the selected process.

    // Example of how the WebSocket message might be sent:
    // import { websocketService } from '@/lib/websocket/websocket-service';
    // if (typeof process === 'string') {
    //   websocketService.sendCommand('start_project', { brief: `Start predefined process: ${process}`, config_name: process });
    // } else {
    //   // File upload logic would be more complex, likely involving a separate API endpoint
    //   // and then a message to start the process with the uploaded file's ID.
    //   console.log("File upload and start logic not implemented yet.");
    // }
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-2xl font-bold">Process Management</h1>
          <p className="text-muted-foreground">
            Start a new automated process by selecting a template or uploading your own configuration.
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>Start New Process</Button>
      </div>

      <ProcessSelectorModal
        isOpen={isModalOpen}
        onOpenChange={setIsModalOpen}
        onStartProcess={handleStartProcess}
      />

      {/* Placeholder for a list of active and past process runs */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold">Process Runs</h2>
        <div className="border rounded-lg p-8 mt-4 text-center text-muted-foreground">
          <p>Process history will be displayed here.</p>
        </div>
      </div>
    </div>
  )
}
