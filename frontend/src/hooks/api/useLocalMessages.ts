/**
 * useLocalMessages hook
 *
 * Manages local message state built from streaming.
 * - On init: Load messages from DB once
 * - During session: Append messages from stream to local state
 * - On reload: Fresh DB load
 *
 * This approach eliminates flickering by never reloading DB during streaming.
 */

import { useState, useCallback } from 'react';
import type { SessionMessage } from '@/types/session';
import { apiUrl } from '@/lib/api';

export interface LocalMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool' | 'system';
  content: string;
  timestamp: string;
  agent_id?: string;
  agent_name?: string;
  from_instance_id?: string; // Session ID where message originated (for cross-session routing)
  tool_name?: string;
  tool_args?: any;
  tool_id?: string;
  tool_result?: string; // Tool execution result
  tool_error?: boolean; // Whether the tool execution failed
  isStreaming?: boolean;
  response_id?: string; // UUID shared by all blocks in same response
}

export interface UseLocalMessagesReturn {
  messages: LocalMessage[];
  isLoading: boolean;
  error: string | null;
  hasMore: boolean; // Whether there are more messages to load
  isLoadingMore: boolean; // Whether currently loading older messages

  // Append a user message (optimistic)
  addUserMessage: (content: string) => void;

  // Add incoming cross-session user message
  addIncomingUserMessage: (messageId: string, content: string, agentId?: string, agentName?: string, fromInstanceId?: string, timestamp?: string) => void;

  // Start streaming assistant message
  startAssistantMessage: (agentId?: string, agentName?: string, responseId?: string) => void;

  // Append content to streaming message
  appendToAssistant: (content: string) => void;

  // Complete streaming message (mark as non-streaming)
  completeAssistantMessage: () => void;

  // Add tool use message
  addToolUse: (toolUseId: string, toolName: string, toolInput: any, responseId?: string, agentId?: string, agentName?: string) => void;

  // Add tool complete message (or update existing tool message)
  addToolComplete: (toolUseId: string, result?: string, isError?: boolean) => void;

  // Load messages from DB (used only on init)
  loadFromDB: (sessionId: string) => Promise<void>;

  // Load older messages (for infinite scroll)
  loadMoreMessages: (sessionId: string) => Promise<void>;

  // Clear all messages
  clearMessages: () => void;
}

export function useLocalMessages(): UseLocalMessagesReturn {
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true); // Assume more messages until we know otherwise
  const [cursor, setCursor] = useState<string | null>(null); // Track pagination cursor

  const addUserMessage = useCallback((content: string) => {
    const userMessage: LocalMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
  }, []);

  const addIncomingUserMessage = useCallback((
    messageId: string,
    content: string,
    agentId?: string,
    agentName?: string,
    fromInstanceId?: string,
    timestamp?: string
  ) => {
    const userMessage: LocalMessage = {
      id: messageId,
      role: 'user',
      content,
      timestamp: timestamp || new Date().toISOString(),
      agent_id: agentId,
      agent_name: agentName,
      from_instance_id: fromInstanceId,
    };
    setMessages(prev => [...prev, userMessage]);
  }, []);

  const startAssistantMessage = useCallback((agentId?: string, agentName?: string, responseId?: string) => {
    const assistantMessage: LocalMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      agent_id: agentId,
      agent_name: agentName,
      isStreaming: true,
      response_id: responseId,
    };
    setMessages(prev => [...prev, assistantMessage]);
  }, []);

  const appendToAssistant = useCallback((content: string) => {
    setMessages(prev => {
      const updated = [...prev];

      // Find the most recent streaming assistant message
      const lastStreaming = updated.findLast(m =>
        m.role === 'assistant' && m.isStreaming
      );

      if (lastStreaming) {
        // Append to existing streaming message
        lastStreaming.content += content;
      } else {
        // No streaming message exists - this indicates a bug in the flow
        console.warn('[useLocalMessages] No streaming assistant message to append to!');
        console.warn('[useLocalMessages] Content:', content.slice(0, 100));
        // Don't auto-create - let the bug surface
      }

      return updated;
    });
  }, []);

  const completeAssistantMessage = useCallback(() => {
    setMessages(prev => {
      const updated = [...prev];

      // Find the LAST streaming assistant message (not just last message)
      const lastStreamingAssistant = updated.findLast(m =>
        m.role === 'assistant' && m.isStreaming
      );

      if (lastStreamingAssistant) {
        lastStreamingAssistant.isStreaming = false;
        console.log('[useLocalMessages] Completed streaming assistant message');
      } else {
        console.log('[useLocalMessages] No streaming assistant message to complete');
      }

      return updated;
    });
  }, []);

  const addToolUse = useCallback((toolUseId: string, toolName: string, toolInput: any, responseId?: string, agentId?: string, agentName?: string) => {
    const toolMessage: LocalMessage = {
      id: toolUseId,
      role: 'tool',
      content: '',
      timestamp: new Date().toISOString(),
      tool_name: toolName,
      tool_args: toolInput,
      tool_id: toolUseId,
      isStreaming: false,
      response_id: responseId,
      agent_id: agentId,
      agent_name: agentName,
    };
    setMessages(prev => [...prev, toolMessage]);
  }, []);

  const addToolComplete = useCallback((toolUseId: string, result?: string, isError?: boolean) => {
    // Update the tool message with the result
    setMessages(prev => {
      const updated = [...prev];
      const toolMessage = updated.find(m => m.tool_id === toolUseId);

      if (toolMessage) {
        toolMessage.tool_result = result;
        toolMessage.tool_error = isError;
        console.log('[useLocalMessages] Tool complete:', toolUseId, 'has result:', !!result);
      } else {
        console.warn('[useLocalMessages] Tool message not found for:', toolUseId);
      }

      return updated;
    });
  }, []);

  const loadFromDB = useCallback(async (sessionId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(apiUrl(`/api/v1/sessions/${sessionId}/messages?limit=50`));

      if (!response.ok) {
        throw new Error(`Failed to load messages: ${response.statusText}`);
      }

      const responseData = await response.json();
      // Backend now returns paginated result - extract items array and cursor
      const data: SessionMessage[] = responseData.items || responseData;
      const nextCursor: string | null = responseData.next_cursor || null;

      // Convert SessionMessage to LocalMessage
      const localMessages: LocalMessage[] = data.map(msg => ({
        id: msg.id || msg.timestamp,
        role: msg.role as 'user' | 'assistant' | 'tool' | 'system',
        content: msg.content,
        timestamp: msg.timestamp,
        agent_id: msg.agent_id,
        agent_name: msg.agent_name,
        from_instance_id: msg.from_instance_id, // Cross-session message source
        tool_name: msg.tool_name,
        tool_args: msg.tool_args,
        tool_id: Array.isArray(msg.tool_args) ? msg.tool_args?.[0]?.id : undefined,
        tool_result: msg.tool_result,
        tool_error: msg.tool_error,
        isStreaming: false,
        response_id: msg.response_id, // Preserve response_id for grouping
      }));

      setMessages(localMessages);
      setCursor(nextCursor);
      setHasMore(!!nextCursor); // Has more if there's a next cursor
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load messages';
      setError(errorMessage);
      console.error('[useLocalMessages] Error loading from DB:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadMoreMessages = useCallback(async (sessionId: string) => {
    // Don't load if already loading or no more messages
    if (isLoadingMore || !hasMore || !cursor) {
      return;
    }

    setIsLoadingMore(true);
    setError(null);

    try {
      const response = await fetch(apiUrl(`/api/v1/sessions/${sessionId}/messages?limit=50&cursor=${encodeURIComponent(cursor)}`));

      if (!response.ok) {
        throw new Error(`Failed to load more messages: ${response.statusText}`);
      }

      const responseData = await response.json();
      const data: SessionMessage[] = responseData.items || responseData;
      const nextCursor: string | null = responseData.next_cursor || null;

      // Convert SessionMessage to LocalMessage
      const olderMessages: LocalMessage[] = data.map(msg => ({
        id: msg.id || msg.timestamp,
        role: msg.role as 'user' | 'assistant' | 'tool' | 'system',
        content: msg.content,
        timestamp: msg.timestamp,
        agent_id: msg.agent_id,
        agent_name: msg.agent_name,
        from_instance_id: msg.from_instance_id,
        tool_name: msg.tool_name,
        tool_args: msg.tool_args,
        tool_id: Array.isArray(msg.tool_args) ? msg.tool_args?.[0]?.id : undefined,
        tool_result: msg.tool_result,
        tool_error: msg.tool_error,
        isStreaming: false,
        response_id: msg.response_id,
      }));

      // Prepend older messages to the beginning
      setMessages(prev => [...olderMessages, ...prev]);
      setCursor(nextCursor);
      setHasMore(!!nextCursor);

      console.log(`[useLocalMessages] Loaded ${olderMessages.length} older messages, hasMore: ${!!nextCursor}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load more messages';
      setError(errorMessage);
      console.error('[useLocalMessages] Error loading more messages:', err);
    } finally {
      setIsLoadingMore(false);
    }
  }, [cursor, hasMore, isLoadingMore]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setCursor(null);
    setHasMore(true);
  }, []);

  return {
    messages,
    isLoading,
    isLoadingMore,
    hasMore,
    error,
    addUserMessage,
    addIncomingUserMessage,
    startAssistantMessage,
    appendToAssistant,
    completeAssistantMessage,
    addToolUse,
    addToolComplete,
    loadFromDB,
    loadMoreMessages,
    clearMessages,
  };
}
