/**
 * API Client Tests - Phase 1 Integration
 * Tests for the core API client with retry logic and error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiClient, APIError, handleAPIError, isApiResponseSuccess, isApiResponseError } from './client'

// Mock fetch for testing
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('APIError', () => {
  it('should create an APIError instance with correct properties', () => {
    const error = new APIError(404, 'Not Found', { code: 'RESOURCE_NOT_FOUND' })

    expect(error).toBeInstanceOf(Error)
    expect(error.name).toBe('APIError')
    expect(error.status).toBe(404)
    expect(error.message).toBe('Not Found')
    expect(error.details).toEqual({ code: 'RESOURCE_NOT_FOUND' })
  })
})

describe('handleAPIError', () => {
  it('should handle response errors correctly', () => {
    const axiosError = {
      response: {
        status: 500,
        data: {
          message: 'Internal Server Error',
          details: { error_code: 'SERVER_ERROR' }
        }
      }
    }

    const result = handleAPIError(axiosError)

    expect(result).toBeInstanceOf(APIError)
    expect(result.status).toBe(500)
    expect(result.message).toBe('Internal Server Error')
    expect(result.details).toEqual({ error_code: 'SERVER_ERROR' })
  })

  it('should handle network errors correctly', () => {
    const networkError = {
      message: 'Network Error',
      code: 'NETWORK_ERROR'
    }

    const result = handleAPIError(networkError)

    expect(result).toBeInstanceOf(APIError)
    expect(result.status).toBe(0)
    expect(result.message).toBe('Network Error')
  })

  it('should handle errors without response data', () => {
    const axiosError = {
      response: {
        status: 400,
        data: null
      }
    }

    const result = handleAPIError(axiosError)

    expect(result).toBeInstanceOf(APIError)
    expect(result.status).toBe(400)
    expect(result.message).toBe('API Error')
  })
})

describe('API Response Type Guards', () => {
  describe('isApiResponseSuccess', () => {
    it('should return true for successful responses', () => {
      const successResponse = { success: true, data: { id: '1' } }
      expect(isApiResponseSuccess(successResponse)).toBe(true)
    })

    it('should return false for error responses', () => {
      const errorResponse = { success: false, error: 'Failed' }
      expect(isApiResponseSuccess(errorResponse)).toBe(false)
    })
  })

  describe('isApiResponseError', () => {
    it('should return true for error responses', () => {
      const errorResponse = { success: false, error: 'Failed' }
      expect(isApiResponseError(errorResponse)).toBe(true)
    })

    it('should return false for successful responses', () => {
      const successResponse = { success: true, data: { id: '1' } }
      expect(isApiResponseError(successResponse)).toBe(false)
    })
  })
})

describe('apiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should have correct base configuration', () => {
    expect(apiClient.defaults.baseURL).toBe('http://localhost:8000')
    expect(apiClient.defaults.timeout).toBe(30000)
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json')
  })

  it('should retry failed requests with exponential backoff', async () => {
    // Mock consecutive failures then success
    mockFetch
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ success: true, data: { id: '1' } })
      })

    // Test that retry logic works
    const startTime = Date.now()
    const response = await apiClient.get('/test')
    const endTime = Date.now()

    // Should have taken some time due to retries
    expect(endTime - startTime).toBeGreaterThan(100)
    expect(mockFetch).toHaveBeenCalledTimes(3)
  })

  it('should handle successful API responses', async () => {
    const mockData = { success: true, data: { id: '1', name: 'Test' } }
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockData)
    })

    const response = await apiClient.get('/test')
    expect(response.data).toEqual(mockData)
  })

  it('should handle API error responses', async () => {
    const mockError = { success: false, error: 'Validation failed' }
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve(mockError)
    })

    await expect(apiClient.get('/test')).rejects.toThrow()
  })

  it('should handle network timeouts', async () => {
    vi.useFakeTimers()

    mockFetch.mockImplementationOnce(
      () => new Promise(resolve => setTimeout(resolve, 35000))
    )

    const promise = apiClient.get('/test')

    // Fast-forward time past timeout
    vi.advanceTimersByTime(35000)

    await expect(promise).rejects.toThrow()

    vi.useRealTimers()
  })

  it('should include authorization headers when configured', async () => {
    const token = 'test-token'
    apiClient.defaults.headers['Authorization'] = `Bearer ${token}`

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ success: true, data: {} })
    })

    await apiClient.get('/test')

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/test',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': `Bearer ${token}`
        })
      })
    )
  })

  it('should handle rate limiting with retry after header', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 429,
        headers: new Map([['retry-after', '2']]),
        json: () => Promise.resolve({ success: false, error: 'Rate limited' })
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ success: true, data: {} })
      })

    const startTime = Date.now()
    await apiClient.get('/test')
    const endTime = Date.now()

    // Should have waited for retry-after
    expect(endTime - startTime).toBeGreaterThan(1000)
  })
})