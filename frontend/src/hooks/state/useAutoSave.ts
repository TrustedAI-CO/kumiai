/**
 * useAutoSave Hook
 *
 * Automatically saves data after a debounce delay when value changes
 */
import { useEffect, useRef, useCallback } from 'react';

interface UseAutoSaveOptions {
  delay?: number;
  onSave: () => Promise<void> | void;
  enabled?: boolean;
}

export function useAutoSave(
  value: string | object,
  options: UseAutoSaveOptions
) {
  const { delay = 1000, onSave, enabled = true } = options;
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const previousValueRef = useRef(value);

  // Memoize save handler
  const handleSave = useCallback(async () => {
    try {
      await onSave();
    } catch (error) {
      console.error('[useAutoSave] Save failed:', error);
    }
  }, [onSave]);

  useEffect(() => {
    // Skip if auto-save is disabled
    if (!enabled) return;

    // Skip if value hasn't changed
    const valueString = typeof value === 'string' ? value : JSON.stringify(value);
    const previousValueString = typeof previousValueRef.current === 'string'
      ? previousValueRef.current
      : JSON.stringify(previousValueRef.current);

    if (valueString === previousValueString) return;

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout
    timeoutRef.current = setTimeout(() => {
      handleSave();
      previousValueRef.current = value;
    }, delay);

    // Cleanup
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, delay, handleSave, enabled]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);
}
