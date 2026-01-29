/**
 * Message Sender Utility
 *
 * Handles sending user messages to the enqueue endpoint.
 * Events are received via the persistent SSE connection (sessionStream).
 */

import { apiUrl } from '@/lib/api';

export interface SendMessageOptions {
  instanceId: string;
  content: string;
  onUserMessageSent: () => void;
  onError: (error: Error) => void;
}

/**
 * Enqueue a message for processing.
 * Returns immediately - events are received via persistent SSE stream.
 */
export async function sendMessage({
  instanceId,
  content,
  onUserMessageSent,
  onError,
}: SendMessageOptions): Promise<void> {
  try {
    const response = await fetch(apiUrl(`/api/v1/sessions/${instanceId}/enqueue`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: content,
        stream: true,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to enqueue message: ${response.statusText} - ${errorText}`);
    }

    // Notify that message was enqueued
    onUserMessageSent();
  } catch (err) {
    const error = err instanceof Error ? err : new Error('Failed to send message');
    onError(error);
  }
}
