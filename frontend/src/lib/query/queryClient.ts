/**
 * React Query Client Configuration
 *
 * Centralized configuration for TanStack Query with:
 * - Caching strategy
 * - Retry logic
 * - Error handling
 * - Default options
 */

import { QueryClient } from '@tanstack/react-query';

/**
 * Global query client instance
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Stale time: how long data is considered fresh
      staleTime: 1000 * 60 * 5, // 5 minutes

      // Cache time: how long inactive data stays in cache
      gcTime: 1000 * 60 * 30, // 30 minutes (formerly cacheTime)

      // Retry configuration
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors)
        if (error instanceof Error && 'status' in error) {
          const status = (error as any).status;
          if (status >= 400 && status < 500) {
            return false;
          }
        }
        // Retry up to 2 times for other errors
        return failureCount < 2;
      },

      // Retry delay with exponential backoff
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Refetch configuration
      refetchOnWindowFocus: false, // Don't refetch when window regains focus
      refetchOnReconnect: true,    // Refetch when reconnecting to network
      refetchOnMount: true,        // Refetch when component mounts

      // Network mode
      networkMode: 'online' // Only fetch when online
    },
    mutations: {
      // Retry mutations once on failure
      retry: 1,

      // Network mode
      networkMode: 'online'
    }
  }
});

/**
 * Query key factory for consistent query keys
 */
export const queryKeys = {
  // Projects
  projects: ['projects'] as const,
  project: (id: string) => ['projects', id] as const,

  // Agents
  agents: ['agents'] as const,
  agent: (id: string) => ['agents', id] as const,
  agentInstances: ['agentInstances'] as const,
  agentInstance: (id: string) => ['agentInstances', id] as const,

  // Skills
  skills: ['skills'] as const,
  skill: (id: string) => ['skills', id] as const,

  // Sessions
  sessions: (projectId?: string) =>
    projectId ? ['sessions', { projectId }] : ['sessions'] as const,
  session: (id: string) => ['sessions', id] as const,
  sessionMessages: (sessionId: string) => ['sessions', sessionId, 'messages'] as const,

  // User
  user: ['user'] as const,
  userProfile: ['user', 'profile'] as const,
  userPreferences: ['user', 'preferences'] as const,

  // Files
  files: (contextType: 'project' | 'session', contextId: string) =>
    ['files', contextType, contextId] as const,
  file: (contextType: 'project' | 'session', contextId: string, path: string) =>
    ['files', contextType, contextId, path] as const
} as const;
