/**
 * useLocalStorage Hook
 *
 * Provides a React state interface for localStorage with:
 * - Automatic serialization/deserialization
 * - Error handling
 * - Type safety
 * - SSR compatibility
 */

import { useState, useEffect, useCallback } from 'react';

interface UseLocalStorageOptions<T> {
  /**
   * Serializer function to convert value to string
   * Default: JSON.stringify
   */
  serializer?: (value: T) => string;

  /**
   * Deserializer function to convert string to value
   * Default: JSON.parse
   */
  deserializer?: (value: string) => T;

  /**
   * Whether to sync state across tabs/windows
   * Default: true
   */
  syncAcrossTabs?: boolean;

  /**
   * Callback when storage event occurs from another tab
   */
  onStorageChange?: (newValue: T | null) => void;
}

/**
 * Hook to manage localStorage with React state
 *
 * @param key - localStorage key
 * @param initialValue - Default value if key doesn't exist
 * @param options - Configuration options
 * @returns [value, setValue, removeValue]
 *
 * @example
 * ```tsx
 * const [theme, setTheme, removeTheme] = useLocalStorage('theme', 'light');
 * const [user, setUser] = useLocalStorage<User | null>('user', null);
 * const [settings, setSettings] = useLocalStorage('settings', {}, { syncAcrossTabs: true });
 * ```
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options: UseLocalStorageOptions<T> = {}
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const {
    serializer = JSON.stringify,
    deserializer = JSON.parse,
    syncAcrossTabs = true,
    onStorageChange
  } = options;

  // Initialize state with value from localStorage or initialValue
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? deserializer(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  /**
   * Set value in both state and localStorage
   */
  const setValue = useCallback((value: T | ((prev: T) => T)) => {
    try {
      // Allow value to be a function for same API as useState
      const valueToStore = value instanceof Function ? value(storedValue) : value;

      setStoredValue(valueToStore);

      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, serializer(valueToStore));
      }
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, serializer, storedValue]);

  /**
   * Remove value from localStorage
   */
  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);

      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key);
      }
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  /**
   * Listen for changes from other tabs/windows
   */
  useEffect(() => {
    if (!syncAcrossTabs || typeof window === 'undefined') {
      return;
    }

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key !== key || e.storageArea !== window.localStorage) {
        return;
      }

      try {
        const newValue = e.newValue ? deserializer(e.newValue) : null;
        setStoredValue(newValue ?? initialValue);

        if (onStorageChange) {
          onStorageChange(newValue);
        }
      } catch (error) {
        console.warn(`Error parsing localStorage change for key "${key}":`, error);
      }
    };

    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [key, initialValue, deserializer, syncAcrossTabs, onStorageChange]);

  return [storedValue, setValue, removeValue];
}

/**
 * Hook to manage a simple string value in localStorage
 */
export function useLocalStorageString(
  key: string,
  initialValue: string = ''
): [string, (value: string | ((prev: string) => string)) => void, () => void] {
  return useLocalStorage(key, initialValue, {
    serializer: (v) => v,
    deserializer: (v) => v
  });
}

/**
 * Hook to manage a boolean value in localStorage
 */
export function useLocalStorageBoolean(
  key: string,
  initialValue: boolean = false
): [boolean, (value: boolean | ((prev: boolean) => boolean)) => void, () => void] {
  return useLocalStorage(key, initialValue, {
    serializer: (v) => String(v),
    deserializer: (v) => v === 'true'
  });
}

/**
 * Hook to manage a number value in localStorage
 */
export function useLocalStorageNumber(
  key: string,
  initialValue: number = 0
): [number, (value: number | ((prev: number) => number)) => void, () => void] {
  return useLocalStorage(key, initialValue, {
    serializer: (v) => String(v),
    deserializer: (v) => Number(v)
  });
}
