import React, { Component, ErrorInfo, ReactNode } from "react"
import { emergencyStorageCleanup } from "@/lib/utils/emergency-cleanup"

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

class ChatErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Chat component error:', error, errorInfo)
    
    // Check if it's a timestamp-related error
    if (error.message.includes('timestamp') || 
        error.message.includes('toISOString') ||
        error.message.includes('not a function')) {
      console.warn('Detected timestamp error, attempting storage cleanup...')
      const cleaned = emergencyStorageCleanup()
      if (cleaned) {
        console.log('Storage cleaned, will reload page...')
        setTimeout(() => {
          window.location.reload()
        }, 1000)
      }
    }
  }

  private handleReload = () => {
    emergencyStorageCleanup()
    window.location.reload()
  }

  private handleClearStorage = () => {
    const confirmed = window.confirm(
      'This will clear all chat history and reload the page. Continue?'
    )
    if (confirmed) {
      emergencyStorageCleanup()
      window.location.reload()
    }
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="text-center space-y-4 p-6">
            <div className="text-red-600 text-lg font-semibold">
              ⚠️ Chat Component Error
            </div>
            <p className="text-sm text-gray-600 max-w-md">
              There was an issue loading the chat interface. This is usually caused by corrupted data.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleReload}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Reload Page
              </button>
              <button
                onClick={this.handleClearStorage}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Clear Data & Reload
              </button>
            </div>
            {process.env.NODE_ENV === 'development' && (
              <details className="mt-4 text-xs text-left">
                <summary className="cursor-pointer text-gray-500">Error Details</summary>
                <pre className="mt-2 p-2 bg-gray-100 rounded text-red-600 overflow-auto">
                  {this.state.error?.stack}
                </pre>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ChatErrorBoundary
