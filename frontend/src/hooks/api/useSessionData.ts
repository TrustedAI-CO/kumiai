/**
 * useSessionData hook
 *
 * Loads session metadata and agent information.
 */

import { useState, useEffect } from 'react';
import { api, type Agent } from '@/lib/api';

export function useSessionData(instanceId: string) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [sessionAgentId, setSessionAgentId] = useState<string | null>(null);
  const [sessionDescription, setSessionDescription] = useState<string | null>(null);

  // Load session to get agent_id and description
  useEffect(() => {
    api
      .getSession(instanceId)
      .then((session) => {
        if (session.agent_id) {
          setSessionAgentId(session.agent_id);
        }
        // Description is in context.description (or context.task_description as fallback)
        const description = session.context?.description || session.context?.task_description;
        if (description) {
          setSessionDescription(description);
        }
      })
      .catch((err) => console.error('[Chat] Failed to load session:', err));
  }, [instanceId]);

  // Load agents for avatar display
  useEffect(() => {
    api
      .getAgents()
      .then(setAgents)
      .catch((err) => console.error('[Chat] Failed to load agents:', err));
  }, []);

  // Derive agent avatar and color from session's agent_id
  const sessionAgent = sessionAgentId ? agents.find(a => a.id === sessionAgentId) : null;

  return {
    agents,
    sessionAgentId,
    sessionDescription,
    sessionAgent,
  };
}
