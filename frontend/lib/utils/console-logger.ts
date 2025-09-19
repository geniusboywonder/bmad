// Console Logger - Captures and forwards console messages to log store
// Enhanced error handling for malformed objects

import { useLogStore } from "../stores/log-store"

interface ConsoleMethod {
  (message?: any, ...optionalParams: any[]): void
}

class ConsoleLogger {
  private originalConsole: {
    log: ConsoleMethod
    error: ConsoleMethod
    warn: ConsoleMethod
    info: ConsoleMethod
    debug: ConsoleMethod
  }

  private isInitialized = false

  constructor() {
    // Store original console methods
    this.originalConsole = {
      log: console.log,
      error: console.error,
      warn: console.warn,
      info: console.info,
      debug: console.debug
    }
  }

  init() {
    if (this.isInitialized || typeof window === 'undefined') {
      return
    }

    console.log("[ConsoleLogger] Initializing console message capture...")

    // Override console methods to capture and forward to log store
    console.log = this.createLogProxy('info', this.originalConsole.log)
    console.error = this.createLogProxy('error', this.originalConsole.error)
    console.warn = this.createLogProxy('warning', this.originalConsole.warn)
    console.info = this.createLogProxy('info', this.originalConsole.info)
    console.debug = this.createLogProxy('debug', this.originalConsole.debug)

    this.isInitialized = true
    
    // Test the console capture
    console.info("[ConsoleLogger] Console capture initialized successfully")
  }

  private safeStringify(arg: any): string {
    try {
      if (arg === null) return 'null'
      if (arg === undefined) return 'undefined'
      if (typeof arg === 'string') return arg
      if (typeof arg === 'number' || typeof arg === 'boolean') return String(arg)
      
      if (typeof arg === 'object') {
        // Handle special cases for common problematic objects
        if (arg instanceof Error) {
          return `${arg.name}: ${arg.message}${arg.stack ? '\n' + arg.stack : ''}`
        }
        
        if (arg instanceof Event) {
          return `${arg.type} event${arg.target ? ` on ${arg.target}` : ''}`
        }
        
        // Check for empty objects
        const keys = Object.keys(arg)
        if (keys.length === 0) {
          // Check if it's a plain object or has prototype properties
          const prototype = Object.getPrototypeOf(arg)
          if (prototype === Object.prototype || prototype === null) {
            return '{} (empty object)'
          } else {
            return `{} (${prototype.constructor?.name || 'unknown'} instance)`
          }
        }
        
        // Try to stringify with circular reference handling
        try {
          return JSON.stringify(arg, this.getCircularReplacer(), 2)
        } catch (jsonError) {
          // If JSON.stringify fails, try alternative approach
          try {
            const entries = Object.entries(arg).slice(0, 5) // Limit to first 5 properties
            const preview = entries.map(([key, value]) => {
              try {
                const valueStr = typeof value === 'object' && value !== null 
                  ? '[Object]' 
                  : String(value)
                return `${key}: ${valueStr}`
              } catch {
                return `${key}: [Unreadable]`
              }
            }).join(', ')
            
            const remaining = Object.keys(arg).length - entries.length
            return `{${preview}${remaining > 0 ? `, ...${remaining} more` : ''}}`
          } catch {
            return `[Object: ${arg.constructor?.name || 'Unknown'}]`
          }
        }
      }
      
      // Fallback for any other type
      return String(arg)
    } catch (error) {
      // Ultimate fallback
      return '[Unstringifiable object]'
    }
  }

  private getCircularReplacer() {
    const seen = new WeakSet()
    return (key: string, value: any) => {
      if (typeof value === 'object' && value !== null) {
        if (seen.has(value)) {
          return '[Circular Reference]'
        }
        seen.add(value)
      }
      return value
    }
  }

  private createLogProxy(level: 'info' | 'error' | 'warning' | 'debug', originalMethod: ConsoleMethod) {
    return (message?: any, ...optionalParams: any[]) => {
      // Call original console method first
      originalMethod(message, ...optionalParams)

      try {
        // Convert arguments to string with enhanced error handling
        const allArgs = [message, ...optionalParams]
        const fullMessage = allArgs
          .map(arg => this.safeStringify(arg))
          .filter(str => str && str.trim() !== '')
          .join(' ')

        // Skip empty or whitespace-only messages
        if (!fullMessage || fullMessage.trim() === '') {
          return
        }

        // Determine agent based on message content
        const agent = this.determineAgent(fullMessage)
        
        // Add to log store with enhanced error handling
        const logEntry = {
          agent,
          level,
          message: fullMessage,
          source: 'system' as const,
          category: 'console' as const,
          metadata: {
            captured_from: 'frontend_console',
            original_level: level,
            timestamp: new Date().toISOString(),
            args_count: allArgs.length
          }
        }

        // Safely add to log store
        try {
          useLogStore.getState().addLog(logEntry)
        } catch (storeError) {
          // If log store fails, at least log to original console
          this.originalConsole.error('[ConsoleLogger] Failed to add to log store:', this.safeStringify(storeError))
          this.originalConsole.error('[ConsoleLogger] Original message was:', fullMessage)
        }
        
      } catch (error) {
        // If all else fails, use original console to report the issue
        this.originalConsole.error('[ConsoleLogger] Failed to process log message:', this.safeStringify(error))
        this.originalConsole.error('[ConsoleLogger] Original arguments:', message, ...optionalParams)
      }
    }
  }

  private determineAgent(message: string): string {
    // Enhanced agent detection with more specific patterns
    const patterns = [
      { pattern: /\[WebSocket\]/i, agent: 'WebSocket' },
      { pattern: /\[Agent\]/i, agent: 'Agent' },
      { pattern: /\[Backend\]/i, agent: 'Backend' },
      { pattern: /\[Frontend\]/i, agent: 'Frontend' },
      { pattern: /\[System\]/i, agent: 'System' },
      { pattern: /\[Analyst\]/i, agent: 'Analyst' },
      { pattern: /\[Architect\]/i, agent: 'Architect' },
      { pattern: /\[Developer\]/i, agent: 'Developer' },
      { pattern: /\[Tester\]/i, agent: 'Tester' },
      { pattern: /\[Deployer\]/i, agent: 'Deployer' },
      { pattern: /\[ConsoleLogger\]/i, agent: 'Logger' },
      { pattern: /Connection|WebSocket|ws:/i, agent: 'WebSocket' },
      { pattern: /Failed to establish|Connection error|onerror/i, agent: 'WebSocket' },
    ]

    for (const { pattern, agent } of patterns) {
      if (pattern.test(message)) {
        return agent
      }
    }
    
    // Default to Frontend for console messages
    return 'Frontend'
  }

  // Method to temporarily disable console capture
  disable() {
    if (!this.isInitialized) return

    console.log = this.originalConsole.log
    console.error = this.originalConsole.error
    console.warn = this.originalConsole.warn
    console.info = this.originalConsole.info
    console.debug = this.originalConsole.debug

    this.isInitialized = false
    this.originalConsole.log("[ConsoleLogger] Console capture disabled")
  }

  // Method to re-enable console capture
  enable() {
    this.init()
  }

  // Method to get initialization status
  isActive(): boolean {
    return this.isInitialized
  }

  // Method to test error handling
  testErrorHandling() {
    if (!this.isInitialized) {
      this.originalConsole.warn("[ConsoleLogger] Not initialized")
      return
    }

    console.log("[ConsoleLogger] Testing error handling...")
    console.error("[ConsoleLogger] Test error with empty object:", {})
    console.error("[ConsoleLogger] Test error with null:", null)
    console.error("[ConsoleLogger] Test error with undefined:", undefined)
    console.warn("[ConsoleLogger] Test warning with circular reference:", (() => {
      const obj: any = { name: 'test' }
      obj.self = obj
      return obj
    })())
    console.log("[ConsoleLogger] Error handling test complete")
  }
}

export const consoleLogger = new ConsoleLogger()

// Auto-initialize when module loads in browser
if (typeof window !== 'undefined') {
  // Small delay to ensure log store is ready
  setTimeout(() => {
    consoleLogger.init()
  }, 100)
}
