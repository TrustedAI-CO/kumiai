/**
 * SSE Stream Handler
 *
 * Utility to parse Server-Sent Events stream and emit typed events.
 */

import type { SessionEvent } from '@/types/session';

export interface SSEStreamHandlerOptions {
  reader: ReadableStreamDefaultReader<Uint8Array>;
  onEvent: (event: SessionEvent) => void;
  onComplete: () => void;
  onError: (error: Error) => void;
}

/**
 * Parse and handle SSE stream from backend
 */
export async function handleSSEStream({
  reader,
  onEvent,
  onComplete,
  onError,
}: SSEStreamHandlerOptions): Promise<void> {
  const decoder = new TextDecoder();
  let currentEventType = '';
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        console.log('[SSE] Stream complete');
        onComplete();
        break;
      }

      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEventType = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          const data = line.slice(5).trim();

          if (data) {
            try {
              const eventData = JSON.parse(data);

              // Handle keepalive pings (event type "ping" from backend)
              if (currentEventType === 'ping' || eventData.type === 'keepalive') {
                onEvent({ type: 'keepalive' } as SessionEvent);
              } else {
                const event: SessionEvent = {
                  type: currentEventType as any,
                  ...eventData,
                };
                onEvent(event);
              }
            } catch (parseError) {
              console.error('[SSE] Failed to parse event data:', data, parseError);
            }
          }

          // Reset event type after processing
          currentEventType = '';
        }
      }
    }
  } catch (err) {
    console.error('[SSE] Stream error:', err);
    onError(err instanceof Error ? err : new Error('Stream error'));
  } finally {
    reader.releaseLock();
  }
}
