import * as React from "react"
import { cn } from "@/lib/utils"

interface TypingIndicatorProps {
  className?: string
  size?: "sm" | "md" | "lg"
  color?: "primary" | "secondary" | "muted"
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  className,
  size = "md",
  color = "primary"
}) => {
  const sizeClasses = {
    sm: "w-1 h-1",
    md: "w-2 h-2", 
    lg: "w-3 h-3"
  }

  const colorClasses = {
    primary: "bg-primary",
    secondary: "bg-secondary", 
    muted: "bg-muted-foreground"
  }

  const dotClass = cn(
    "rounded-full animate-bounce",
    sizeClasses[size],
    colorClasses[color]
  )

  return (
    <div className={cn("flex items-center space-x-1", className)}>
      <div 
        className={dotClass}
        style={{ animationDelay: "0ms" }}
      />
      <div 
        className={dotClass}
        style={{ animationDelay: "150ms" }}
      />
      <div 
        className={dotClass}
        style={{ animationDelay: "300ms" }}
      />
    </div>
  )
}

// Alternative wave animation
export const WaveTypingIndicator: React.FC<TypingIndicatorProps> = ({
  className,
  size = "md",
  color = "primary"
}) => {
  const sizeClasses = {
    sm: "h-2",
    md: "h-3",
    lg: "h-4"
  }

  const colorClasses = {
    primary: "bg-primary",
    secondary: "bg-secondary",
    muted: "bg-muted-foreground"
  }

  const barClass = cn(
    "w-1 rounded-full animate-pulse",
    sizeClasses[size],
    colorClasses[color]
  )

  return (
    <div className={cn("flex items-center justify-center space-x-1", className)}>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={barClass}
          style={{
            animationDelay: `${i * 200}ms`,
            animationDuration: "0.6s"
          }}
        />
      ))}
    </div>
  )
}