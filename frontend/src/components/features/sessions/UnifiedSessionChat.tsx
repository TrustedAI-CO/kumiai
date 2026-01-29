/**
 * UnifiedSessionChat Component (REFACTORED)
 *
 * Core chat interface for all session types.
 * Clean, modular architecture with separated concerns via custom hooks.
 *
 * Architecture:
 * - useLocalMessages: Message state management (DB + streaming)
 * - useSessionData: Session metadata and agent info
 * - useStreamHandler: SSE event processing
 * - useMessageSender: Message sending logic
 * - useAutoScroll: Smart scroll behavior
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { AlertCircle } from 'lucide-react';
import { LoadingState, EmptyState } from '@/components/ui';

// Hooks
import { useLocalMessages } from '@/hooks/api/useLocalMessages';
import { useSessionData } from '@/hooks/api/useSessionData';
import { useStreamHandler } from '@/hooks/api/useStreamHandler';
import { useMessageSender } from '@/hooks/api/useMessageSender';
import { useAutoScroll } from '@/hooks/utils/useAutoScroll';

// Components
import { ChatHeader } from '@/components/features/chat/ChatHeader';
import { MessageList } from '@/components/features/chat/MessageList';
import { ChatInput, ChatInputHandle } from '@/components/features/chat/ChatInput';
import { QueuePreview } from '@/components/features/chat/QueuePreview';

// Contexts
import { FileContextProvider } from '@/contexts/FileContext';

// Utils
import { api } from '@/lib/api';
import type { SessionRole } from '@/types/session';
import { getRoleConfig, getRoleIcon } from '@/types/session';

interface UnifiedSessionChatProps {
  instanceId: string;
  role: SessionRole;
  onClose?: () => void;
  onAutoSave?: (type: 'skill' | 'agent', id: string) => void;
  onSessionJump?: (sessionId: string) => void;
  onFilesCommitted?: () => void;
  onNewSession?: () => void;
  className?: string;
  readOnly?: boolean;
  showHeader?: boolean;
  agentColor?: string;
  agentAvatar?: string;
  userAvatar?: string;
  initialSessionDescription?: string;
}

export const UnifiedSessionChat: React.FC<UnifiedSessionChatProps> = ({
  instanceId,
  role,
  onClose,
  onAutoSave,
  onSessionJump,
  onFilesCommitted,
  onNewSession,
  className = '',
  readOnly = false,
  showHeader = true,
  agentColor,
  agentAvatar,
  userAvatar,
  initialSessionDescription,
}) => {
  const roleConfig = getRoleConfig(role);

  // Message state management
  const {
    messages: localMessages,
    isLoading: messagesLoading,
    isLoadingMore,
    hasMore,
    error: messagesError,
    addUserMessage,
    addIncomingUserMessage,
    startAssistantMessage,
    appendToAssistant,
    completeAssistantMessage,
    addToolUse,
    addToolComplete,
    loadFromDB,
    loadMoreMessages,
  } = useLocalMessages();

  // Session data (agent info, description)
  const { agents, sessionAgentId, sessionDescription, sessionAgent } = useSessionData(instanceId);

  // UI state (managed here to avoid circular dependencies)
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queueSize, setQueueSize] = useState(0);
  const [queuedMessages, setQueuedMessages] = useState<import('@/types/session').QueuedMessagePreview[]>([]);

  // Refs
  const chatInputRef = useRef<ChatInputHandle>(null);
  const dragCounterRef = useRef(0);

  // Auto-scroll behavior
  const { messagesEndRef, messagesContainerRef, scrollToBottom } = useAutoScroll({
    messages: localMessages,
  });

  // Stream event handler
  const handleStreamEvent = useStreamHandler({
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
  });

  // Use ref to always access latest event handler without triggering reconnections
  const handleStreamEventRef = React.useRef(handleStreamEvent);
  React.useEffect(() => {
    handleStreamEventRef.current = handleStreamEvent;
  }, [handleStreamEvent]);

  // Message sender
  const {
    input,
    setInput,
    handleSendMessage,
  } = useMessageSender({
    instanceId,
    loadFromDB,
    onFilesCommitted,
    onSendComplete: () => scrollToBottom('smooth'),
  });

  // Handle interrupt (cancel current operation)
  const handleInterrupt = useCallback(async () => {
    try {
      await api.cancelSession(instanceId);
      setIsSending(false);
      await loadFromDB(instanceId);
    } catch (err) {
      console.error('[Chat] Failed to interrupt:', err);
    }
  }, [instanceId, loadFromDB, setIsSending]);

  // Drag and drop handlers for entire chat area
  const handleChatDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Check if dragging files
    if (e.dataTransfer.types.includes('Files')) {
      dragCounterRef.current += 1;
    }
  }, []);

  const handleChatDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleChatDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    dragCounterRef.current -= 1;
  }, []);

  const handleChatDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    dragCounterRef.current = 0;

    // Get files from drop event
    const files = Array.from(e.dataTransfer.files || []);
    if (files.length > 0 && chatInputRef.current) {
      // Add files to ChatInput
      await chatInputRef.current.addFiles(files);
    }
  }, []);

  // Load messages from DB on mount
  useEffect(() => {
    loadFromDB(instanceId);
  }, [instanceId, loadFromDB]);

  // Check session status on mount to sync isSending state
  useEffect(() => {
    const checkSessionStatus = async () => {
      try {
        const session = await api.getSession(instanceId);
        // If session is actively processing, set isSending to true
        if (session.status === 'thinking' || session.status === 'working') {
          console.log('[Chat] Session is processing on mount, setting isSending=true');
          setIsSending(true);
        }
      } catch (err) {
        console.error('[Chat] Failed to check session status:', err);
      }
    };

    checkSessionStatus();
  }, [instanceId]);

  // Queue changes are now handled by ResizeObserver in useAutoScroll
  // No need for separate scroll logic here

  // Open persistent SSE connection for session events
  useEffect(() => {
    let cleanup: (() => void) | null = null;
    let mounted = true;

    // Import the session stream utility
    import('@/lib/services/sessionStream').then(({ openSessionStream }) => {
      if (!mounted) return; // Component unmounted during import

      cleanup = openSessionStream({
        instanceId,
        onEvent: (event) => {
          // Use ref to always call the latest event handler
          // This prevents reconnections when handler dependencies change
          handleStreamEventRef.current(event);
        },
        onError: (err) => {
          console.error('[Chat] SSE stream error:', err);
          // Don't set error state for SSE failures - just log them
          // This prevents SSE connection issues from blocking the UI
        },
      });
    }).catch((err) => {
      console.error('[Chat] Failed to open SSE connection:', err);
      // Don't block UI on SSE failure
    });

    // Return cleanup function
    return () => {
      mounted = false;
      if (cleanup) {
        cleanup();
      }
    };
  }, [instanceId]); // Only reconnect when instanceId changes

  // Infinite scroll: Load more messages when scrolling to top
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      // Check if user scrolled near the top (within 100px)
      if (container.scrollTop < 100 && hasMore && !isLoadingMore && !messagesLoading) {
        // Store current scroll height to restore position after loading
        const previousScrollHeight = container.scrollHeight;
        const previousScrollTop = container.scrollTop;

        loadMoreMessages(instanceId).then(() => {
          // Restore scroll position after new messages are prepended
          // This prevents jumping to top when new messages load
          requestAnimationFrame(() => {
            if (container) {
              const newScrollHeight = container.scrollHeight;
              const scrollDiff = newScrollHeight - previousScrollHeight;
              container.scrollTop = previousScrollTop + scrollDiff;
            }
          });
        });
      }
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [instanceId, hasMore, isLoadingMore, messagesLoading, loadMoreMessages, messagesContainerRef]);

  // Derive agent avatar and color
  // Use agent_id as seed for avatar generation (like kanban board)
  const derivedAgentAvatar = agentAvatar || sessionAgentId;
  const derivedAgentColor = agentColor || sessionAgent?.icon_color;
  const hasMessages = localMessages.length > 0;

  return (
    <FileContextProvider contextType="session" contextId={instanceId}>
      <div
        className={`flex flex-col h-full ${className}`}
        onDragEnter={readOnly ? undefined : handleChatDragEnter}
        onDragOver={readOnly ? undefined : handleChatDragOver}
        onDragLeave={readOnly ? undefined : handleChatDragLeave}
        onDrop={readOnly ? undefined : handleChatDrop}
      >
      {/* Header */}
      {showHeader && (
        <ChatHeader
          title={sessionDescription || initialSessionDescription || 'New Session'}
          agentAvatar={derivedAgentAvatar || undefined}
          agentColor={derivedAgentColor || undefined}
          isProcessing={isSending}
          onClose={onClose}
          onInterrupt={isSending ? handleInterrupt : undefined}
          onNewSession={onNewSession}
        />
      )}

      {/* Messages Area */}
      <div
        ref={messagesContainerRef}
        className={`flex-1 overflow-y-auto px-2 pt-3 relative transition-all ${
          queuedMessages.length > 0 ? 'pb-2' : 'pb-4'
        }`}
      >
        {/* Loading more indicator (at top) */}
        {isLoadingMore && hasMessages && (
          <div className="flex justify-center py-2 mb-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
              <span>Loading older messages...</span>
            </div>
          </div>
        )}

        {/* Loading state */}
        {messagesLoading && !hasMessages && (
          <LoadingState message="Loading messages..." />
        )}

        {/* Error state */}
        {messagesError && (
          <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded mb-4">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{messagesError}</span>
          </div>
        )}

        {/* Empty state */}
        {!messagesLoading && !hasMessages && (
          <EmptyState
            icon={getRoleIcon(roleConfig.icon)}
            title="No messages yet"
            description="Start a conversation by sending a message"
            centered
          />
        )}

        {/* Message list */}
        {hasMessages && (
          <MessageList
            messages={localMessages}
            instanceId={instanceId}
            role={role}
            agentColor={derivedAgentColor || undefined}
            agentAvatar={derivedAgentAvatar || undefined}
            userAvatar={userAvatar}
            agents={agents}
            onSessionJump={onSessionJump}
          />
        )}

        {/* Scroll anchor - Add extra space when queue is visible */}
        <div ref={messagesEndRef} className={queuedMessages.length > 0 ? 'h-4' : ''} />
      </div>

      {/* Queue Preview */}
      {!readOnly && <QueuePreview messages={queuedMessages} />}

      {/* Input Area */}
      {!readOnly && (
        <ChatInput
          ref={chatInputRef}
          sessionId={instanceId}
          value={input}
          onChange={setInput}
          onSend={(fileMetadata) => handleSendMessage(isSending, setIsSending, setError, fileMetadata)}
          disabled={false}
          isSending={isSending}
          error={error}
          placeholder={`Message ${roleConfig.displayName}...`}
          onInterrupt={isSending ? handleInterrupt : undefined}
        />
      )}
      </div>
    </FileContextProvider>
  );
};
