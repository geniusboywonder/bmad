"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Checkbox } from "@/components/ui/checkbox"
import { UploadCloud, Settings, Layers, Cog } from "lucide-react"

const mockArtifactsToGenerate = [
    { id: 'srs', label: 'System Requirements Specification' },
    { id: 'use_case', label: 'Use Case Diagrams' },
    { id: 'risk_analysis', label: 'Risk Analysis Report' },
    { id: 'architecture_diagram', label: 'Architecture Diagram' },
    { id: 'source_code', label: 'Source Code Files' },
    { id: 'test_cases', label: 'Test Cases & Scripts' },
]

interface StageConfigProps {
  stageName: string
}

export function StageConfig({ stageName = "Stage" }: StageConfigProps) {
  return (
    <div className="space-y-6">
      
      {/* Stage Configuration Box */}
      <Card className="border-2">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            <CardTitle>Stage Configuration</CardTitle>
          </div>
          <CardDescription>
            Configure the agent role and behavior for the {stageName} stage.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <Label htmlFor="agent-role" className="text-sm font-medium">Agent Role Definition</Label>
            <p className="text-xs text-muted-foreground">Upload a .md file to define the agent's role, goals, and constraints.</p>
            <div className="flex w-full max-w-md items-center space-x-2">
              <Input id="agent-role" type="file" accept=".md" className="text-sm" />
              <Button size="sm">
                <UploadCloud className="w-4 h-4 mr-1" />
                Upload
              </Button>
            </div>
          </div>
          <div className="pt-2">
            <Button size="sm" variant="outline">Save Configuration</Button>
          </div>
        </CardContent>
      </Card>

      {/* Artifact Generation Box */}
      <Card className="border-2">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5" />
            <CardTitle>Artifact Generation</CardTitle>
          </div>
          <CardDescription>
            Select which artifacts should be generated during this stage.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {mockArtifactsToGenerate.map(artifact => (
              <div key={artifact.id} className="flex items-center space-x-2">
                <Checkbox id={artifact.id} defaultChecked />
                <label
                  htmlFor={artifact.id}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {artifact.label}
                </label>
              </div>
            ))}
          </div>
          <div className="pt-2">
            <Button size="sm" variant="outline">Update Artifacts</Button>
          </div>
        </CardContent>
      </Card>

      {/* Stage Settings Box */}
      <Card className="border-2">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Cog className="w-5 h-5" />
            <CardTitle>Stage Settings</CardTitle>
          </div>
          <CardDescription>
            Enable or disable specific behaviors and automation for this stage.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label htmlFor="auto-approve" className="text-sm font-medium">Auto-approve Tasks</Label>
                <p className="text-xs text-muted-foreground">Automatically approve all tasks in this stage without human review</p>
              </div>
              <Switch id="auto-approve" />
            </div>
            
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label htmlFor="strict-mode" className="text-sm font-medium">Strict Mode</Label>
                <p className="text-xs text-muted-foreground">Agent must follow instructions precisely with no deviation</p>
              </div>
              <Switch id="strict-mode" defaultChecked />
            </div>
            
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label htmlFor="human-review" className="text-sm font-medium">Human Review Required</Label>
                <p className="text-xs text-muted-foreground">Pause workflow for human review before proceeding</p>
              </div>
              <Switch id="human-review" />
            </div>
          </div>
          <div className="pt-2">
            <Button size="sm" variant="outline">Save Settings</Button>
          </div>
        </CardContent>
      </Card>
      
    </div>
  )
}
