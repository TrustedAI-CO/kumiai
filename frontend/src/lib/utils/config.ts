/**
 * Frontend configuration with environment variable support
 */

import { API_BASE } from '@/lib/api';

export const config = {
  // API configuration - use centralized API_BASE from api.ts
  apiUrl: API_BASE,

  // Path configuration
  // Note: These are server-side paths passed to the backend API
  // The backend will resolve them relative to its base directory
  paths: {
    // Use env vars if provided, otherwise use relative paths that the backend will resolve
    projectRoot: import.meta.env.VITE_PROJECT_ROOT || './poc-multiagent',
    skillLibrary: import.meta.env.VITE_SKILL_LIBRARY_PATH || './poc-multiagent/skill_library',
    characterLibrary: import.meta.env.VITE_CHARACTER_LIBRARY_PATH || './poc-multiagent/character_library',
  },
};

// Export individual values for convenience
export const { apiUrl, paths } = config;
