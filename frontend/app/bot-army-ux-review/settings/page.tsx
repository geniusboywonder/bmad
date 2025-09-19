"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { 
  Save, 
  RefreshCw, 
  Eye, 
  EyeOff, 
  AlertTriangle,
  CheckCircle,
  Settings as SettingsIcon,
  Key,
  Server,
  Globe,
  Zap,
  TestTube
} from "lucide-react"
import { cn } from "@/lib/utils"

interface EnvVariable {
  key: string
  value: string | boolean
  description: string
  category: string
  isSecret?: boolean
  required?: boolean
  type: "string" | "boolean" | "number"
}

const getDefaultEnvVariables = (): EnvVariable[] => [
  // LLM Configuration
  {
    key: "OPENAI_API_KEY",
    value: "",
    description: "OpenAI API key for GPT models",
    category: "LLM Configuration",
    isSecret: true,
    required: true,
    type: "string"
  },
  {
    key: "GEMINI_KEY_KEY",
    value: "AIzaSyB_FH53-q9yE13t7Nav0_tSq2I9GbhBLN4",
    description: "Google Gemini API key",
    category: "LLM Configuration",
    isSecret: true,
    required: false,
    type: "string"
  },
  {
    key: "MAX_AGENTS",
    value: "6",
    description: "Maximum number of concurrent agents",
    category: "LLM Configuration",
    required: true,
    type: "number"
  },
  {
    key: "AGENT_TIMEOUT",
    value: "300",
    description: "Agent timeout in seconds",
    category: "LLM Configuration",
    required: true,
    type: "number"
  },
  {
    key: "LLM_RATE_LIMIT_DELAY",
    value: "2",
    description: "Delay between LLM requests in seconds",
    category: "LLM Configuration",
    required: true,
    type: "number"
  },

  // Backend Configuration
  {
    key: "BACKEND_HOST",
    value: "localhost",
    description: "Backend server hostname",
    category: "Backend Configuration",
    required: true,
    type: "string"
  },
  {
    key: "BACKEND_PORT",
    value: "8000",
    description: "Backend server port",
    category: "Backend Configuration",
    required: true,
    type: "number"
  },
  {
    key: "BACKEND_URL",
    value: "http://localhost:8000",
    description: "Full backend URL",
    category: "Backend Configuration",
    required: true,
    type: "string"
  },

  // WebSocket Configuration
  {
    key: "WEBSOCKET_URL",
    value: "ws://localhost:8000/api/ws",
    description: "WebSocket server URL",
    category: "WebSocket Configuration",
    required: true,
    type: "string"
  },
  {
    key: "NEXT_PUBLIC_WEBSOCKET_URL",
    value: "ws://localhost:8000/api/ws",
    description: "Public WebSocket URL for client-side",
    category: "WebSocket Configuration",
    required: true,
    type: "string"
  },

  // Frontend Configuration
  {
    key: "NEXT_PUBLIC_BACKEND_URL",
    value: "http://localhost:8000",
    description: "Public backend URL for Next.js",
    category: "Frontend Configuration",
    required: true,
    type: "string"
  },

  // Development Settings
  {
    key: "DEBUG",
    value: true,
    description: "Enable debug mode",
    category: "Development Settings",
    required: false,
    type: "boolean"
  },
  {
    key: "LOG_LEVEL",
    value: "INFO",
    description: "Logging level (DEBUG, INFO, WARN, ERROR)",
    category: "Development Settings",
    required: false,
    type: "string"
  },

  // Testing Configuration
  {
    key: "AGENT_TEST_MODE",
    value: true,
    description: "Enable agent test mode",
    category: "Testing Configuration",
    required: false,
    type: "boolean"
  },
  {
    key: "ROLE_TEST_MODE",
    value: false,
    description: "Enable role test mode",
    category: "Testing Configuration",
    required: false,
    type: "boolean"
  },
  {
    key: "TEST_MODE",
    value: true,
    description: "Enable overall test mode",
    category: "Testing Configuration",
    required: false,
    type: "boolean"
  },
  {
    key: "ENABLE_HITL",
    value: false,
    description: "Enable Human-in-the-Loop functionality",
    category: "Testing Configuration",
    required: false,
    type: "boolean"
  },
  {
    key: "AUTO_ACTION",
    value: "approve",
    description: "Default auto action (approve/reject)",
    category: "Testing Configuration",
    required: false,
    type: "string"
  }
]

const getCategoryIcon = (category: string) => {
  switch (category) {
    case "LLM Configuration": return <Key className="w-4 h-4 text-purple-500" />
    case "Backend Configuration": return <Server className="w-4 h-4 text-blue-500" />
    case "WebSocket Configuration": return <Zap className="w-4 h-4 text-yellow-500" />
    case "Frontend Configuration": return <Globe className="w-4 h-4 text-green-500" />
    case "Development Settings": return <SettingsIcon className="w-4 h-4 text-gray-500" />
    case "Testing Configuration": return <TestTube className="w-4 h-4 text-orange-500" />
    default: return <SettingsIcon className="w-4 h-4 text-gray-500" />
  }
}

const getCategoryColor = (category: string) => {
  switch (category) {
    case "LLM Configuration": return "bg-purple-100 text-purple-800 border-purple-200"
    case "Backend Configuration": return "bg-blue-100 text-blue-800 border-blue-200"
    case "WebSocket Configuration": return "bg-yellow-100 text-yellow-800 border-yellow-200"
    case "Frontend Configuration": return "bg-green-100 text-green-800 border-green-200"
    case "Development Settings": return "bg-gray-100 text-gray-800 border-gray-200"
    case "Testing Configuration": return "bg-orange-100 text-orange-800 border-orange-200"
    default: return "bg-gray-100 text-gray-800 border-gray-200"
  }
}

export default function SettingsPage() {
  const [envVariables, setEnvVariables] = useState<EnvVariable[]>([])
  const [visibleSecrets, setVisibleSecrets] = useState<string[]>([])
  const [hasChanges, setHasChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle")
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
    setEnvVariables(getDefaultEnvVariables())
  }, [])

  // Group variables by category for 3-column layout
  const allVariables = envVariables.reduce((acc, variable) => {
    if (!acc[variable.category]) {
      acc[variable.category] = []
    }
    acc[variable.category].push(variable)
    return acc
  }, {} as Record<string, EnvVariable[]>)

  const categories = Object.keys(allVariables)

  const toggleSecretVisibility = (key: string) => {
    setVisibleSecrets(prev =>
      prev.includes(key)
        ? prev.filter(k => k !== key)
        : [...prev, key]
    )
  }

  const updateEnvVariable = (key: string, newValue: string | boolean) => {
    setEnvVariables(prev =>
      prev.map(env =>
        env.key === key ? { ...env, value: newValue } : env
      )
    )
    setHasChanges(true)
    setSaveStatus("idle")
  }

  const handleSave = async () => {
    setIsSaving(true)
    setSaveStatus("idle")
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    try {
      // Here you would make the actual API call to save the environment variables
      console.log("Saving environment variables:", envVariables)
      setSaveStatus("success")
      setHasChanges(false)
    } catch (error) {
      console.error("Failed to save:", error)
      setSaveStatus("error")
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = () => {
    setEnvVariables(getDefaultEnvVariables())
    setHasChanges(false)
    setSaveStatus("idle")
  }

  if (!isClient) {
    return <div>Loading...</div>
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Environment Settings</h1>
        <p className="text-lg text-gray-600">
          Configure environment variables and application settings for the BotArmy platform.
        </p>
      </div>

      {/* Save Actions */}
      <Card className="border-dashed border-teal-200 bg-teal-50">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {saveStatus === "success" && (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">Settings saved successfully</span>
                </div>
              )}
              {saveStatus === "error" && (
                <div className="flex items-center space-x-2 text-red-600">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm font-medium">Failed to save settings</span>
                </div>
              )}
              {hasChanges && saveStatus === "idle" && (
                <div className="flex items-center space-x-2 text-amber-600">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm font-medium">You have unsaved changes</span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Button 
                variant="outline" 
                onClick={handleReset}
                disabled={isSaving || !hasChanges}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Reset
              </Button>
              <Button 
                onClick={handleSave}
                disabled={isSaving || !hasChanges}
                className={cn(
                  "bg-teal-600 hover:bg-teal-700 text-white shadow-sm",
                  hasChanges && "ring-2 ring-teal-300 ring-offset-1"
                )}
              >
                {isSaving ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Save className="w-4 h-4 mr-2" />
                )}
                {isSaving ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Environment Variables Section */}
      <div className="space-y-4">
        <div className="border-t border-gray-200 pt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Configuration Categories</h2>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-8">
          {categories.map((category) => (
            <Card key={category} className="shadow-sm">
              <CardHeader>
              <div className="flex items-center space-x-3">
                {getCategoryIcon(category)}
                <div>
                  <CardTitle className="text-base">{category}</CardTitle>
                  <CardDescription>
                    {allVariables[category].length} variables
                  </CardDescription>
                </div>
              </div>
              <Badge variant="outline" className={cn("w-fit", getCategoryColor(category))}>
                {category.replace(" Configuration", "").replace(" Settings", "")}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              {allVariables[category].map((env) => (
                <div key={env.key} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor={env.key} className="text-xs font-semibold flex items-center space-x-2">
                      <span>{env.key}</span>
                    </Label>
                    {env.isSecret && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleSecretVisibility(env.key)}
                        className="h-6 px-2"
                      >
                        {visibleSecrets.includes(env.key) ? (
                          <EyeOff className="w-3 h-3" />
                        ) : (
                          <Eye className="w-3 h-3" />
                        )}
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{env.description}</p>
                  
                  {env.type === "boolean" ? (
                    <div className="flex items-center space-x-2">
                      <Switch
                        id={env.key}
                        checked={env.value as boolean}
                        onCheckedChange={(checked) => updateEnvVariable(env.key, checked)}
                      />
                      <Label htmlFor={env.key} className="text-sm">
                        {env.value ? "Enabled" : "Disabled"}
                      </Label>
                    </div>
                  ) : (
                    <Input
                      id={env.key}
                      type={env.isSecret && !visibleSecrets.includes(env.key) ? "password" : "text"}
                      value={env.value as string}
                      onChange={(e) => updateEnvVariable(env.key, e.target.value)}
                      className={cn(
                        "font-mono text-xs",
                        env.required && !env.value && "border-red-300 focus:border-red-500"
                      )}
                      placeholder={env.required ? "Required" : "Optional"}
                    />
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
          ))}
        </div>
      </div>
    </div>
  )
}