/**
 * API Services Integration
 * Central export point for all API services and utilities
 */

// Core API client
export { apiClient, APIError, handleAPIError, isApiResponseSuccess, isApiResponseError } from './client';

// Type definitions
export type * from './types';

// Service classes
export { projectsService } from './projects.service';
export { healthService } from './health.service';
export { agentsService } from './agents.service';
export { hitlService } from './hitl.service';

// Error handling
export { APIErrorBoundary, useAPIErrorHandler, withAPIErrorBoundary } from './error-boundary';

// Loading states
export {
  LoadingSpinner,
  LoadingCard,
  LoadingSkeleton,
  DataTableSkeleton,
  LoadingOverlay,
  AsyncOperationIndicator,
  useLoadingState,
  withLoadingState,
} from './loading-states';

// WebSocket integration
export { EnhancedWebSocketClient, WebSocketManager, websocketManager } from '../websocket/enhanced-websocket-client';

// Safety integration
export { SafetyEventHandler, safetyEventHandler } from '../safety/safety-event-handler';
export type { SafetyAlert, SafetyAction, SafetyEventConfig } from '../safety/safety-event-handler';

/**
 * Initialize API services with configuration
 */
export interface APIConfig {
  baseURL?: string;
  timeout?: number;
  retries?: number;
  websocketURL?: string;
  enableSafetyHandling?: boolean;
  safetyConfig?: {
    enableAudioAlerts?: boolean;
    enableNotifications?: boolean;
    emergencyContactEmail?: string;
  };
}

/**
 * Initialize all API services
 */
export function initializeAPIServices(config: APIConfig = {}): {
  api: typeof apiClient;
  websocket: WebSocketManager;
  safety: SafetyEventHandler;
} {
  // Configure API client
  if (config.baseURL) {
    apiClient.setRetryConfig({
      maxAttempts: config.retries || 3,
    });
  }

  // Initialize WebSocket manager
  const websocket = websocketManager;

  // Initialize safety handler
  const safety = safetyEventHandler;

  // Connect safety handler to global WebSocket if enabled
  if (config.enableSafetyHandling !== false) {
    const globalConnection = websocket.getGlobalConnection();
    safety.connectToWebSocket(globalConnection);
  }

  console.log('[API Services] Initialized with config:', {
    baseURL: config.baseURL || 'default',
    websocketURL: config.websocketURL || 'default',
    safetyEnabled: config.enableSafetyHandling !== false,
  });

  return {
    api: apiClient,
    websocket,
    safety,
  };
}

/**
 * Clean up all API services
 */
export function cleanupAPIServices(): void {
  websocketManager.disconnectAll();
  safetyEventHandler.disconnectFromWebSocket();
  console.log('[API Services] Cleaned up all connections');
}