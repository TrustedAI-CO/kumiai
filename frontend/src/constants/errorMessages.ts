/**
 * Error Message Constants
 *
 * Centralized error messages for consistent UX
 */

export const ERROR_MESSAGES = {
  // Session Errors
  SESSION_ERROR_TITLE: 'Session Error',
  SESSION_ERROR_READONLY: 'This session encountered an error. Chat history is read-only.',
  PM_SESSION_ERROR: 'PM session encountered an error. Chat history is available in read-only mode.',
  AGENT_SESSION_ERROR: 'Agent session encountered an error. Chat history is available in read-only mode.',
  NO_PM_SESSION: 'No PM session found. Try refreshing the page.',

  // Load Errors
  FAILED_LOAD_SESSIONS: 'Failed to load sessions',
  FAILED_LOAD_MESSAGES: 'Failed to load messages',
  FAILED_LOAD_FILES: 'Failed to load files',
  FAILED_LOAD_AGENTS: 'Failed to load agents',
  FAILED_LOAD_SKILLS: 'Failed to load skills',
  FAILED_LOAD_PROJECTS: 'Failed to load projects',

  // Save/Update Errors
  FAILED_SAVE: 'Failed to save changes',
  FAILED_CREATE: 'Failed to create item',
  FAILED_UPDATE: 'Failed to update item',
  FAILED_DELETE: 'Failed to delete item',

  // File Errors
  FAILED_UPLOAD: 'Failed to upload file',
  FAILED_DOWNLOAD: 'Failed to download file',
  FILE_TOO_LARGE: 'File size exceeds maximum allowed',
  INVALID_FILE_TYPE: 'Invalid file type',

  // Validation Errors
  REQUIRED_FIELD: 'This field is required',
  INVALID_INPUT: 'Invalid input',

  // Network Errors
  NETWORK_ERROR: 'Network error. Please check your connection.',
  TIMEOUT_ERROR: 'Request timed out. Please try again.',

  // Generic
  UNKNOWN_ERROR: 'An unexpected error occurred',
} as const;

export type ErrorMessageKey = keyof typeof ERROR_MESSAGES;
