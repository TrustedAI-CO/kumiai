/**
 * useStreamHandler hook
 *
 * Handles SSE stream events from the backend.
 */

import { useCallback, useRef } from 'react';
import type { SessionEvent, ContentBlockEvent, AutoSaveEvent, UserNotificationEvent, UserMessageEvent, QueueStatusEvent, QueuedMessagePreview, ToolUseEvent, ToolCompleteEvent } from '@/types/session';
import { desktopNotifications } from '@/lib/utils';

interface UseStreamHandlerOptions {
  appendToAssistant: (content: string) => void;
  completeAssistantMessage: () => void;
  startAssistantMessage: (agentId?: string, agentName?: string, responseId?: string) => void;
  addIncomingUserMessage: (messageId: string, content: string, agentId?: string, agentName?: string, fromInstanceId?: string, timestamp?: string) => void;
  addToolUse: (toolUseId: string, toolName: string, toolInput: any, responseId?: string, agentId?: string, agentName?: string) => void;
  addToolComplete: (toolUseId: string, result?: string, isError?: boolean) => void;
  onAutoSave?: (type: 'skill' | 'agent', id: string) => void;
  setIsSending: (isSending: boolean) => void;
  setError: (error: string | null) => void;
  setQueueSize: (size: number) => void;
  setQueuedMessages: (messages: QueuedMessagePreview[]) => void;
  loadFromDB: (instanceId: string) => Promise<void>;
  instanceId: string;
}

export function useStreamHandler({
  appendToAssistant,
  completeAssistantMessage,
  startAssistantMessage,
  addIncomingUserMessage,
  addToolUse,
  addToolComplete,
  onAutoSave,
  setIsSending,
  setError,
  setQueueSize,
  setQueuedMessages,
  loadFromDB,
  instanceId,
}: UseStreamHandlerOptions) {
  // Track the current response_id being streamed (null when not streaming)
  const currentResponseIdRef = useRef<string | null>(null);

  // Track processed event IDs to prevent duplicates
  const processedEventIdsRef = useRef<Set<string>>(new Set());

  const handleStreamEvent = useCallback(
    (event: SessionEvent) => {
      console.log('[Chat] Stream event:', event.type);

      // Check for duplicate events (SSE can send duplicates during reconnection)
      const eventId = (event as any).event_id;
      if (eventId && processedEventIdsRef.current.has(eventId)) {
        console.log('[Chat] Skipping duplicate event:', eventId);
        return;
      }
      if (eventId) {
        processedEventIdsRef.current.add(eventId);
      }

      switch (event.type) {
        case 'user_message':
          const userMsgEvent = event as UserMessageEvent;
          console.log('[Chat] User message received:', userMsgEvent.message_id);
          addIncomingUserMessage(
            userMsgEvent.message_id,
            userMsgEvent.content,
            userMsgEvent.agent_id,
            userMsgEvent.agent_name,
            userMsgEvent.from_instance_id,
            userMsgEvent.timestamp
          );
          break;

        case 'content_block':
          const blockEvent = event as ContentBlockEvent;
          if (blockEvent.block_type === 'text') {
            // Each content_block is a complete text block (not a delta)
            // Create a new message for each block - they'll be grouped by response_id in UI

            // Complete any previous streaming message from the same response
            if (currentResponseIdRef.current === blockEvent.response_id) {
              completeAssistantMessage();
            }

            // Start new assistant message for this content block
            startAssistantMessage(blockEvent.agent_id, blockEvent.agent_name, blockEvent.response_id);
            // Append the content
            appendToAssistant(blockEvent.content);
            // Complete immediately (content_block is complete, not streaming)
            completeAssistantMessage();

            // Track the response_id
            currentResponseIdRef.current = blockEvent.response_id || null;
          }
          break;

        case 'message_complete':
          console.log('[Chat] Message complete - conversation done');
          // Complete the assistant message bubble
          if (currentResponseIdRef.current !== null) {
            completeAssistantMessage();
            currentResponseIdRef.current = null;
          }
          setIsSending(false);
          break;

        case 'tool_use':
          const toolUseEvent = event as ToolUseEvent;
          console.log('[Chat] Tool use:', toolUseEvent.tool_name);
          addToolUse(toolUseEvent.tool_use_id, toolUseEvent.tool_name, toolUseEvent.tool_input, toolUseEvent.response_id, toolUseEvent.agent_id, toolUseEvent.agent_name);
          break;

        case 'tool_complete':
          const toolCompleteEvent = event as ToolCompleteEvent;
          console.log('[Chat] Tool complete:', toolCompleteEvent.tool_use_id, 'result:', toolCompleteEvent.result?.substring(0, 100));
          addToolComplete(toolCompleteEvent.tool_use_id, toolCompleteEvent.result, toolCompleteEvent.is_error);

          // Reload messages from database to get persisted tool message
          // This ensures tool messages saved by backend are displayed
          loadFromDB(instanceId).catch((err) => {
            console.error('[Chat] Failed to reload messages after tool_complete:', err);
          });
          break;

        case 'auto_save':
          const autoSaveEvent = event as AutoSaveEvent;
          if (onAutoSave) {
            onAutoSave(autoSaveEvent.auto_save_type, autoSaveEvent.item_id);
          }
          break;

        case 'user_notification':
          const notificationEvent = event as UserNotificationEvent;
          desktopNotifications.show({
            title: notificationEvent.title,
            message: notificationEvent.message,
            project_name: notificationEvent.project_name,
            priority: notificationEvent.priority || 'normal',
          });
          break;

        case 'queue_status':
          const queueStatusEvent = event as QueueStatusEvent;
          const messages = queueStatusEvent.messages || [];
          console.log('[Chat] Queue status:', messages.length, 'messages');
          setQueueSize(messages.length);
          setQueuedMessages(messages);
          break;

        case 'error':
          console.error('[Chat] Stream error:', (event as any).error);
          setError((event as any).error || 'An error occurred');
          setIsSending(false);
          break;

        default:
          // Handle session_status and other events not in the SessionEvent union yet
          if ((event as any).type === 'session_status') {
            const sessionStatusEvent = event as any; // SessionStatusEvent
            console.log('[Chat] Session status changed:', sessionStatusEvent.status);
            // Update isSending based on session status
            if (sessionStatusEvent.status === 'working') {
              setIsSending(true);
            } else if (sessionStatusEvent.status === 'idle' || sessionStatusEvent.status === 'error') {
              setIsSending(false);
            }
          }
          break;
      }
    },
    [appendToAssistant, completeAssistantMessage, startAssistantMessage, addIncomingUserMessage, addToolUse, addToolComplete, onAutoSave, setIsSending, setError, setQueueSize, setQueuedMessages, loadFromDB, instanceId]
  );

  return handleStreamEvent;
}
