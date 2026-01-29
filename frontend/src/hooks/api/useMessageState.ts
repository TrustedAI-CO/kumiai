/**
 * useMessageState hook
 *
 * Manages three separate message states:
 * 1. Persisted messages from DB
 * 2. Optimistic user message (temporary, shown immediately)
 * 3. Streaming assistant message (temporary, built during stream)
 */

import { useState, useCallback } from 'react';
import type { SessionMessage } from '@/types/session';

export interface OptimisticUserMessage {
  content: string;
  timestamp: string;
}

export interface StreamingAssistantMessage {
  content: string;
  timestamp: string;
}

export interface MessageState {
  // Optimistic user message (shown immediately when user sends)
  optimisticUserMessage: OptimisticUserMessage | null;

  // Streaming assistant message (built during stream)
  streamingAssistantMessage: StreamingAssistantMessage | null;
}

export interface MessageStateActions {
  setOptimisticUserMessage: (content: string) => void;
  clearOptimisticUserMessage: () => void;

  startStreamingAssistant: () => void;
  appendToStreamingAssistant: (content: string) => void;
  clearStreamingAssistant: () => void;

  clearAllOptimistic: () => void;
}

export function useMessageState(): [MessageState, MessageStateActions] {
  const [optimisticUserMessage, setOptimisticUserMessage] = useState<OptimisticUserMessage | null>(null);
  const [streamingAssistantMessage, setStreamingAssistantMessage] = useState<StreamingAssistantMessage | null>(null);

  const actions: MessageStateActions = {
    setOptimisticUserMessage: useCallback((content: string) => {
      setOptimisticUserMessage({
        content,
        timestamp: new Date().toISOString(),
      });
    }, []),

    clearOptimisticUserMessage: useCallback(() => {
      setOptimisticUserMessage(null);
    }, []),

    startStreamingAssistant: useCallback(() => {
      setStreamingAssistantMessage({
        content: '',
        timestamp: new Date().toISOString(),
      });
    }, []),

    appendToStreamingAssistant: useCallback((content: string) => {
      setStreamingAssistantMessage((prev) => {
        if (!prev) {
          // Start new streaming message if none exists
          return {
            content,
            timestamp: new Date().toISOString(),
          };
        }

        // Append to existing
        return {
          ...prev,
          content: prev.content + content,
        };
      });
    }, []),

    clearStreamingAssistant: useCallback(() => {
      setStreamingAssistantMessage(null);
    }, []),

    clearAllOptimistic: useCallback(() => {
      setOptimisticUserMessage(null);
      setStreamingAssistantMessage(null);
    }, []),
  };

  return [
    {
      optimisticUserMessage,
      streamingAssistantMessage,
    },
    actions,
  ];
}
