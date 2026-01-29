/**
 * Standardized error handling utilities
 * Provides consistent error logging and user messaging across the application
 */

/**
 * Extract a user-friendly error message from an unknown error object
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  if (error && typeof error === 'object' && 'message' in error) {
    return String(error.message);
  }
  return 'An unknown error occurred';
}

/**
 * Handle errors with consistent logging and user feedback
 * @param error - The error that occurred
 * @param context - Description of what operation failed (e.g., "create file", "load agents")
 * @param options - Configuration for error handling
 * @param options.notify - Function to call for user notification (e.g., toast.error)
 * @param options.showAlert - Whether to show browser alert (deprecated, use notify instead)
 * @returns The error message string
 */
export function handleError(
  error: unknown,
  context: string,
  options?: {
    notify?: (message: string, title?: string) => void;
    showAlert?: boolean;
  }
): string {
  const message = getErrorMessage(error);
  const fullMessage = `Failed to ${context}`;

  // Log to console with full context
  console.error(`[Error] ${fullMessage}:`, message, error);

  // Use notification function if provided (modern approach)
  if (options?.notify) {
    options.notify(message, fullMessage);
  }
  // Fall back to browser alert if explicitly requested (legacy support)
  else if (options?.showAlert === true) {
    alert(`${fullMessage}. Please try again.\n\nError: ${message}`);
  }

  return message;
}

/**
 * Handle errors silently (log only, no user alert)
 * Useful for background operations or non-critical failures
 */
export function handleErrorSilently(error: unknown, context: string): string {
  return handleError(error, context);
}

/**
 * Async wrapper that handles errors automatically
 * @param fn - Async function to execute
 * @param context - Description of the operation
 * @param options - Configuration for error handling
 * @param options.notify - Function to call for user notification (e.g., toast.error)
 * @param options.onError - Optional callback when error occurs
 * @returns Promise that resolves to the function result or undefined on error
 */
export async function withErrorHandling<T>(
  fn: () => Promise<T>,
  context: string,
  options?: {
    notify?: (message: string, title?: string) => void;
    onError?: (message: string) => void;
  }
): Promise<T | undefined> {
  try {
    return await fn();
  } catch (error) {
    const message = handleError(error, context, { notify: options?.notify });
    options?.onError?.(message);
    return undefined;
  }
}

/**
 * Async wrapper that handles errors silently
 * Useful for polling or background operations where user alerts would be disruptive
 */
export async function withSilentErrorHandling<T>(
  fn: () => Promise<T>,
  context: string
): Promise<T | undefined> {
  try {
    return await fn();
  } catch (error) {
    handleErrorSilently(error, context);
    return undefined;
  }
}
