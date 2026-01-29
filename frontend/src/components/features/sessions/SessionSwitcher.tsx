/**
 * SessionSwitcher - Quick session switcher modal
 *
 * Keyboard-accessible modal for quickly switching between sessions.
 * Triggered by Cmd/Ctrl + Shift + S shortcut.
 */
import { useState, useEffect } from 'react';
import { api, AgentInstance, Agent, Project } from '@/lib/api';
import { cn } from '@/lib/utils';
import { SwitcherModal, SwitcherSection, SwitcherEmpty, Avatar } from '@/ui';

interface SessionSwitcherProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectSession: (instanceId: string) => void;
  currentProjectId?: string;
}

export function SessionSwitcher({
  isOpen,
  onClose,
  onSelectSession,
  currentProjectId,
}: SessionSwitcherProps) {
  const [sessions, setSessions] = useState<AgentInstance[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);

  // Load sessions when modal opens
  useEffect(() => {
    if (isOpen) {
      loadData();
      setSearchQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sessionsData, agentsData, projectsData] = await Promise.all([
        api.getSessions(),
        api.getAgents(),
        api.getProjects(false),
      ]);

      // Filter out PM sessions - only show what kanban/table view shows
      const filteredSessions = sessionsData.filter(session => session.role !== 'pm');

      setSessions(filteredSessions);
      setAgents(agentsData);
      setProjects(projectsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get agent name by ID
  const getAgentName = (agentId?: string): string => {
    if (!agentId) return 'Unknown';
    const agent = agents.find((a) => a.id === agentId);
    return agent?.name || agentId;
  };

  // Get project name by ID
  const getProjectName = (projectId: string): string => {
    const project = projects.find((p) => p.id === projectId);
    return project?.name || 'Unknown Project';
  };

  // Get session description (same as SessionCard)
  const getSessionDescription = (session: AgentInstance): string => {
    return session.current_session_description || session.context?.description || 'No description';
  };

  // Get agent avatar color
  const getAgentColor = (agentId?: string): string => {
    if (!agentId) return '#6366f1'; // default primary color
    const agent = agents.find((a) => a.id === agentId);
    return agent?.icon_color || '#6366f1';
  };

  // Filter sessions: only current project + search by description
  const filteredSessions = sessions.filter((session) => {
    // Only show sessions from current project
    if (currentProjectId && session.project_id !== currentProjectId) {
      return false;
    }

    // If no current project, don't show any sessions
    if (!currentProjectId) {
      return false;
    }

    // Search by description only
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    const description = getSessionDescription(session).toLowerCase();
    return description.includes(query);
  });

  // Sort by started_at descending (most recent first)
  const sortedSessions = [...filteredSessions].sort((a, b) => {
    return new Date(b.started_at).getTime() - new Date(a.started_at).getTime();
  });

  // Recent sessions (top 5)
  const recentSessions = sortedSessions.slice(0, 5);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, sortedSessions.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const session = sortedSessions[selectedIndex];
        if (session) {
          onSelectSession(session.instance_id);
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, sortedSessions, onSelectSession, onClose]);

  const emptyMessage = !currentProjectId
    ? 'No project selected'
    : searchQuery
      ? 'No sessions found'
      : 'No sessions in this project';

  return (
    <SwitcherModal
      isOpen={isOpen}
      onClose={onClose}
      searchQuery={searchQuery}
      onSearchChange={(value) => {
        setSearchQuery(value);
        setSelectedIndex(0);
      }}
      placeholder="Search sessions by description..."
      title="Sessions"
      subtitle="Quick session switcher"
      shortcut="Cmd/Ctrl + Shift + S"
      loading={loading}
    >
      {sortedSessions.length === 0 ? (
        <SwitcherEmpty message={emptyMessage} />
      ) : (
        <>
          {/* Recent Sessions */}
          {!searchQuery && (
            <SwitcherSection title="Recent Sessions">
              {recentSessions.map((session, index) => (
                <SessionItem
                  key={session.instance_id}
                  session={session}
                  description={getSessionDescription(session)}
                  agentName={getAgentName(session.agent_id)}
                  agentColor={getAgentColor(session.agent_id)}
                  isSelected={index === selectedIndex}
                  onClick={() => {
                    onSelectSession(session.instance_id);
                    onClose();
                  }}
                />
              ))}
            </SwitcherSection>
          )}

          {/* All/Filtered Sessions */}
          {searchQuery && (
            <SwitcherSection title="All Sessions">
              {sortedSessions.map((session, index) => (
                <SessionItem
                  key={session.instance_id}
                  session={session}
                  description={getSessionDescription(session)}
                  agentName={getAgentName(session.agent_id)}
                  agentColor={getAgentColor(session.agent_id)}
                  isSelected={index === selectedIndex}
                  onClick={() => {
                    onSelectSession(session.instance_id);
                    onClose();
                  }}
                />
              ))}
            </SwitcherSection>
          )}
        </>
      )}
    </SwitcherModal>
  );
}

// Session Item Component
interface SessionItemProps {
  session: AgentInstance;
  description: string;
  agentName: string;
  agentColor: string;
  isSelected: boolean;
  onClick: () => void;
}

function SessionItem({ session, description, agentName, agentColor, isSelected, onClick }: SessionItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-left",
        isSelected
          ? "bg-muted text-foreground"
          : "hover:bg-gray-100 text-gray-700"
      )}
    >
      <Avatar
        seed={session.agent_id || 'unknown'}
        size={32}
        className="w-8 h-8 flex-shrink-0"
        color={agentColor}
      />

      <div className="flex-1 min-w-0">
        <p className="type-body-sm font-medium truncate line-clamp-2 mb-0.5">
          {description}
        </p>
        <p className="type-caption text-gray-500 truncate">
          {agentName}
        </p>
      </div>
    </button>
  );
}
