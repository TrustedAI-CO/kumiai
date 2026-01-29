/**
 * Session Stream Utility
 *
 * Manages persistent SSE connection for a session with auto-reconnection.
 * One connection per session, receives all events for all messages.
 */

import type { SessionEvent } from '@/types/session';
import { handleSSEStream } from './sseStreamHandler';
import { apiUrl } from '@/lib/api';

export interface SessionStreamOptions {
  instanceId: string;
  onEvent: (event: SessionEvent) => void;
  onError: (error: Error) => void;
}

/**
 * Open persistent SSE connection for a session with auto-reconnection.
 * Returns cleanup function to close the connection.
 */
export function openSessionStream({
  instanceId,
  onEvent,
  onError,
}: SessionStreamOptions): () => void {
  let isClosed = false;
  let reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  let reconnectAttempts = 0;
  let reconnectTimeout: NodeJS.Timeout | null = null;
  let healthCheckInterval: NodeJS.Timeout | null = null;
  let lastPingTime = Date.now();

  const MAX_RECONNECT_DELAY = 30000; // Max 30 seconds
  const HEALTH_CHECK_INTERVAL = 10000; // Check every 10 seconds
  const PING_TIMEOUT = 45000; // Expect ping every 45 seconds (30s + buffer)

  function cleanup() {
    if (reader) {
      reader.cancel().catch(() => {});
      reader = null;
    }
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
    if (healthCheckInterval) {
      clearInterval(healthCheckInterval);
      healthCheckInterval = null;
    }
  }

  function scheduleReconnect() {
    if (isClosed) return;

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
    reconnectAttempts++;

    console.log(`[SessionStream] Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);

    reconnectTimeout = setTimeout(() => {
      if (!isClosed) {
        startStream();
      }
    }, delay);
  }

  function startHealthCheck() {
    // Clear existing health check
    if (healthCheckInterval) {
      clearInterval(healthCheckInterval);
    }

    // Check for keepalive pings
    healthCheckInterval = setInterval(() => {
      if (isClosed) return;

      const timeSinceLastPing = Date.now() - lastPingTime;
      if (timeSinceLastPing > PING_TIMEOUT) {
        console.warn(`[SessionStream] No keepalive ping for ${timeSinceLastPing}ms, reconnecting...`);
        cleanup();
        scheduleReconnect();
      }
    }, HEALTH_CHECK_INTERVAL);
  }

  async function startStream() {
    cleanup();
    lastPingTime = Date.now();

    try {
      const response = await fetch(apiUrl(`/api/v1/sessions/${instanceId}/stream`), {
        method: 'GET',
        headers: {
          Accept: 'text/event-stream',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to open stream: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      reader = response.body.getReader();

      // Reset reconnect attempts on successful connection
      reconnectAttempts = 0;
      console.log('[SessionStream] Connected');

      // Start health monitoring
      startHealthCheck();

      // Wrap onEvent to detect keepalive pings
      const wrappedOnEvent = (event: SessionEvent) => {
        // Update ping time for any event (keepalive or regular)
        lastPingTime = Date.now();

        // Don't forward keepalive pings to the app
        if (event.type === 'keepalive') {
          return;
        }

        onEvent(event);
      };

      // Handle the SSE stream
      await handleSSEStream({
        reader,
        onEvent: wrappedOnEvent,
        onComplete: () => {
          console.log('[SessionStream] Stream completed, reconnecting...');
          if (!isClosed) {
            scheduleReconnect();
          }
        },
        onError: (err) => {
          console.error('[SessionStream] Stream error:', err);
          if (!isClosed) {
            onError(err);
            scheduleReconnect();
          }
        },
      });
    } catch (err) {
      if (!isClosed) {
        const error = err instanceof Error ? err : new Error('Stream failed');
        console.error('[SessionStream] Connection error:', error);
        onError(error);
        scheduleReconnect();
      }
    }
  }

  // Start the stream
  startStream();

  // Return cleanup function
  return () => {
    isClosed = true;
    cleanup();
  };
}
