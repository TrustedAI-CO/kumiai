/**
 * useSessionMessages hook
 *
 * Manages persisted message history from database.
 * Does NOT handle optimistic updates or streaming - those are handled in the component.
 */

import { useEffect, useState, useCallback } from 'react';
import type { SessionMessage, SessionRole, SessionEvent } from '@/types/session';
import { filterMessagesByRole } from '@/types/session';
import { apiUrl } from '@/lib/api';

interface UseSessionMessagesOptions {
  instanceId: string;
  role: SessionRole;
  autoLoad?: boolean;
}

interface UseSessionMessagesReturn {
  messages: SessionMessage[];
  filteredMessages: SessionMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessageRequest: (content: string) => Promise<ReadableStreamDefaultReader<Uint8Array>>;
  loadMessages: () => Promise<void>;
  clearMessages: () => void;
}

export function useSessionMessages({
  instanceId,
  role,
  autoLoad = true,
}: UseSessionMessagesOptions): UseSessionMessagesReturn {
  const [messages, setMessages] = useState<SessionMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load messages from database
   */
  const loadMessages = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const url = apiUrl(`/api/v1/sessions/${instanceId}/messages?limit=100`);
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to load messages: ${response.statusText}`);
      }

      const data = await response.json();
      // Backend returns paginated result - extract items array
      setMessages(data.items || data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load messages';
      setError(errorMessage);
      console.error('[useSessionMessages] Error loading messages:', err);
    } finally {
      setIsLoading(false);
    }
  }, [instanceId]);

  /**
   * Send message and return SSE stream reader
   * Does NOT handle optimistic UI - caller is responsible for that
   */
  const sendMessageRequest = useCallback(
    async (content: string): Promise<ReadableStreamDefaultReader<Uint8Array>> => {
      setError(null);

      try {
        const response = await fetch(apiUrl(`/api/v1/sessions/${instanceId}/query`), {
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
          throw new Error(`Failed to send message: ${response.statusText}`);
        }

        if (!response.body) {
          throw new Error('Response body is null');
        }

        // Return the stream reader - caller will handle SSE parsing
        return response.body.getReader();
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);
        console.error('[useSessionMessages] Error sending message:', err);
        throw err;
      }
    },
    [instanceId]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Auto-load messages on mount if enabled
  useEffect(() => {
    if (autoLoad) {
      loadMessages();
    }
  }, [autoLoad, loadMessages]);

  // Filter messages based on role
  const filteredMessages = filterMessagesByRole(messages, role);

  return {
    messages,
    filteredMessages,
    isLoading,
    error,
    sendMessageRequest,
    loadMessages,
    clearMessages,
  };
}
