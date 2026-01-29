/**
 * SkillAssistantChat Component
 *
 * Skill assistant chat interface using UnifiedSessionChat.
 * Replaces ChatWidget skill_assistant functionality with unified architecture.
 */

import { useState } from 'react';
import { Wrench, Bot, RotateCw } from 'lucide-react';
import { UnifiedSessionChat } from '@/components/features/sessions/UnifiedSessionChat';
import { api } from '@/lib/api';
import { LoadingState, EmptyState } from '@/components/ui';
import { SessionErrorBanner } from '@/components/features/sessions/SessionErrorBanner';
import { useLoadOrCreateAssistantSession } from '@/hooks/api/useLoadOrCreateAssistantSession';
import { getErrorMessage } from '@/lib/utils';
import { useUser } from '@/contexts/UserContext';

interface SkillAssistantChatProps {
  isOpen: boolean;
  onToggle: () => void;
  skillId?: string;
  skillName?: string;
  onSkillUpdated?: () => void; // Callback when skill is auto-saved
  className?: string;
}

export function SkillAssistantChat({
  isOpen,
  onToggle,
  skillId,
  skillName,
  onSkillUpdated,
  className = 'bg-white',
}: SkillAssistantChatProps) {
  const { profile } = useUser();

  // Load or create skill assistant session
  const { sessionId, isLoading, error, sessionStatus } = useLoadOrCreateAssistantSession({
    role: 'skill_assistant',
    sessionDescription: 'Skill Assistant - helps create/edit skill definitions',
    projectPath: '', // Backend will override with settings.skills_dir
  });

  // Local loading state for recreation
  const [isRecreating, setIsRecreating] = useState(false);
  const [recreateError, setRecreateError] = useState<string | null>(null);
  const [sessionKey, setSessionKey] = useState(0); // Key to force remount on recreate

  // Handle auto-save events
  const handleAutoSave = (type: 'skill' | 'agent', id: string) => {
    console.log('[SkillAssistantChat] Auto-save event:', type, id);
    if (type === 'skill' && onSkillUpdated) {
      onSkillUpdated();
    }
  };

  // Handle skill assistant recreation
  const handleRecreateSkillAssistant = async () => {
    if (!sessionId) {
      setRecreateError('No session to recreate');
      return;
    }

    try {
      setIsRecreating(true);
      setRecreateError(null);

      // Call API to recreate - resets the current session
      console.log('[SkillAssistantChat] Recreating skill assistant session:', sessionId);
      const recreatedSession = await api.recreateSession(sessionId);

      console.log('[SkillAssistantChat] Skill assistant session recreated:', recreatedSession.instance_id);

      // Force UnifiedSessionChat to remount and reload messages
      setSessionKey(prev => prev + 1);
      setIsRecreating(false);
    } catch (err) {
      console.error('[SkillAssistantChat] Failed to recreate skill assistant:', err);
      setRecreateError(getErrorMessage(err, 'Failed to recreate skill assistant'));
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
            <h3 className="text-sm font-semibold text-foreground">Skill Assistant</h3>
          </div>
          {/* New Session button */}
          {sessionId && (
            <button
              onClick={handleRecreateSkillAssistant}
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
          <LoadingState message="Loading skill assistant session..." />
        ) : !sessionId ? (
          <EmptyState
            icon={Wrench}
            title="No skill assistant session"
            description={error || 'Select a skill to start chatting with the assistant'}
            centered
          />
        ) : (
          <UnifiedSessionChat
            key={sessionKey}
            instanceId={sessionId}
            role="skill_assistant"
            onClose={onToggle}
            className="h-full"
            readOnly={sessionStatus === 'error'}
            onAutoSave={handleAutoSave}
            onNewSession={handleRecreateSkillAssistant}
            showHeader={false}
            userAvatar={profile?.avatar || undefined}
          />
        )}
      </div>
    </div>
  );
}
