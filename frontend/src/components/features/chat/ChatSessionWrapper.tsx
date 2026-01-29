/**
 * ChatSessionWrapper Component
 *
 * Wrapper component that handles common chat session UI patterns:
 * - Loading states
 * - Empty states
 * - Error banners
 * - UnifiedSessionChat integration
 *
 * Consolidates duplicate patterns from PMChat, SkillAssistantChat, AgentAssistantChat
 */
import { ReactNode } from 'react';
import { LucideIcon, X } from 'lucide-react';
import { UnifiedSessionChat } from '@/components/features/sessions/UnifiedSessionChat';
import { LoadingState } from '@/ui';
import { EmptyState } from '@/ui';

interface ChatSessionWrapperProps {
  // Session state
  sessionId: string | null;
  isLoading: boolean;
  error: string | null;
  sessionStatus?: string;
  role: 'pm' | 'skill_assistant' | 'agent_assistant' | 'specialist';

  // UI customization
  icon: LucideIcon;
  loadingMessage?: string;
  emptyTitle?: string;
  emptyDescription?: string;

  // UnifiedSessionChat props
  readOnly?: boolean;
  showHeader?: boolean;
  userAvatar?: string;
  onClose?: () => void;
  onSessionJump?: (sessionId: string) => void;
  className?: string;

  // Optional custom content
  customContent?: ReactNode;
}

export function ChatSessionWrapper({
  sessionId,
  isLoading,
  error,
  sessionStatus,
  role,
  icon: Icon,
  loadingMessage = 'Loading session...',
  emptyTitle = 'No session available',
  emptyDescription,
  readOnly = false,
  showHeader = true,
  userAvatar,
  onClose,
  onSessionJump,
  className = 'h-full',
  customContent,
}: ChatSessionWrapperProps) {
  // Loading state
  if (isLoading) {
    return <LoadingState message={loadingMessage} />;
  }

  // Empty state (no session)
  if (!sessionId) {
    return (
      <EmptyState
        icon={Icon}
        title={emptyTitle}
        description={error || emptyDescription}
        centered
      />
    );
  }

  // Session loaded - show error banner if in error state
  const isErrorState = sessionStatus === 'error';
  const isReadOnly = readOnly || isErrorState;

  return (
    <div className="flex flex-col h-full">
      {/* Error banner for sessions in error state */}
      {isErrorState && (
        <div className="flex-shrink-0 bg-red-50 border-b border-red-200 px-4 py-2">
          <div className="flex items-start gap-2">
            <div className="w-5 h-5 mt-0.5 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
              <X className="w-3 h-3 text-red-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-red-900">Session Error</p>
              <p className="text-xs text-red-700 mt-0.5">
                {error || 'This session encountered an error. Chat history is read-only.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Custom content (optional) */}
      {customContent}

      {/* Chat interface */}
      <div className="flex-1 overflow-hidden">
        <UnifiedSessionChat
          instanceId={sessionId}
          role={role}
          className={className}
          readOnly={isReadOnly}
          showHeader={showHeader}
          userAvatar={userAvatar}
          onClose={onClose}
          onSessionJump={onSessionJump}
        />
      </div>
    </div>
  );
}
