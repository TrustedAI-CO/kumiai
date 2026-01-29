/**
 * User Store - Manages user profile and preferences
 *
 * Replaces UserContext with Zustand for better performance and DevTools support
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface UserProfile {
  avatar: string;
  description?: string;
  preferences?: Record<string, any>;
}

interface UserState {
  // State
  profile: UserProfile | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setProfile: (profile: UserProfile | null) => void;
  updateProfile: (updates: Partial<UserProfile>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearUser: () => void;
}

/**
 * User store with DevTools support
 */
export const useUserStore = create<UserState>()(
  devtools(
    (set) => ({
      // Initial state
      profile: null,
      isLoading: false,
      error: null,

      // Actions
      setProfile: (profile) =>
        set({ profile, error: null }, false, 'setProfile'),

      updateProfile: (updates) =>
        set(
          (state) => ({
            profile: state.profile
              ? { ...state.profile, ...updates }
              : null
          }),
          false,
          'updateProfile'
        ),

      setLoading: (isLoading) =>
        set({ isLoading }, false, 'setLoading'),

      setError: (error) =>
        set({ error }, false, 'setError'),

      clearUser: () =>
        set(
          { profile: null, isLoading: false, error: null },
          false,
          'clearUser'
        )
    }),
    {
      name: 'UserStore',
      enabled: import.meta.env.DEV // Only enable DevTools in development
    }
  )
);
