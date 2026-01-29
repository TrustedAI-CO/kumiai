/**
 * PMChat Component
 *
 * PM (Project Manager) chat interface using UnifiedSessionChat.
 * Replaces ChatWidget PM functionality with unified architecture.
 */

import { useState, useEffect } from 'react';
import { Briefcase, Bot, RotateCw, Maximize2, Minimize2 } from 'lucide-react';
import { UnifiedSessionChat } from '@/components/features/sessions/UnifiedSessionChat';
import { api } from '@/lib/api';
import { useUser } from '@/contexts/UserContext';
import { LoadingState, EmptyState } from '@/components/ui';
import { SessionErrorBanner } from '@/components/features/sessions/SessionErrorBanner';
import { getErrorMessage } from '@/lib/utils';
import { ERROR_MESSAGES } from '@/constants/errorMessages';

interface PMChatProps {
  isOpen: boolean;
  onToggle: () => void;
  projectId: string;
  projectPath?: string;
  projectName?: string;
  onSessionJump?: (sessionId: string) => void;
  className?: string;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

export function PMChat({ isOpen, onToggle, projectId, projectPath, projectName, onSessionJump, className = 'bg-white', isExpanded = false, onToggleExpand }: PMChatProps) {
  const [pmInstanceId, setPmInstanceId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<string>('idle');
  const [isRecreating, setIsRecreating] = useState(false);
  const [sessionKey, setSessionKey] = useState(0); // Key to force remount on recreate
  const { profile } = useUser();

  // Load or create PM session when project changes
  useEffect(() => {
    const loadPMSession = async () => {
      if (!projectId || !projectPath) {
        setPmInstanceId(null);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Query for existing PM session for this project (include all statuses)
        // Filter by project_id at the backend for better performance and accuracy
        const sessions = await api.getSessions(projectId);

        // Find all PM sessions for this project
        const pmSessions = sessions.filter(
          (s) => s.role === 'pm'
        );

        // Warn about duplicates
        if (pmSessions.length > 1) {
          console.warn(`[PMChat] Found ${pmSessions.length} PM sessions for project ${projectId}. Using the last one. Duplicates:`,
            pmSessions.map(s => ({ id: s.instance_id, status: s.status }))
          );
        }

        // If multiple PM sessions exist, use the most recent one (or last in array)
        // This matches Projects page behavior where Map.set overwrites with last session
        const pmSession = pmSessions.length > 0 ? pmSessions[pmSessions.length - 1] : null;

        if (pmSession) {
          // Treat cancelled sessions as idle (they're ready to use again)
          const effectiveStatus = pmSession.status === 'cancelled' ? 'idle' : pmSession.status;

          setPmInstanceId(pmSession.instance_id);
          setSessionStatus(effectiveStatus || 'idle');

          // If session is in error state, set error message
          if (pmSession.status === 'error') {
            setError(ERROR_MESSAGES.PM_SESSION_ERROR);
          }
        } else {
          console.log('[PMChat] No PM session found for project', projectId);
          // PM session should have been created when project was created
          // If not found, there might be an issue
          setError(ERROR_MESSAGES.NO_PM_SESSION);
        }
      } catch (err) {
        console.error('[PMChat] Failed to load PM session:', err);
        setError(getErrorMessage(err, ERROR_MESSAGES.FAILED_LOAD_SESSIONS));
      } finally {
        setIsLoading(false);
      }
    };

    loadPMSession();
  }, [projectId, projectPath]);

  // Handle PM session recreation
  const handleRecreatePM = async () => {
    if (!pmInstanceId) {
      setError('No session to recreate');
      return;
    }

    try {
      setIsRecreating(true);
      setError(null);

      // Call API to recreate - resets the current session
      console.log('[PMChat] Recreating PM session:', pmInstanceId);
      const recreatedSession = await api.recreateSession(pmInstanceId);

      console.log('[PMChat] PM session recreated:', recreatedSession.instance_id);

      // Force UnifiedSessionChat to remount and reload messages
      setSessionKey(prev => prev + 1);
      setIsRecreating(false);
    } catch (err) {
      console.error('[PMChat] Failed to recreate PM session:', err);
      setError(getErrorMessage(err, 'Failed to recreate PM session'));
      setIsRecreating(false);
    }
  };

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
            <h3 className="text-sm font-semibold text-foreground">Project Manager</h3>
          </div>
          <div className="flex items-center gap-2">
            {/* Expand/Minimize button */}
            {onToggleExpand && (
              <button
                onClick={onToggleExpand}
                className="p-2 hover:bg-gray-100 rounded text-gray-600 hover:text-gray-700 transition-colors"
                aria-label={isExpanded ? "Exit focus mode" : "Focus on PM"}
                title={isExpanded ? "Exit focus mode" : "Focus on PM"}
              >
                {isExpanded ? (
                  <Minimize2 className="w-5 h-5" />
                ) : (
                  <Maximize2 className="w-5 h-5" />
                )}
              </button>
            )}
            {/* New Session button */}
            {pmInstanceId && (
              <button
                onClick={handleRecreatePM}
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
      </div>

      {/* Error banner for sessions in error state - positioned outside flex container */}
      {sessionStatus === 'error' && <SessionErrorBanner error={error} />}

      {/* Content */}
      <div className="flex-1 min-h-0">
        {isLoading ? (
          <LoadingState message="Loading PM session..." />
        ) : !pmInstanceId ? (
          <EmptyState
            icon={Briefcase}
            title="No PM session available"
            description={error || 'Select a project with a PM to start chatting'}
            centered
          />
        ) : (
          <UnifiedSessionChat
            key={sessionKey}
            instanceId={pmInstanceId}
            role="pm"
            className="h-full"
            readOnly={sessionStatus === 'error'}
            showHeader={false}
            userAvatar={profile?.avatar || undefined}
            onClose={onToggle}
            onSessionJump={onSessionJump}
          />
        )}
      </div>
    </div>
  );
}
