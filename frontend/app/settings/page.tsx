"use client"

import React, { useState, useEffect } from "react"
import { MainLayout } from "@/components/main-layout"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import Link from "next/link"
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
  TestTube,
  FileText
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

// Fetch environment variables from API
const fetchEnvVariables = async (): Promise<EnvVariable[]> => {
  try {
    const response = await fetch('/api/env-settings')
    const data = await response.json()
    
    if (data.success) {
      // Map API response to our EnvVariable format with proper categories
      return data.variables.map((variable: any) => {
        // Determine category based on variable key
        let category = "Testing Configuration"
        if (variable.key.startsWith('HITL_') || variable.key === 'ENABLE_HITL' || variable.key === 'AUTO_ACTION') {
          category = "HITL Configuration"
        }
        
        return {
          ...variable,
          category,
          required: false,
          isSecret: false
        }
      })
    } else {
      console.error('Failed to fetch environment variables:', data.error)
      return getDefaultEnvVariables()
    }
  } catch (error) {
    console.error('Error fetching environment variables:', error)
    return getDefaultEnvVariables()
  }
}

const getDefaultEnvVariables = (): EnvVariable[] => [
  // Testing Configuration
  {
    key: "AGENT_TEST_MODE",
    value: true,
    description: "Enable agent test mode to return static confirmations",
    category: "Testing Configuration",
    required: false,
    type: "boolean"
  },
  {
    key: "ROLE_TEST_MODE",
    value: false,
    description: "Enable role test mode for LLM role confirmation",
    category: "Testing Configuration",
    required: false,
    type: "boolean"
  },
  {
    key: "TEST_MODE",
    value: true,
    description: "Enable overall test mode for mock LLM responses",
    category: "Testing Configuration",
    required: false,
    type: "boolean"
  },
  // HITL Configuration - Core Settings
  {
    key: "ENABLE_HITL",
    value: false,
    description: "Enable Human-in-the-Loop functionality",
    category: "HITL Configuration",
    required: false,
    type: "boolean"
  },
  {
    key: "AUTO_ACTION",
    value: "none",
    description: "Default auto action (approve/reject/none)",
    category: "HITL Configuration",
    required: false,
    type: "string"
  },
  
  // HITL Configuration - Timing & Thresholds
  {
    key: "HITL_TIMEOUT",
    value: "30",
    description: "Timeout in seconds for HITL decisions",
    category: "HITL Configuration",
    required: false,
    type: "string"
  },
  {
    key: "HITL_APPROVAL_THRESHOLD",
    value: "0.8",
    description: "Confidence threshold for automatic approval (0.0-1.0)",
    category: "HITL Configuration",
    required: false,
    type: "string"
  },
  {
    key: "HITL_RETRY_ATTEMPTS",
    value: "3",
    description: "Number of retry attempts for failed HITL operations",
    category: "HITL Configuration",
    required: false,
    type: "string"
  },
  
  // HITL Configuration - Notifications & Queue Management
  {
    key: "HITL_NOTIFICATION_EMAIL",
    value: "",
    description: "Email address for HITL notifications",
    category: "HITL Configuration",
    required: false,
    type: "string"
  },
  {
    key: "HITL_QUEUE_SIZE",
    value: "100",
    description: "Maximum size of HITL decision queue",
    category: "HITL Configuration",
    required: false,
    type: "string"
  },
  {
    key: "HITL_AUTO_ESCALATION",
    value: false,
    description: "Enable automatic escalation of timed-out HITL requests",
    category: "HITL Configuration",
    required: false,
    type: "boolean"
  }
]

const getCategoryIcon = (category: string) => {
  switch (category) {
    case "LLM Configuration": return <Key className="w-4 h-4 text-primary" />
    case "Backend Configuration": return <Server className="w-4 h-4 text-analyst" />
    case "WebSocket Configuration": return <Zap className="w-4 h-4 text-amber" />
    case "Frontend Configuration": return <Globe className="w-4 h-4 text-tester" />
    case "Development Settings": return <SettingsIcon className="w-4 h-4 text-muted-foreground" />
    case "Testing Configuration": return <TestTube className="w-4 h-4 text-developer" />
    case "HITL Configuration": return <AlertTriangle className="w-4 h-4 text-orange-500" />
    default: return <SettingsIcon className="w-4 h-4 text-muted-foreground" />
  }
}

const getCategoryColor = (category: string) => {
  switch (category) {
    case "LLM Configuration": return "bg-primary/10 text-primary border-primary/20"
    case "Backend Configuration": return "bg-analyst/10 text-analyst border-analyst/20"
    case "WebSocket Configuration": return "bg-amber/10 text-amber border-amber/20"
    case "Frontend Configuration": return "bg-tester/10 text-tester border-tester/20"
    case "Development Settings": return "bg-muted/10 text-muted-foreground border-muted/20"
    case "Testing Configuration": return "bg-developer/10 text-developer border-developer/20"
    case "HITL Configuration": return "bg-orange-500/10 text-orange-500 border-orange-500/20"
    default: return "bg-muted/10 text-muted-foreground border-muted/20"
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
    // Load real environment variables from the API
    const loadEnvVariables = async () => {
      const variables = await fetchEnvVariables()
      setEnvVariables(variables)
    }
    loadEnvVariables()
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
    
    try {
      const response = await fetch('/api/env-settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          variables: envVariables
        }),
      })
      
      const data = await response.json()
      
      if (data.success) {
        console.log("Environment variables saved successfully")
        
        // Refresh backend configuration cache
        try {
          const refreshResponse = await fetch('/api/config-refresh', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          })
          
          if (refreshResponse.ok) {
            console.log("Backend configuration cache refreshed")
          } else {
            console.warn("Failed to refresh backend configuration cache")
          }
        } catch (refreshError) {
          console.warn("Could not refresh backend configuration cache:", refreshError)
        }
        
        setSaveStatus("success")
        setHasChanges(false)
      } else {
        console.error("Failed to save:", data.error)
        setSaveStatus("error")
      }
    } catch (error) {
      console.error("Failed to save:", error)
      setSaveStatus("error")
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = async () => {
    const variables = await fetchEnvVariables()
    setEnvVariables(variables)
    setHasChanges(false)
    setSaveStatus("idle")
  }

  if (!isClient) {
    return (
      <MainLayout>
        <div className="p-6">
          <div className="animate-pulse">Loading...</div>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="p-6 space-y-8">
        {/* Page Header */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight text-foreground">Environment Settings</h1>
              <p className="text-lg text-muted-foreground">
                Configure environment variables and application settings for the BotArmy platform.
              </p>
            </div>
            <Link href="/logs">
              <Button variant="outline" className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                View Logs
              </Button>
            </Link>
          </div>
        </div>

        {/* Status Messages */}
        {(saveStatus !== "idle" || hasChanges) && (
          <div className="flex items-center space-x-3 p-4 rounded-lg bg-muted/10">
            {saveStatus === "success" && (
              <div className="flex items-center space-x-2 text-tester">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm font-medium">Settings saved successfully</span>
              </div>
            )}
            {saveStatus === "error" && (
              <div className="flex items-center space-x-2 text-destructive">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm font-medium">Failed to save settings</span>
              </div>
            )}
            {hasChanges && saveStatus === "idle" && (
              <div className="flex items-center space-x-2 text-amber">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm font-medium">You have unsaved changes</span>
              </div>
            )}
          </div>
        )}

        {/* Environment Variables Section */}
        <div className="space-y-6">
          <div className="border-t border-border pt-8">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-foreground">Configuration Categories</h2>
              <div className="flex items-center space-x-2">
                <Button 
                  variant="ghost" 
                  onClick={handleReset}
                  disabled={isSaving || !hasChanges}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reset
                </Button>
                <Button 
                  onClick={handleSave}
                  disabled={isSaving || !hasChanges}
                  variant={hasChanges ? "default" : "secondary"}
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
          </div>
          {categories.map((category) => (
            <Card key={category} className="shadow-sm">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getCategoryIcon(category)}
                    <div>
                      <CardTitle className="text-lg">{category}</CardTitle>
                      <CardDescription>
                        {allVariables[category].length} configuration {allVariables[category].length === 1 ? 'variable' : 'variables'}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge variant="outline" className={cn("", getCategoryColor(category))}>
                    {category.replace(" Configuration", "").replace(" Settings", "")}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {allVariables[category].map((env) => (
                    <div key={env.key} className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Label htmlFor={env.key} className="text-sm font-semibold flex items-center space-x-2">
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
                      <p className="text-xs text-muted-foreground line-clamp-2">{env.description}</p>
                      
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
                            "font-mono text-sm",
                            env.required && !env.value && "border-destructive focus:border-destructive"
                          )}
                          placeholder={env.required ? "Required" : "Optional"}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </MainLayout>
  )
}
