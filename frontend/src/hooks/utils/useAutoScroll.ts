/**
 * useAutoScroll hook
 *
 * Manages auto-scrolling behavior for chat messages.
 * - Initial load: scroll to bottom instantly
 * - User sends message: always scroll to bottom
 * - New messages arrive: only scroll if user already near bottom
 *
 * Uses ResizeObserver to detect content size changes and RAF for proper timing
 */

import { useEffect, useRef, useCallback } from 'react';

interface UseAutoScrollOptions {
  messages: any[];
  enabled?: boolean;
}

export function useAutoScroll({ messages, enabled = true }: UseAutoScrollOptions) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isInitialLoad = useRef(true);
  const rafIdRef = useRef<number | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);

  const performScroll = useCallback((behavior: ScrollBehavior) => {
    // Cancel any pending RAF
    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
    }

    // Schedule scroll after layout is complete
    rafIdRef.current = requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ behavior });
      rafIdRef.current = null;
    });
  }, []);

  const checkAndScroll = useCallback(() => {
    if (!enabled) return;

    const container = messagesContainerRef.current;
    if (!container) return;

    // Check if user is scrolled near bottom (within 200px threshold)
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 200;

    if (isInitialLoad.current && messages.length > 0) {
      // Initial load: always scroll instantly
      performScroll('instant');
      isInitialLoad.current = false;
    } else if (isNearBottom && messages.length > 0) {
      // User is at bottom: smooth scroll
      performScroll('smooth');
    }
  }, [messages, enabled, performScroll]);

  // Watch for message changes
  useEffect(() => {
    checkAndScroll();
  }, [checkAndScroll]);

  // Watch for container size changes (content expansion during streaming)
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container || !enabled) return;

    // Create ResizeObserver to detect content size changes
    resizeObserverRef.current = new ResizeObserver(() => {
      checkAndScroll();
    });

    resizeObserverRef.current.observe(container);

    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
        resizeObserverRef.current = null;
      }
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    };
  }, [enabled, checkAndScroll]);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    performScroll(behavior);
  }, [performScroll]);

  return {
    messagesEndRef,
    messagesContainerRef,
    scrollToBottom,
  };
}
