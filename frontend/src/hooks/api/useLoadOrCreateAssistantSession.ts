/**
 * useLoadOrCreateAssistantSession Hook
 *
 * Consolidates duplicate session loading logic from SkillAssistantChat and AgentAssistantChat
 */
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { getErrorMessage } from '@/lib/utils';

interface UseLoadOrCreateAssistantSessionOptions {
  role: 'skill_assistant' | 'agent_assistant';
  sessionDescription: string;
  projectPath?: string;
}

interface UseLoadOrCreateAssistantSessionResult {
  sessionId: string | null;
  isLoading: boolean;
  error: string | null;
  sessionStatus: string;
  recreateSession: () => Promise<void>;
}

export function useLoadOrCreateAssistantSession(
  options: UseLoadOrCreateAssistantSessionOptions
): UseLoadOrCreateAssistantSessionResult {
  const { role, sessionDescription, projectPath = '' } = options;

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<string>('idle');

  const loadOrCreateSession = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Query for existing assistant session
      const sessions = await api.getSessions();

      console.log(`[${role}] All sessions:`, sessions.map(s => ({ id: s.instance_id, role: s.role, status: s.status })));

      // Find all sessions for this role (exclude cancelled and error)
      const assistantSessions = sessions
        .filter(
          (s) =>
            s.role === role &&
            s.status !== 'cancelled' &&
            s.status !== 'error'
        )
        // Sort by creation date (most recent first)
        .sort((a, b) => {
          const dateA = new Date(a.started_at || a.created_at || 0);
          const dateB = new Date(b.started_at || b.created_at || 0);
          return dateB.getTime() - dateA.getTime();
        });

      console.log(`[${role}] Found ${role} sessions:`, assistantSessions.length);

      // Use the most recent session
      const session = assistantSessions[0];

      if (session) {
        console.log(`[${role}] Using session:`, session.instance_id, 'status:', session.status);
        setSessionId(session.instance_id);
        setSessionStatus(session.status || 'idle');
      } else {
        // No session found, create one automatically
        console.log(`[${role}] No session found, creating new ${role} session`);
        const newSession = await api.launchSession({
          team_member_ids: [],
          project_path: projectPath,
          session_description: sessionDescription,
          role: role,
          auto_start: false, // Don't auto-start, wait for user message
        });

        console.log(`[${role}] Created new session:`, newSession.instance_id);
        setSessionId(newSession.instance_id);
        setSessionStatus(newSession.status || 'idle');
      }
    } catch (err) {
      console.error(`[${role}] Failed to load/create session:`, err);
      setError(getErrorMessage(err, `Failed to load ${role} session`));
    } finally {
      setIsLoading(false);
    }
  };

  const recreateSession = async () => {
    console.log(`[${role}] Recreating session...`);
    setSessionId(null);
    setSessionStatus('idle');
    await loadOrCreateSession();
  };

  // Load session on mount
  useEffect(() => {
    loadOrCreateSession();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    sessionId,
    isLoading,
    error,
    sessionStatus,
    recreateSession,
  };
}
