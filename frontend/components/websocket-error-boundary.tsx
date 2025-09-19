"use client"

import { Component, ErrorInfo, ReactNode } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertTriangle, RefreshCw, Wifi } from "lucide-react"
import { websocketService } from "@/lib/websocket/websocket-service"

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  isRetrying: boolean
}

export class WebSocketErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)

    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      isRetrying: false
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log the error for debugging
    console.error('[WebSocketErrorBoundary] Caught error:', error)
    console.error('[WebSocketErrorBoundary] Error info:', errorInfo)

    // Update state with error info
    this.setState({
      error,
      errorInfo
    })

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // Log to our logging system if available
    try {
      // Import and use log store if available
      import("@/lib/stores/log-store").then(({ useLogStore }) => {
        useLogStore.getState().addLog({
          agent: "ErrorBoundary",
          level: "error",
          message: `React error boundary caught: ${error.message}`,
          metadata: {
            errorName: error.name,
            errorStack: error.stack,
            componentStack: errorInfo.componentStack,
            timestamp: new Date().toISOString()
          }
        })
      }).catch(() => {
        // Ignore if log store not available
      })
    } catch {
      // Ignore logging errors
    }
  }

  handleRetry = async () => {
    this.setState({ isRetrying: true })

    try {
      // Try to reconnect WebSocket
      websocketService.disconnect()
      await new Promise(resolve => setTimeout(resolve, 1000))
      websocketService.enableAutoConnect()

      // Reset error state after a delay
      setTimeout(() => {
        this.setState({
          hasError: false,
          error: null,
          errorInfo: null,
          isRetrying: false
        })
      }, 2000)
    } catch (retryError) {
      console.error('[WebSocketErrorBoundary] Retry failed:', retryError)
      this.setState({ isRetrying: false })
    }
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      // Check if it's likely a WebSocket-related error
      const error = this.state.error
      const isWebSocketError = error && (
        error.message.toLowerCase().includes('websocket') ||
        error.message.toLowerCase().includes('connection') ||
        error.stack?.toLowerCase().includes('websocket')
      )

      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <Card className="mx-auto max-w-lg mt-8 border-red-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-5 w-5" />
              {isWebSocketError ? 'Connection Error' : 'Something went wrong'}
            </CardTitle>
            <CardDescription>
              {isWebSocketError 
                ? 'There was a problem with the WebSocket connection. This may be due to network issues or the backend server being unavailable.'
                : 'An unexpected error occurred. The page may need to be refreshed.'
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800 font-medium mb-1">Error Details:</p>
              <p className="text-sm text-red-700 font-mono">
                {error?.name}: {error?.message}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-2">
              <Button
                onClick={this.handleRetry}
                disabled={this.state.isRetrying}
                variant="outline"
                className="flex-1"
              >
                {this.state.isRetrying ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Retrying...
                  </>
                ) : (
                  <>
                    <Wifi className="h-4 w-4 mr-2" />
                    {isWebSocketError ? 'Reconnect' : 'Retry'}
                  </>
                )}
              </Button>
              <Button
                onClick={this.handleReload}
                variant="default"
                className="flex-1"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Page
              </Button>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground">
                  Show technical details
                </summary>
                <div className="mt-2 p-3 bg-gray-100 rounded-lg overflow-auto">
                  <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                    {error?.stack}
                  </pre>
                  <pre className="text-xs text-gray-600 whitespace-pre-wrap mt-2">
                    Component Stack: {this.state.errorInfo.componentStack}
                  </pre>
                </div>
              </details>
            )}
          </CardContent>
        </Card>
      )
    }

    return this.props.children
  }
}

// Hook version for functional components
export function useWebSocketErrorHandler() {
  const handleError = (error: Error, context?: string) => {
    console.error(`[WebSocket Error - ${context || 'Unknown'}]:`, error)
    
    // Try to log to our logging system
    try {
      import("@/lib/stores/log-store").then(({ useLogStore }) => {
        useLogStore.getState().addLog({
          agent: "WebSocket",
          level: "error",
          message: `${context ? `${context}: ` : ''}${error.message}`,
          metadata: {
            errorName: error.name,
            errorStack: error.stack,
            context: context || 'unknown',
            timestamp: new Date().toISOString()
          }
        })
      }).catch(() => {
        // Ignore if log store not available
      })
    } catch {
      // Ignore logging errors
    }
  }

  const handleConnectionError = (error: any) => {
    const message = error?.message || 'Connection error occurred'
    handleError(new Error(message), 'WebSocket Connection')
  }

  return {
    handleError,
    handleConnectionError
  }
}

export default WebSocketErrorBoundary
