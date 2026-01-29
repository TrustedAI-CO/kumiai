/**
 * useSessionStream hook
 *
 * Manages SSE connection for session streaming and normalizes events.
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import type {
  SessionEvent,
  SessionRole,
  SessionStatus,
} from '@/types/session';
import { apiUrl } from '@/lib/api';

interface UseSessionStreamOptions {
  instanceId: string;
  role: SessionRole;
  onEvent?: (event: SessionEvent) => void;
  autoConnect?: boolean;
}

interface UseSessionStreamReturn {
  events: SessionEvent[];
  status: SessionStatus;
  isConnected: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
  clearEvents: () => void;
}

export function useSessionStream({
  instanceId,
  role,
  onEvent,
  autoConnect = true,
}: UseSessionStreamOptions): UseSessionStreamReturn {
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [status, setStatus] = useState<SessionStatus>('idle');
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const eventsBufferRef = useRef<SessionEvent[]>([]);
  const batchTimeoutRef = useRef<NodeJS.Timeout>();

  // Event reordering state
  const eventReorderBufferRef = useRef<Map<number, SessionEvent>>(new Map());
  const nextExpectedSequenceRef = useRef<number>(1);
  const reorderTimeoutRef = useRef<NodeJS.Timeout>();
  const REORDER_TIMEOUT_MS = 5000; // Wait up to 5s for missing events (increased for queued reminders)

  // Use ref to always call the latest onEvent callback without triggering reconnections
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  // Fetch initial status on mount to avoid showing stale "idle" state
  // NOTE: Disabled because /status endpoint doesn't exist in new backend
  useEffect(() => {
    /* DISABLED - /status endpoint doesn't exist
    const fetchInitialStatus = async () => {
      try {
        const response = await fetch(`/api/v1/sessions/${instanceId}/status`);
        if (response.ok) {
          const data = await response.json();
          setStatus(data.status);
          console.log(`[useSessionStream] Initial status: ${data.status} (source: ${data.source})`);
        } else {
          console.warn(`[useSessionStream] Failed to fetch initial status: ${response.statusText}`);
          // Keep default 'idle' status
        }
      } catch (error) {
        console.error('[useSessionStream] Error fetching initial status:', error);
        // Keep default 'idle' status
      }
    };

    if (instanceId) {
      fetchInitialStatus();
    }
    */
  }, [instanceId]);

  // Process events in sequence order from reorder buffer
  const processReorderedEvents = useCallback(() => {
    const processedEvents: SessionEvent[] = [];

    // Process all consecutive events starting from nextExpectedSequence
    while (true) {
      const event = eventReorderBufferRef.current.get(nextExpectedSequenceRef.current);
      if (!event) break; // No more consecutive events

      // Remove from buffer and process
      eventReorderBufferRef.current.delete(nextExpectedSequenceRef.current);
      nextExpectedSequenceRef.current++;

      // Call event handler
      if (onEventRef.current) {
        onEventRef.current(event);
      }

      // Add to processed events for batching
      processedEvents.push(event);
    }

    // Add processed events to buffer for batched state update
    if (processedEvents.length > 0) {
      eventsBufferRef.current.push(...processedEvents);
    }

    return processedEvents.length;
  }, []);

  // Force flush reorder buffer after timeout (for missing events)
  const flushReorderBuffer = useCallback(() => {
    console.warn(
      `[useSessionStream] Flushing ${eventReorderBufferRef.current.size} buffered events after timeout. ` +
      `Expected sequence: ${nextExpectedSequenceRef.current}, buffered sequences: ${Array.from(eventReorderBufferRef.current.keys()).sort((a, b) => a - b).join(', ')}`
    );

    // Process all buffered events in sequence order, skipping gaps
    const sortedSequences = Array.from(eventReorderBufferRef.current.keys()).sort((a, b) => a - b);

    for (const seq of sortedSequences) {
      const event = eventReorderBufferRef.current.get(seq)!;
      eventReorderBufferRef.current.delete(seq);

      // Call event handler
      if (onEventRef.current) {
        onEventRef.current(event);
      }

      eventsBufferRef.current.push(event);
    }

    // Update next expected sequence to be after the last flushed event
    if (sortedSequences.length > 0) {
      nextExpectedSequenceRef.current = sortedSequences[sortedSequences.length - 1] + 1;
    }
  }, []);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      return;
    }

    // NOTE: The /stream endpoint doesn't exist in the new backend architecture.
    // SSE streaming is now handled directly by the /query endpoint when sending messages.
    // This hook is kept for backward compatibility but doesn't establish a connection.
    console.warn('[useSessionStream] Stream endpoint not available in new backend. SSE handled by /query endpoint.');

    /* OLD IMPLEMENTATION - DISABLED
    const eventSource = new EventSource(apiUrl(`/api/v1/sessions/${instanceId}/stream`));

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as SessionEvent;

        // Update status immediately for status_change events (don't batch these)
        if (data.type === 'status_change') {
          setStatus((data as any).status);

          // Warn if status not persisted to DB (indicates DB congestion)
          if ((data as any).db_persisted === false) {
            console.warn(
              `[useSessionStream] ⚠️ Status change to '${(data as any).status}' not persisted to database. ` +
              `DB may be congested. Status updates via SSE only.`
            );
            // Could show toast notification to user here if needed
          }
        }

        // Handle events with sequence numbers (reorder if needed)
        if ((data as any).sequence !== undefined) {
          const sequence = (data as any).sequence as number;

          // Check if this is the next expected event
          if (sequence === nextExpectedSequenceRef.current) {
            // Process this event immediately
            nextExpectedSequenceRef.current++;

            if (onEventRef.current) {
              onEventRef.current(data);
            }

            eventsBufferRef.current.push(data);

            // Try to process any buffered events that are now in sequence
            processReorderedEvents();

            // Clear reorder timeout if buffer is empty
            if (eventReorderBufferRef.current.size === 0) {
              clearTimeout(reorderTimeoutRef.current);
            }
          } else if (sequence > nextExpectedSequenceRef.current) {
            // Future event, buffer it for later
            const gap = sequence - nextExpectedSequenceRef.current;

            // Warn about large gaps (potential issue)
            if (gap > 5) {
              console.warn(
                `[useSessionStream] Large sequence gap detected! seq=${sequence}, expected=${nextExpectedSequenceRef.current}, gap=${gap}. ` +
                `This may indicate dropped events or concurrent query execution.`
              );
            } else {
              console.log(
                `[useSessionStream] Buffering out-of-order event (seq=${sequence}, expected=${nextExpectedSequenceRef.current}, gap=${gap})`
              );
            }

            eventReorderBufferRef.current.set(sequence, data);

            // Set timeout to flush buffer if we don't receive missing events
            clearTimeout(reorderTimeoutRef.current);
            reorderTimeoutRef.current = setTimeout(() => {
              flushReorderBuffer();
            }, REORDER_TIMEOUT_MS);
          } else {
            // Old event (already processed), likely a duplicate - skip it
            console.log(
              `[useSessionStream] Skipping old/duplicate event (seq=${sequence}, expected=${nextExpectedSequenceRef.current})`
            );
          }
        } else {
          // Event without sequence number - process immediately (legacy support)
          if (onEventRef.current) {
            onEventRef.current(data);
          }

          eventsBufferRef.current.push(data);
        }

        // Clear existing timeout and schedule new batch update
        clearTimeout(batchTimeoutRef.current);
        batchTimeoutRef.current = setTimeout(() => {
          if (eventsBufferRef.current.length > 0) {
            setEvents((prev) => [...prev, ...eventsBufferRef.current]);
            eventsBufferRef.current = [];
          }
        }, 100); // Batch updates every 100ms
      } catch (err) {
        console.error('[useSessionStream] Failed to parse event:', err, 'Raw data:', event.data);

        // Emit synthetic error event to notify parent component
        const errorEvent: SessionEvent = {
          type: 'error',
          error: `Failed to parse stream event: ${err instanceof Error ? err.message : String(err)}`,
        };

        // Add error event immediately (don't batch errors)
        setEvents((prev) => [...prev, errorEvent]);

        // Notify parent component of parse error
        if (onEventRef.current) {
          onEventRef.current(errorEvent);
        }

        // Set error state to show in UI
        setError('Received malformed data from server');
      }
    };

    eventSource.onerror = (err) => {
      console.error(`[useSessionStream] Connection error:`, err);
      setError('Connection lost');
      setIsConnected(false);

      // Close and cleanup
      eventSource.close();
      eventSourceRef.current = null;
    };

    eventSourceRef.current = eventSource;
    */
  }, [instanceId]); // Only reconnect when instanceId changes

  const disconnect = useCallback(() => {
    // Clear any pending timeouts
    clearTimeout(batchTimeoutRef.current);
    clearTimeout(reorderTimeoutRef.current);

    // Flush any remaining buffered events in order
    if (eventReorderBufferRef.current.size > 0) {
      flushReorderBuffer();
    }

    // Flush any remaining batched events
    if (eventsBufferRef.current.length > 0) {
      setEvents((prev) => [...prev, ...eventsBufferRef.current]);
      eventsBufferRef.current = [];
    }

    // Reset sequence tracking
    nextExpectedSequenceRef.current = 1;
    eventReorderBufferRef.current.clear();

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, [flushReorderBuffer]);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    events,
    status,
    isConnected,
    error,
    connect,
    disconnect,
    clearEvents,
  };
}
