/**
 * AgentAssistantChat Component
 *
 * Agent assistant chat interface using UnifiedSessionChat.
 * Helps create and edit agent configurations.
 */

import { useState } from 'react';
import { User as UserIcon, Bot, RotateCw } from 'lucide-react';
import { UnifiedSessionChat } from '@/components/features/sessions/UnifiedSessionChat';
import { api } from '@/lib/api';
import { LoadingState, EmptyState } from '@/components/ui';
import { SessionErrorBanner } from '@/components/features/sessions/SessionErrorBanner';
import { useLoadOrCreateAssistantSession } from '@/hooks/api/useLoadOrCreateAssistantSession';
import { getErrorMessage } from '@/lib/utils';
import { useUser } from '@/contexts/UserContext';

interface AgentAssistantChatProps {
  isOpen: boolean;
  onToggle: () => void;
  agentId?: string;
  agentName?: string;
  onAgentUpdated?: () => void; // Callback when agent is auto-saved
  className?: string;
}

export function AgentAssistantChat({
  isOpen,
  onToggle,
  agentId,
  agentName,
  onAgentUpdated,
  className = 'bg-white',
}: AgentAssistantChatProps) {
  const { profile } = useUser();

  // Load or create agent assistant session
  const { sessionId, isLoading, error, sessionStatus } = useLoadOrCreateAssistantSession({
    role: 'agent_assistant',
    sessionDescription: 'Agent Assistant - helps create/edit agent configurations',
    projectPath: '', // Backend will override with settings.agents_dir
  });

  // Local loading state for recreation
  const [isRecreating, setIsRecreating] = useState(false);
  const [recreateError, setRecreateError] = useState<string | null>(null);
  const [sessionKey, setSessionKey] = useState(0); // Key to force remount on recreate

  // Handle auto-save events
  const handleAutoSave = (type: 'skill' | 'agent', id: string) => {
    console.log('[AgentAssistantChat] Auto-save event:', type, id);
    if (type === 'agent' && onAgentUpdated) {
      onAgentUpdated();
    }
  };

  // Handle agent assistant recreation
  const handleRecreateAgentAssistant = async () => {
    if (!sessionId) {
      setRecreateError('No session to recreate');
      return;
    }

    try {
      setIsRecreating(true);
      setRecreateError(null);

      // Call API to recreate - resets the current session
      console.log('[AgentAssistantChat] Recreating agent assistant session:', sessionId);
      const recreatedSession = await api.recreateSession(sessionId);

      console.log('[AgentAssistantChat] Agent assistant session recreated:', recreatedSession.instance_id);

      // Force UnifiedSessionChat to remount and reload messages
      setSessionKey(prev => prev + 1);
      setIsRecreating(false);
    } catch (err) {
      console.error('[AgentAssistantChat] Failed to recreate agent assistant:', err);
      setRecreateError(getErrorMessage(err, 'Failed to recreate agent assistant'));
      setIsRecreating(false);
    }
  };

  // Mobile: full screen, Desktop: fills the detail panel area
  // Note: The floating toggle button is rendered by the parent page
  if (!isOpen) {
    return null;
  }

  return (
    <div className={`flex-1 flex flex-col min-h-0 ${className}`}>
      {/* Header */}
      <div className="flex-shrink-0 h-14 px-4">
        <div className="flex items-center justify-between h-full">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Agent Assistant</h3>
          </div>
          {/* New Session button */}
          {sessionId && (
            <button
              onClick={handleRecreateAgentAssistant}
              disabled={isRecreating}
              className="p-2 hover:bg-gray-100 rounded text-gray-600 hover:text-gray-700 transition-colors disabled:opacity-50"
              aria-label="New Session"
              title="Start new session"
            >
              <RotateCw className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Error banner for sessions in error state - positioned outside flex container */}
      {sessionStatus === 'error' && <SessionErrorBanner />}

      {/* Content */}
      <div className="flex-1 min-h-0">
        {isLoading ? (
          <LoadingState message="Loading agent assistant session..." />
        ) : !sessionId ? (
          <EmptyState
            icon={UserIcon}
            title="No agent assistant session"
            description={error || 'Select an agent to start chatting with the assistant'}
            centered
          />
        ) : (
          <UnifiedSessionChat
            key={sessionKey}
            instanceId={sessionId}
            role="agent_assistant"
            onClose={onToggle}
            className="h-full"
            readOnly={sessionStatus === 'error'}
            onAutoSave={handleAutoSave}
            onNewSession={handleRecreateAgentAssistant}
            showHeader={false}
            userAvatar={profile?.avatar || undefined}
          />
        )}
      </div>
    </div>
  );
}
