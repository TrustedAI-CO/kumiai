import { AgentInstance, Agent } from '@/lib/api';
import { Button } from '@/components/ui/primitives/button';
import { SessionCard } from '@/components/features/sessions/SessionCard';
import { Plus, ChevronRight } from 'lucide-react';
import { LoadingState } from '@/ui';

interface SessionListMobileProps {
  sessions: AgentInstance[];
  agents: Agent[];
  onSessionSelect: (session: AgentInstance) => void;
  onSessionDelete?: (sessionId: string) => void;
  onSessionCreate?: () => void;
  selectedSessionId?: string;
  onBack?: () => void;
  loading?: boolean;
  fileBasedAgents?: any[];
}

export function SessionListMobile({
  sessions,
  agents,
  onSessionSelect,
  onSessionDelete,
  onSessionCreate,
  selectedSessionId,
  onBack,
  loading = false,
  fileBasedAgents
}: SessionListMobileProps) {
  // Group sessions by stage
  const sessionsByStage = sessions.reduce((acc, session) => {
    const stage = session.kanban_stage || 'backlog';
    if (!acc[stage]) acc[stage] = [];
    acc[stage].push(session);
    return acc;
  }, {} as Record<string, AgentInstance[]>);

  const stages = [
    { id: 'backlog', label: 'Backlog' },
    { id: 'active', label: 'Active' },
    { id: 'waiting', label: 'Waiting' },
    { id: 'done', label: 'Done' },
  ];

  return (
    <div className="flex flex-col h-full bg-gray-50 overflow-hidden">
      {/* Back to Projects Header */}
      {onBack && (
        <div className="flex-shrink-0 border-b border-gray-200 bg-white px-4 py-3">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-700 hover:text-gray-900 transition-colors"
          >
            <ChevronRight className="w-5 h-5 rotate-180" />
            <span className="type-body-sm font-medium">Back to Projects</span>
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto overscroll-contain">
      {stages.map((stage) => {
        const stageSessions = sessionsByStage[stage.id] || [];
        if (stageSessions.length === 0) return null;

        return (
          <div key={stage.id} className="mb-4">
            {/* Stage Header */}
            <div className="sticky top-0 bg-gray-100 px-4 py-2 border-b border-gray-200 z-10">
              <div className="flex items-center justify-between">
                <h3 className="type-subtitle text-gray-700">
                  {stage.label}
                </h3>
                <span className="type-caption text-gray-500 bg-white px-2 py-1 rounded-full">
                  {stageSessions.length}
                </span>
              </div>
            </div>

            {/* Sessions List */}
            <div className="px-4 py-2 space-y-2">
              {stageSessions.map((session) => {
                const isSelected = session.instance_id === selectedSessionId;

                return (
                  <SessionCard
                    key={session.instance_id}
                    session={session}
                    agents={agents}
                    onClick={() => onSessionSelect(session)}
                    onDelete={onSessionDelete ? (sessionId) => {
                      if (confirm('Delete this session?')) {
                        onSessionDelete(sessionId);
                      }
                    } : undefined}
                    fileBasedAgents={fileBasedAgents}
                    isSelected={isSelected}
                    showAnimation={false}
                  />
                );
              })}
            </div>
          </div>
        );
      })}

      {sessions.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          {loading ? (
            <LoadingState message="Loading sessions..." />
          ) : (
            <div className="text-center text-gray-500">
              <p className="type-body-sm">No sessions yet</p>
              <p className="type-caption text-gray-400 mt-1">Create one to get started</p>
            </div>
          )}
        </div>
      )}
      </div>

      {/* Bottom Action Container */}
      {onSessionCreate && (
        <div className="flex-shrink-0 bg-white p-4">
          <Button
            variant="default"
            size="default"
            onClick={onSessionCreate}
            className="w-full"
          >
            <Plus className="w-5 h-5" />
            New Session
          </Button>
        </div>
      )}
    </div>
  );
}
