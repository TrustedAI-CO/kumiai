/**
 * Custom Hooks Library
 *
 * Centralized barrel export organized by category
 */

// API hooks - data fetching and session management
export * from './api';

// Query hooks - React Query wrappers
export * from './queries';

// State hooks - state management utilities
export * from './state';

// Utility hooks - general purpose utilities
export * from './utils';

// UI hooks
export { useToast } from '../components/ui/composite/Toast';
export { useToast as useNotification } from '../components/ui/composite/Toast';
