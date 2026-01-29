/**
 * useMessageSender hook
 *
 * Handles sending messages via the enqueue endpoint.
 */

import { useState, useCallback } from 'react';
import { sendMessage } from '@/lib/services/messageSender';

interface UseMessageSenderOptions {
  instanceId: string;
  loadFromDB: (sessionId: string) => Promise<void>;
  onFilesCommitted?: () => void;
  onSendComplete?: () => void;
}

export function useMessageSender({
  instanceId,
  loadFromDB,
  onFilesCommitted,
  onSendComplete,
}: UseMessageSenderOptions) {
  const [input, setInput] = useState('');
  const [pendingFileMetadata, setPendingFileMetadata] = useState<string>('');

  const handleSendMessage = useCallback(async (
    isSending: boolean,
    setIsSending: (value: boolean) => void,
    setError: (value: string | null) => void,
    fileMetadata?: string // Optional file metadata to append
  ) => {
    // Allow queueing multiple messages even when session is processing
    if (!input.trim() && !fileMetadata) return;

    // Build final message content with file metadata if provided
    const baseMessage = input.trim() || '';
    const finalMessage = fileMetadata ? baseMessage + fileMetadata : baseMessage;

    // Convert single newlines to double for proper Markdown rendering
    const messageContent = finalMessage.replace(/\n/g, '\n\n');
    setInput('');
    setPendingFileMetadata('');
    setError(null);

    // Set processing indicator immediately to show user feedback
    setIsSending(true);

    // NOTE: User message is NOT added optimistically here
    // It will be added via SSE stream (user_message event) from the backend
    // This ensures consistent behavior with cross-session messages

    // Notify parent that message was sent (for scroll)
    if (onSendComplete) {
      onSendComplete();
    }

    try {
      // Enqueue message (returns immediately)
      await sendMessage({
        instanceId,
        content: messageContent,
        onUserMessageSent: () => {
          console.log('[Chat] Message enqueued');
          if (onFilesCommitted) {
            onFilesCommitted();
          }
        },
        onError: (err) => {
          console.error('[Chat] Enqueue error:', err);
          setError(err.message);
          setIsSending(false);
          // On error, reload from DB to get correct state
          loadFromDB(instanceId);
        },
      });
    } catch (err) {
      console.error('[Chat] Enqueue failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to send message');
      setIsSending(false);
      // On error, reload from DB to get correct state
      loadFromDB(instanceId);
    }
  }, [input, instanceId, onFilesCommitted, loadFromDB, onSendComplete]);

  return {
    input,
    setInput,
    handleSendMessage,
    setPendingFileMetadata,
  };
}
