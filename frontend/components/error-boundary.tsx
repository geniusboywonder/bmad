"use client"

import React from "react"
import { AlertTriangle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
  errorInfo?: React.ErrorInfo
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<ErrorFallbackProps>
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface ErrorFallbackProps {
  error: Error
  resetError: () => void
  errorInfo?: React.ErrorInfo
}

const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({ 
  error, 
  resetError, 
  errorInfo 
}) => (
  <Card className="mx-auto max-w-md">
    <CardHeader>
      <CardTitle className="flex items-center gap-2 text-destructive">
        <AlertTriangle className="w-5 h-5" />
        Something went wrong
      </CardTitle>
      <CardDescription>
        An unexpected error occurred in this component
      </CardDescription>
    </CardHeader>
    <CardContent className="space-y-4">
      <div className="rounded-md bg-muted p-3">
        <p className="text-sm font-mono text-muted-foreground">
          {error.message}
        </p>
      </div>
      
      <div className="flex flex-col gap-2">
        <Button onClick={resetError} variant="outline" className="w-full">
          <RefreshCw className="w-4 h-4 mr-2" />
          Try again
        </Button>
        
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => window.location.reload()}
          className="w-full"
        >
          Reload page
        </Button>
      </div>
      
      {process.env.NODE_ENV === 'development' && errorInfo && (
        <details className="text-xs">
          <summary className="cursor-pointer font-medium">
            Debug info (dev only)
          </summary>
          <pre className="mt-2 overflow-auto rounded bg-muted p-2 text-xs">
            {errorInfo.componentStack}
          </pre>
        </details>
      )}
    </CardContent>
  </Card>
)

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo })
    
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }
    
    // Call onError callback if provided
    this.props.onError?.(error, errorInfo)
  }

  resetError = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined })
  }

  render() {
    if (this.state.hasError && this.state.error) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback
      
      return (
        <FallbackComponent
          error={this.state.error}
          resetError={this.resetError}
          errorInfo={this.state.errorInfo}
        />
      )
    }

    return this.props.children
  }
}

// Hook for functional components
export const useErrorBoundary = () => {
  const [error, setError] = React.useState<Error | null>(null)

  const resetError = React.useCallback(() => {
    setError(null)
  }, [])

  const captureError = React.useCallback((error: Error) => {
    setError(error)
  }, [])

  React.useEffect(() => {
    if (error) {
      throw error
    }
  }, [error])

  return { captureError, resetError }
}