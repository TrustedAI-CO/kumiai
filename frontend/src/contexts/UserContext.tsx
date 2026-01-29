/**
 * UserContext - Global user profile state
 *
 * Provides user profile information (avatar, description, preferences) across the app.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, UserProfile } from '@/lib/api';

interface UserContextValue {
  profile: UserProfile | null;
  isLoading: boolean;
  error: string | null;
  refreshProfile: () => Promise<void>;
}

const UserContext = createContext<UserContextValue | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProfile = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const userProfile = await api.getUserProfile();
      setProfile(userProfile);
    } catch (err) {
      console.error('[UserContext] Failed to load profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to load user profile');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const value: UserContextValue = {
    profile,
    isLoading,
    error,
    refreshProfile: loadProfile,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
