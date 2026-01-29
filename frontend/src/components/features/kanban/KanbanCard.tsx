import type { AgentInstance, Agent } from '@/lib/api';
import { SessionCard } from '@/components/features/sessions/SessionCard';

interface KanbanCardProps {
  agent: AgentInstance;
  agentDefinitions: Agent[];
  onClick: () => void;
  onDelete?: (agentId: string) => void;
  dragListeners?: any;
  fileBasedAgents?: any[];
}

export function KanbanCard({ agent, agentDefinitions, onClick, onDelete, dragListeners, fileBasedAgents }: KanbanCardProps) {
  return (
    <SessionCard
      session={agent}
      agents={agentDefinitions}
      onClick={onClick}
      onDelete={onDelete}
      dragListeners={dragListeners}
      fileBasedAgents={fileBasedAgents}
      showAnimation={true}
    />
  );
}
