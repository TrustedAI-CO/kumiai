/**
 * Error Utilities
 *
 * Consistent error handling and message extraction
 */

/**
 * Extract error message from unknown error type
 * Handles Error objects, string errors, and unknown types
 */
export function getErrorMessage(err: unknown, fallback: string = 'An error occurred'): string {
  if (err instanceof Error) {
    return err.message;
  }
  if (typeof err === 'string') {
    return err;
  }
  return fallback;
}

/**
 * Check if error is a specific type
 */
export function isErrorType(err: unknown, type: string): boolean {
  return err instanceof Error && err.name === type;
}

/**
 * Log error with context
 */
export function logError(context: string, err: unknown): void {
  console.error(`[${context}] Error:`, err);
}

/**
 * Create error with context
 */
export function createError(message: string, context?: string): Error {
  return new Error(context ? `[${context}] ${message}` : message);
}
