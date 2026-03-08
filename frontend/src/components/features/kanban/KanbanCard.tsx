import type { AgentInstance, Agent } from '@/lib/api';
import { SessionCard } from '@/components/features/sessions/SessionCard';
import type { TaskStatus } from '@/types/task';

interface KanbanCardProps {
  agent: AgentInstance;
  agentDefinitions: Agent[];
  onClick: () => void;
  onDelete?: (agentId: string) => void;
  dragListeners?: any;
  fileBasedAgents?: any[];
  taskName?: string;
  taskStatus?: TaskStatus;
}

export function KanbanCard({ agent, agentDefinitions, onClick, onDelete, dragListeners, fileBasedAgents, taskName, taskStatus }: KanbanCardProps) {
  return (
    <SessionCard
      session={agent}
      agents={agentDefinitions}
      onClick={onClick}
      onDelete={onDelete}
      dragListeners={dragListeners}
      fileBasedAgents={fileBasedAgents}
      showAnimation={true}
      taskName={taskName}
      taskStatus={taskStatus}
    />
  );
}
