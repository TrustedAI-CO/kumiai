import { useMemo, memo } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { AgentInstance, Agent } from '@/lib/api';
import { Settings } from 'lucide-react';
import { BaseCard } from '@/ui';
import { CardHeader, CardContent } from '@/components/ui/primitives/card';
import { StatusBadge } from '@/ui';
import { TeamMembersDisplay } from '@/ui';
import { AgentTooltip } from './AgentTooltip';
import { STATUS_ICONS, isAnimatedStatus, DEFAULT_AGENT_COLOR } from '@/constants/components';

interface AgentCardProps {
  agent: AgentInstance;
  agents: Agent[];
  isSelected: boolean;
  onClick: () => void;
}

export const AgentCard = memo(function AgentCard({ agent, agents, isSelected, onClick }: AgentCardProps) {
  const StatusIcon = STATUS_ICONS[agent.status] || Settings;

  // Get agent name and color from agent_id (no legacy character fallback)
  const agentName = agent.agent_id || 'Unknown Agent';
  const agentColor = DEFAULT_AGENT_COLOR;

  // Memoize team members calculation
  const teamMembers = useMemo(() => {
    const selectedIds = agent.selected_specialists || [];
    return selectedIds
      .map(id => agents.find(a => a.id === id))
      .filter((a): a is Agent => a !== undefined);
  }, [agent.selected_specialists, agents]);

  // Determine if status should be animated
  const isStatusAnimated = isAnimatedStatus(agent.status);

  return (
    <motion.div
      className="relative"
      onClick={onClick}
      whileHover={{ y: -2 }}
      style={{ zIndex: isSelected ? 10 : 1 }}
      role="button"
      aria-pressed={isSelected}
      aria-label={`Agent ${agentName}, status: ${agent.status}`}
    >
      <BaseCard
        isSelected={isSelected}
        className="overflow-visible"
      >
        <CardHeader className="p-3 pb-2">
          <TeamMembersDisplay
            members={teamMembers}
            maxDisplay={5}
            size={40}
            showNames={true}
            tooltipComponent={AgentTooltip}
          />
        </CardHeader>

        <CardContent className="p-3 pt-0 space-y-2">
          {/* Status */}
          <StatusBadge
            status={agent.status}
            color={agentColor}
            icon={StatusIcon}
            animated={isStatusAnimated}
          />

          {/* Current Session */}
          {agent.current_session_description && (
            <div className="type-caption line-clamp-2">
              <span className="font-medium">Session:</span> {agent.current_session_description}
            </div>
          )}
        </CardContent>

        {/* Activity Indicator */}
        {agent.status === 'working' && (
          <motion.div
            className="absolute top-3 right-3 w-3 h-3 rounded-full"
            style={{ backgroundColor: agentColor }}
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
            aria-label="Agent is working"
          />
        )}
      </BaseCard>
    </motion.div>
  );
});
