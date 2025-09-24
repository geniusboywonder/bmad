/**
 * API Error Boundary Component
 * Enhanced error boundary for API integration with detailed error handling
 */

import React, { Component, ReactNode } from 'react';
import { APIError } from './client';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, RefreshCw, Bug, Wifi, WifiOff } from 'lucide-react';

interface APIErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: any;
  retryCount: number;
}

interface APIErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, retry: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: any) => void;
  maxRetries?: number;
  showDetails?: boolean;
}

export class APIErrorBoundary extends Component<APIErrorBoundaryProps, APIErrorBoundaryState> {
  private retryTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: APIErrorBoundaryProps) {
    super(props);

    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<APIErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('API Error Boundary caught an error:', error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // Call the onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  componentWillUnmount() {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  handleRetry = () => {
    const { maxRetries = 3 } = this.props;
    const { retryCount } = this.state;

    if (retryCount < maxRetries) {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: retryCount + 1,
      });
    }
  };

  handleAutoRetry = () => {
    // Auto retry with exponential backoff
    const delay = Math.min(1000 * Math.pow(2, this.state.retryCount), 30000);

    this.retryTimeoutId = setTimeout(() => {
      this.handleRetry();
    }, delay);
  };

  getErrorType = (error: Error): 'network' | 'api' | 'auth' | 'validation' | 'unknown' => {
    if (error instanceof APIError) {
      if (error.status === 401 || error.status === 403) return 'auth';
      if (error.status === 400 || error.status === 422) return 'validation';
      if (error.status >= 500) return 'api';
      if (error.status === 0) return 'network';
    }

    if (error.message.includes('Network Error') || error.message.includes('fetch')) {
      return 'network';
    }

    return 'unknown';
  };

  getErrorIcon = (errorType: string) => {
    switch (errorType) {
      case 'network':
        return <WifiOff className="w-6 h-6 text-destructive" />;
      case 'api':
        return <AlertTriangle className="w-6 h-6 text-destructive" />;
      case 'auth':
        return <Wifi className="w-6 h-6 text-amber" />;
      default:
        return <Bug className="w-6 h-6 text-destructive" />;
    }
  };

  getErrorMessage = (error: Error, errorType: string): string => {
    if (error instanceof APIError) {
      return error.message;
    }

    switch (errorType) {
      case 'network':
        return 'Unable to connect to the server. Please check your internet connection.';
      case 'api':
        return 'The server encountered an error. Please try again later.';
      case 'auth':
        return 'Authentication failed. Please log in again.';
      case 'validation':
        return 'Invalid data provided. Please check your input.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  };

  getErrorSuggestions = (errorType: string): string[] => {
    switch (errorType) {
      case 'network':
        return [
          'Check your internet connection',
          'Verify the server is running',
          'Try refreshing the page',
        ];
      case 'api':
        return [
          'Wait a moment and try again',
          'Check if the server is overloaded',
          'Contact support if the problem persists',
        ];
      case 'auth':
        return [
          'Log out and log back in',
          'Clear browser cache and cookies',
          'Check if your session has expired',
        ];
      case 'validation':
        return [
          'Check your input data',
          'Ensure required fields are filled',
          'Verify data format is correct',
        ];
      default:
        return [
          'Try refreshing the page',
          'Clear browser cache',
          'Contact support if the problem persists',
        ];
    }
  };

  render() {
    const { children, fallback, maxRetries = 3, showDetails = false } = this.props;
    const { hasError, error, errorInfo, retryCount } = this.state;

    if (hasError && error) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback(error, this.handleRetry);
      }

      const errorType = this.getErrorType(error);
      const errorMessage = this.getErrorMessage(error, errorType);
      const suggestions = this.getErrorSuggestions(errorType);
      const canRetry = retryCount < maxRetries;

      return (
        <div className="flex items-center justify-center min-h-[400px] p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                {this.getErrorIcon(errorType)}
              </div>
              <CardTitle className="text-xl">Something went wrong</CardTitle>
              <CardDescription>{errorMessage}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-center space-x-2">
                <Badge variant="destructive" className="text-xs">
                  {errorType.toUpperCase()}
                </Badge>
                {error instanceof APIError && (
                  <Badge variant="outline" className="text-xs">
                    {error.status}
                  </Badge>
                )}
              </div>

              {suggestions.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Try these solutions:</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    {suggestions.map((suggestion, index) => (
                      <li key={index} className="flex items-start">
                        <span className="mr-2">•</span>
                        {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex flex-col space-y-2">
                {canRetry && (
                  <Button onClick={this.handleRetry} className="w-full">
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Try Again ({maxRetries - retryCount} attempts left)
                  </Button>
                )}

                <Button
                  variant="outline"
                  onClick={() => window.location.reload()}
                  className="w-full"
                >
                  Refresh Page
                </Button>
              </div>

              {showDetails && (
                <details className="mt-4">
                  <summary className="text-sm cursor-pointer text-muted-foreground">
                    Technical Details
                  </summary>
                  <div className="mt-2 p-3 bg-muted rounded-md text-xs font-mono">
                    <div><strong>Error:</strong> {error.message}</div>
                    {error instanceof APIError && (
                      <>
                        <div><strong>Status:</strong> {error.status}</div>
                        {error.details && (
                          <div><strong>Details:</strong> {JSON.stringify(error.details, null, 2)}</div>
                        )}
                      </>
                    )}
                    {errorInfo && (
                      <div><strong>Stack:</strong> {errorInfo.componentStack}</div>
                    )}
                  </div>
                </details>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return children;
  }
}

/**
 * Hook for handling API errors in functional components
 */
export function useAPIErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null);

  const handleError = React.useCallback((error: Error) => {
    console.error('API Error:', error);
    setError(error);
  }, []);

  const clearError = React.useCallback(() => {
    setError(null);
  }, []);

  const retry = React.useCallback((asyncFn: () => Promise<any>) => {
    clearError();
    return asyncFn().catch(handleError);
  }, [clearError, handleError]);

  return {
    error,
    hasError: !!error,
    handleError,
    clearError,
    retry,
  };
}

/**
 * Higher-order component for wrapping components with API error boundary
 */
export function withAPIErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  errorBoundaryProps?: Partial<APIErrorBoundaryProps>
) {
  const WithAPIErrorBoundaryComponent = (props: P) => (
    <APIErrorBoundary {...errorBoundaryProps}>
      <WrappedComponent {...props} />
    </APIErrorBoundary>
  );

  WithAPIErrorBoundaryComponent.displayName =
    `withAPIErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;

  return WithAPIErrorBoundaryComponent;
}