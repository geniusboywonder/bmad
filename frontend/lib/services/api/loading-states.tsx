/**
 * Loading States Components
 * Comprehensive loading indicators for API operations
 */

import React from 'react';
import { Loader2, RefreshCw, AlertCircle, CheckCircle, Clock, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

export interface LoadingState {
  isLoading: boolean;
  error?: string | null;
  progress?: number;
  message?: string;
  type?: 'default' | 'processing' | 'uploading' | 'connecting' | 'retrying';
}

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  className?: string;
}

/**
 * Simple loading spinner component
 */
export function LoadingSpinner({ size = 'md', message, className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className={cn('flex items-center justify-center', className)}>
      <div className="flex flex-col items-center space-y-2">
        <Loader2 className={cn('animate-spin text-primary', sizeClasses[size])} />
        {message && (
          <p className="text-sm text-muted-foreground text-center">{message}</p>
        )}
      </div>
    </div>
  );
}

interface LoadingCardProps {
  title?: string;
  description?: string;
  progress?: number;
  message?: string;
  type?: LoadingState['type'];
  className?: string;
}

/**
 * Loading card with progress and status information
 */
export function LoadingCard({
  title = 'Loading...',
  description,
  progress,
  message,
  type = 'default',
  className,
}: LoadingCardProps) {
  const getIcon = () => {
    switch (type) {
      case 'processing':
        return <Zap className="w-5 h-5 text-blue-500" />;
      case 'uploading':
        return <RefreshCw className="w-5 h-5 text-green-500 animate-spin" />;
      case 'connecting':
        return <Clock className="w-5 h-5 text-amber-500" />;
      case 'retrying':
        return <RefreshCw className="w-5 h-5 text-orange-500 animate-spin" />;
      default:
        return <Loader2 className="w-5 h-5 text-primary animate-spin" />;
    }
  };

  const getTypeColor = () => {
    switch (type) {
      case 'processing':
        return 'text-blue-500';
      case 'uploading':
        return 'text-green-500';
      case 'connecting':
        return 'text-amber-500';
      case 'retrying':
        return 'text-orange-500';
      default:
        return 'text-primary';
    }
  };

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center space-x-2">
          {getIcon()}
          <CardTitle className="text-lg">{title}</CardTitle>
          <Badge variant="outline" className={cn('text-xs', getTypeColor())}>
            {type.toUpperCase()}
          </Badge>
        </div>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="space-y-4">
        {progress !== undefined && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="w-full" />
          </div>
        )}
        {message && (
          <p className="text-sm text-muted-foreground">{message}</p>
        )}
      </CardContent>
    </Card>
  );
}

interface LoadingSkeletonProps {
  lines?: number;
  showAvatar?: boolean;
  showButton?: boolean;
  className?: string;
}

/**
 * Skeleton loading placeholder
 */
export function LoadingSkeleton({
  lines = 3,
  showAvatar = false,
  showButton = false,
  className,
}: LoadingSkeletonProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {showAvatar && (
        <div className="flex items-center space-x-4">
          <Skeleton className="h-12 w-12 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-4 w-[200px]" />
          </div>
        </div>
      )}

      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, index) => (
          <Skeleton
            key={index}
            className={`h-4 ${
              index === lines - 1 ? 'w-[180px]' : 'w-full'
            }`}
          />
        ))}
      </div>

      {showButton && (
        <Skeleton className="h-10 w-[100px]" />
      )}
    </div>
  );
}

interface DataTableSkeletonProps {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
  className?: string;
}

/**
 * Data table skeleton loading
 */
export function DataTableSkeleton({
  rows = 5,
  columns = 4,
  showHeader = true,
  className,
}: DataTableSkeletonProps) {
  return (
    <div className={cn('space-y-4', className)}>
      {showHeader && (
        <div className="flex space-x-4">
          {Array.from({ length: columns }).map((_, index) => (
            <Skeleton key={index} className="h-8 flex-1" />
          ))}
        </div>
      )}

      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex space-x-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} className="h-6 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
  progress?: number;
  type?: LoadingState['type'];
  backdrop?: boolean;
  className?: string;
}

/**
 * Full-screen or container overlay loading
 */
export function LoadingOverlay({
  isVisible,
  message,
  progress,
  type = 'default',
  backdrop = true,
  className,
}: LoadingOverlayProps) {
  if (!isVisible) return null;

  return (
    <div
      className={cn(
        'absolute inset-0 z-50 flex items-center justify-center',
        backdrop && 'bg-background/80 backdrop-blur-sm',
        className
      )}
    >
      <LoadingCard
        title="Loading"
        message={message}
        progress={progress}
        type={type}
        className="max-w-sm"
      />
    </div>
  );
}

interface AsyncOperationIndicatorProps {
  state: LoadingState;
  successMessage?: string;
  className?: string;
}

/**
 * Comprehensive async operation indicator
 */
export function AsyncOperationIndicator({
  state,
  successMessage = 'Operation completed successfully',
  className,
}: AsyncOperationIndicatorProps) {
  const { isLoading, error, progress, message, type } = state;

  if (error) {
    return (
      <div className={cn('flex items-center space-x-2 text-destructive', className)}>
        <AlertCircle className="w-4 h-4" />
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={cn('flex items-center space-x-2', className)}>
        <Loader2 className="w-4 h-4 animate-spin text-primary" />
        <span className="text-sm text-muted-foreground">
          {message || 'Processing...'}
        </span>
        {progress !== undefined && (
          <span className="text-xs text-muted-foreground">
            {Math.round(progress)}%
          </span>
        )}
      </div>
    );
  }

  // Show success state briefly
  return (
    <div className={cn('flex items-center space-x-2 text-green-600', className)}>
      <CheckCircle className="w-4 h-4" />
      <span className="text-sm">{successMessage}</span>
    </div>
  );
}

/**
 * Hook for managing loading states
 */
export function useLoadingState(initialLoading: boolean = false) {
  const [state, setState] = React.useState<LoadingState>({
    isLoading: initialLoading,
  });

  const setLoading = React.useCallback((isLoading: boolean, message?: string, type?: LoadingState['type']) => {
    setState(prev => ({
      ...prev,
      isLoading,
      message: isLoading ? message : undefined,
      type: isLoading ? type : undefined,
      error: isLoading ? undefined : prev.error, // Clear error when starting new operation
    }));
  }, []);

  const setProgress = React.useCallback((progress: number, message?: string) => {
    setState(prev => ({
      ...prev,
      progress: Math.max(0, Math.min(100, progress)),
      message: message || prev.message,
    }));
  }, []);

  const setError = React.useCallback((error: string) => {
    setState(prev => ({
      ...prev,
      isLoading: false,
      error,
      progress: undefined,
    }));
  }, []);

  const setSuccess = React.useCallback((message?: string) => {
    setState(prev => ({
      ...prev,
      isLoading: false,
      error: undefined,
      message,
      progress: 100,
    }));
  }, []);

  const reset = React.useCallback(() => {
    setState({
      isLoading: false,
    });
  }, []);

  return {
    ...state,
    setLoading,
    setProgress,
    setError,
    setSuccess,
    reset,
  };
}

/**
 * Higher-order component for adding loading states to any component
 */
export function withLoadingState<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  loadingProps?: Partial<LoadingOverlayProps>
) {
  const WithLoadingStateComponent = (props: P & { isLoading?: boolean }) => {
    const { isLoading, ...restProps } = props;

    return (
      <div className="relative">
        <WrappedComponent {...(restProps as P)} />
        <LoadingOverlay
          isVisible={!!isLoading}
          {...loadingProps}
        />
      </div>
    );
  };

  WithLoadingStateComponent.displayName =
    `withLoadingState(${WrappedComponent.displayName || WrappedComponent.name})`;

  return WithLoadingStateComponent;
}