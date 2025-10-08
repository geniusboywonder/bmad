/**
 * API Client with error handling and retry logic
 * Provides a centralized HTTP client for backend communication
 */

import { ApiResponse, ApiError, RequestConfig } from './types';

const SERVER_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const BROWSER_BASE_URL = '';
const DEFAULT_TIMEOUT = 30000;
const MAX_RETRIES = 3;

/**
 * Custom API Error class for structured error handling
 */
export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Retry configuration for different types of errors
 */
interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  retryableStatuses: number[];
}

const defaultRetryConfig: RetryConfig = {
  maxAttempts: MAX_RETRIES,
  baseDelay: 1000, // 1 second
  maxDelay: 30000, // 30 seconds
  retryableStatuses: [408, 429, 500, 502, 503, 504], // Timeout, rate limit, server errors
};

/**
 * Exponential backoff delay calculation
 */
function calculateDelay(attempt: number, baseDelay: number, maxDelay: number): number {
  const delay = baseDelay * Math.pow(2, attempt - 1);
  return Math.min(delay, maxDelay);
}

/**
 * Sleep utility for retry delays
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Enhanced fetch with timeout support
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout: number = DEFAULT_TIMEOUT
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new APIError(408, 'Request timeout');
    }
    throw error;
  }
}

/**
 * Main API client class
 */
export class ApiClient {
  private baseURL: string;
  private defaultHeaders: Record<string, string>;
  private retryConfig: RetryConfig;

  constructor(baseURL?: string) {
    const resolvedBase =
      baseURL ??
      (typeof window === 'undefined' ? SERVER_BASE_URL : BROWSER_BASE_URL);

    this.baseURL = resolvedBase.replace(/\/$/, ''); // Remove trailing slash
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    this.retryConfig = { ...defaultRetryConfig };
  }

  /**
   * Set authentication header
   */
  setAuthToken(token: string): void {
    this.defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Remove authentication header
   */
  clearAuthToken(): void {
    delete this.defaultHeaders['Authorization'];
  }

  /**
   * Update retry configuration
   */
  setRetryConfig(config: Partial<RetryConfig>): void {
    this.retryConfig = { ...this.retryConfig, ...config };
  }

  /**
   * Make HTTP request with retry logic
   */
  async request<T = any>(config: RequestConfig): Promise<ApiResponse<T>> {
    const {
      method,
      url,
      data,
      params,
      timeout = DEFAULT_TIMEOUT,
      retries = this.retryConfig.maxAttempts,
    } = config;

    const fullUrl = this.buildUrl(url, params);
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const requestOptions: RequestInit = {
          method,
          headers: { ...this.defaultHeaders },
        };

        if (data && method !== 'GET') {
          requestOptions.body = JSON.stringify(data);
        }

        console.log(`[API] ${method} ${fullUrl} (attempt ${attempt}/${retries})`);

        const response = await fetchWithTimeout(fullUrl, requestOptions, timeout);

        // Handle successful responses
        if (response.ok) {
          const responseData = await this.parseResponse<T>(response);
          return {
            success: true,
            data: responseData,
            timestamp: new Date().toISOString(),
          };
        }

        // Handle error responses
        const errorData = await this.parseErrorResponse(response);
        const apiError = new APIError(response.status, errorData.message, errorData.details);

        // Check if error is retryable
        if (!this.isRetryableError(apiError, attempt, retries)) {
          throw apiError;
        }

        lastError = apiError;
        console.warn(`[API] Request failed (attempt ${attempt}/${retries}):`, apiError.message);

        // Wait before retry (except on last attempt)
        if (attempt < retries) {
          const delay = calculateDelay(attempt, this.retryConfig.baseDelay, this.retryConfig.maxDelay);
          console.log(`[API] Retrying in ${delay}ms...`);
          await sleep(delay);
        }

      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        // Don't retry on network/timeout errors on last attempt
        if (attempt === retries) {
          break;
        }

        console.warn(`[API] Network error (attempt ${attempt}/${retries}):`, lastError.message);

        const delay = calculateDelay(attempt, this.retryConfig.baseDelay, this.retryConfig.maxDelay);
        await sleep(delay);
      }
    }

    // All attempts failed
    const finalError = lastError || new Error('Unknown error occurred');

    return {
      success: false,
      error: {
        code: finalError instanceof APIError ? String(finalError.status) : 'NETWORK_ERROR',
        message: finalError.message,
        details: finalError instanceof APIError ? finalError.details : undefined,
      },
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Convenience methods for different HTTP verbs
   */
  async get<T = any>(url: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    return this.request<T>({ method: 'GET', url, params });
  }

  async post<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>({ method: 'POST', url, data });
  }

  async put<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>({ method: 'PUT', url, data });
  }

  async patch<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>({ method: 'PATCH', url, data });
  }

  async delete<T = any>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>({ method: 'DELETE', url });
  }

  /**
   * Build full URL with query parameters
   */
  private buildUrl(url: string, params?: Record<string, any>): string {
    const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`;

    if (!params || Object.keys(params).length === 0) {
      return fullUrl;
    }

    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });

    const queryString = searchParams.toString();
    return queryString ? `${fullUrl}?${queryString}` : fullUrl;
  }

  /**
   * Parse successful response
   */
  private async parseResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type');

    if (contentType?.includes('application/json')) {
      return response.json();
    }

    if (contentType?.includes('text/')) {
      return response.text() as unknown as T;
    }

    // For other content types, return as blob or buffer
    return response.blob() as unknown as T;
  }

  /**
   * Parse error response
   */
  private async parseErrorResponse(response: Response): Promise<{ message: string; details?: any }> {
    try {
      const data = await response.json();
      return {
        message: data.message || data.detail || `HTTP ${response.status}: ${response.statusText}`,
        details: data,
      };
    } catch {
      return {
        message: `HTTP ${response.status}: ${response.statusText}`,
      };
    }
  }

  /**
   * Determine if error is retryable
   */
  private isRetryableError(error: APIError, attempt: number, maxAttempts: number): boolean {
    // Don't retry if we've reached max attempts
    if (attempt >= maxAttempts) {
      return false;
    }

    // Retry on specific status codes
    return this.retryConfig.retryableStatuses.includes(error.status);
  }
}

/**
 * Default API client instance
 */
export const apiClient = new ApiClient();

/**
 * Error handler utility for API responses
 */
export function handleAPIError(error: any): APIError {
  if (error instanceof APIError) {
    return error;
  }

  if (error?.response) {
    return new APIError(
      error.response.status,
      error.response.data?.message || 'API Error',
      error.response.data
    );
  }

  return new APIError(0, 'Network Error', error);
}

/**
 * Type guard for API response success
 */
export function isApiResponseSuccess<T>(response: ApiResponse<T>): response is ApiResponse<T> & { success: true; data: T } {
  return response.success === true;
}

/**
 * Type guard for API response error
 */
export function isApiResponseError<T>(response: ApiResponse<T>): response is ApiResponse<T> & { success: false; error: NonNullable<ApiResponse<T>['error']> } {
  return response.success === false;
}
