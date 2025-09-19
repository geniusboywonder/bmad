"use client"

import { Loader2, Brain, Cog, Zap } from "lucide-react"
import { cn } from "@/lib/utils"

interface LoadingStateProps {
  className?: string
  size?: "sm" | "md" | "lg"
  variant?: "spinner" | "dots" | "pulse" | "brain" | "cog" | "zap"
  text?: string
  subtext?: string
  showIcon?: boolean
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  className,
  size = "md",
  variant = "spinner",
  text,
  subtext,
  showIcon = true
}) => {
  const sizeClasses = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg"
  }

  const iconSizes = {
    sm: "h-4 w-4",
    md: "h-6 w-6", 
    lg: "h-8 w-8"
  }

  const renderIcon = () => {
    if (!showIcon) return null

    const iconClass = cn("animate-spin", iconSizes[size])

    switch (variant) {
      case "brain":
        return <Brain className={cn(iconClass, "text-blue-500")} />
      case "cog":
        return <Cog className={cn(iconClass, "text-purple-500")} />
      case "zap":
        return <Zap className={cn(iconClass, "text-yellow-500")} />
      case "dots":
        return <DotsLoader size={size} />
      case "pulse":
        return <PulseLoader size={size} />
      default:
        return <Loader2 className={iconClass} />
    }
  }

  return (
    <div className={cn("flex flex-col items-center justify-center space-y-2", className)}>
      {renderIcon()}
      {text && (
        <div className={cn("font-medium text-center", sizeClasses[size])}>
          {text}
        </div>
      )}
      {subtext && (
        <div className="text-sm text-muted-foreground text-center max-w-xs">
          {subtext}
        </div>
      )}
    </div>
  )
}

// Dots loading animation
const DotsLoader: React.FC<{ size: "sm" | "md" | "lg" }> = ({ size }) => {
  const dotSizes = {
    sm: "w-1 h-1",
    md: "w-2 h-2",
    lg: "w-3 h-3"
  }

  return (
    <div className="flex items-center space-x-1">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={cn(
            "bg-primary rounded-full animate-bounce",
            dotSizes[size]
          )}
          style={{
            animationDelay: `${i * 0.15}s`,
            animationDuration: "0.6s"
          }}
        />
      ))}
    </div>
  )
}

// Pulse loading animation
const PulseLoader: React.FC<{ size: "sm" | "md" | "lg" }> = ({ size }) => {
  const pulseSizes = {
    sm: "w-6 h-6",
    md: "w-8 h-8",
    lg: "w-12 h-12"
  }

  return (
    <div className="relative">
      <div
        className={cn(
          "bg-primary/20 rounded-full animate-ping",
          pulseSizes[size]
        )}
      />
      <div
        className={cn(
          "absolute inset-0 bg-primary/40 rounded-full animate-pulse",
          pulseSizes[size]
        )}
      />
    </div>
  )
}

// Convenience components for common loading scenarios
export const AgentThinking: React.FC<{ agentName?: string; className?: string }> = ({ 
  agentName, 
  className 
}) => (
  <LoadingState
    variant="brain"
    text={agentName ? `${agentName} is thinking...` : "Thinking..."}
    className={className}
  />
)

export const WorkflowProcessing: React.FC<{ className?: string }> = ({ className }) => (
  <LoadingState
    variant="cog"
    text="Processing workflow..."
    subtext="This may take a few moments"
    className={className}
  />
)

export const GeneratingResponse: React.FC<{ className?: string }> = ({ className }) => (
  <LoadingState
    variant="zap"
    text="Generating response..."
    subtext="AI is crafting the perfect response"
    className={className}
  />
)