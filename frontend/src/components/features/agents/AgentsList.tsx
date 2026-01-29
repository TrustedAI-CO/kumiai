import { useState, useEffect, useMemo } from 'react';
import { Plus, User } from 'lucide-react';
import { api, Agent } from '@/lib/api';
import { Avatar, DeleteButton } from '@/ui';
import { ItemCard } from '@/ui';
import { ListLayout } from '@/components/layout/ListLayout';
import { cn } from '@/lib/utils';

interface AgentsListProps {
  currentAgentId?: string;
  onSelectAgent: (agentId: string) => void;
  onDeleteAgent: (agentId: string) => void;
  onCreateAgent: () => void;
  isMobile?: boolean;
  reloadTrigger?: number;
}

export function AgentsList({
  currentAgentId,
  onSelectAgent,
  onDeleteAgent,
  onCreateAgent,
  isMobile = false,
  reloadTrigger
}: AgentsListProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    if (reloadTrigger !== undefined) {
      loadAgents();
    }
  }, [reloadTrigger]);

  const loadAgents = async () => {
    setLoading(true);
    try {
      const data = await api.getAgents();
      setAgents(data);
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredAgents = useMemo(() =>
    agents.filter(agent =>
      agent.name.toLowerCase().includes(searchQuery.toLowerCase())
    ),
    [agents, searchQuery]
  );

  return (
    <ListLayout
      searchQuery={searchQuery}
      onSearchChange={setSearchQuery}
      searchPlaceholder="Search agents..."
      loading={loading}
      isEmpty={filteredAgents.length === 0}
      emptyIcon={User}
      emptyTitle={searchQuery ? 'No agents found' : 'No agents yet'}
      emptyDescription={searchQuery ? 'Try a different search term' : 'Create one to get started'}
      actionButtons={[
        { icon: Plus, onClick: onCreateAgent, title: 'New Agent', variant: 'primary' }
      ]}
      isMobile={isMobile}
    >
      <div className={cn("flex flex-col gap-2")}>
        {filteredAgents.map((agent) => (
          <div
            key={agent.id}
            className="group relative"
          >
            <ItemCard
              id={agent.id}
              name={agent.name}
              description={agent.description || 'No description'}
              icon={<Avatar seed={agent.id} size={32} className="w-full h-full" color={agent.icon_color} />}
              iconColor={agent.icon_color}
              onClick={() => onSelectAgent(agent.id)}
              isSelected={currentAgentId === agent.id}
            />
            <DeleteButton
              onClick={(e) => {
                e.stopPropagation();
                onDeleteAgent(agent.id);
              }}
              title={`Delete ${agent.name}`}
            />
          </div>
        ))}
      </div>
    </ListLayout>
  );
}
