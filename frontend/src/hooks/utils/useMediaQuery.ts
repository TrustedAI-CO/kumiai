/**
 * useMediaQuery Hook
 *
 * Reactive hook for media queries that updates when window resizes.
 * Replaces window.matchMedia() calls that don't react to changes.
 *
 * @param query - Media query string (e.g., '(min-width: 768px)')
 * @returns boolean - Whether the media query matches
 *
 * @example
 * const isMobile = useMediaQuery('(max-width: 1023px)');
 * const isDesktop = useMediaQuery('(min-width: 1024px)');
 * const isTablet = useMediaQuery('(min-width: 768px) and (max-width: 1023px)');
 */
import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState<boolean>(() => {
    // Initialize with current match state (SSR-safe)
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    // Skip if window is not available (SSR)
    if (typeof window === 'undefined') {
      return;
    }

    const mediaQuery = window.matchMedia(query);

    // Update state immediately in case it changed since initial render
    setMatches(mediaQuery.matches);

    // Listen for changes
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Modern browsers
    mediaQuery.addEventListener('change', handleChange);

    // Cleanup
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [query]);

  return matches;
}

/**
 * Common breakpoint hooks for convenience
 */
export function useIsMobile(): boolean {
  return useMediaQuery('(max-width: 1023px)');
}

export function useIsTablet(): boolean {
  return useMediaQuery('(min-width: 768px) and (max-width: 1023px)');
}

export function useIsDesktop(): boolean {
  return useMediaQuery('(min-width: 1024px)');
}
