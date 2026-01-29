/**
 * useLocalStorageState Hook
 *
 * Persists state in localStorage with automatic sync
 * Consolidates duplicate localStorage patterns from Skills.tsx and Agents.tsx
 */
import { useState, useEffect, Dispatch, SetStateAction } from 'react';

export function useLocalStorageState<T>(
  key: string,
  defaultValue: T
): [T, Dispatch<SetStateAction<T>>] {
  // Initialize state from localStorage
  const [state, setState] = useState<T>(() => {
    try {
      const saved = localStorage.getItem(key);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (error) {
      console.error(`Error reading from localStorage key "${key}":`, error);
    }
    return defaultValue;
  });

  // Sync state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(state));
    } catch (error) {
      console.error(`Error writing to localStorage key "${key}":`, error);
    }
  }, [key, state]);

  return [state, setState];
}

/**
 * Specialized hook for boolean localStorage state
 */
export function useLocalStorageBool(
  key: string,
  defaultValue: boolean = false
): [boolean, Dispatch<SetStateAction<boolean>>] {
  return useLocalStorageState<boolean>(key, defaultValue);
}
