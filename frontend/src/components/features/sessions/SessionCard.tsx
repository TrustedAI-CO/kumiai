import { useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { AgentInstance, Agent } from '@/lib/api';
import { Settings } from 'lucide-react';
import { Avatar, DeleteButton } from '@/ui';
import { StatusBadge } from '@/ui';
import { TeamMembersDisplay } from '@/ui';
import { STATUS_ICONS, isAnimatedStatus, DEFAULT_AGENT_COLOR, getStatusColor } from '@/constants/components';

interface SessionCardProps {
  session: AgentInstance;
  agents: Agent[];
  onClick: () => void;
  onDelete?: (sessionId: string) => void;
  dragListeners?: any;
  fileBasedAgents?: any[];
  isSelected?: boolean;
  showAnimation?: boolean;
}

export function SessionCard({
  session,
  agents,
  onClick,
  onDelete,
  dragListeners,
  fileBasedAgents,
  isSelected = false,
  showAnimation = true
}: SessionCardProps) {
  const StatusIcon = STATUS_ICONS[session.status] || Settings;

  // Memoize team members calculation
  const teamMembers = useMemo(() => {
    const selectedIds = session.selected_specialists || [];
    return selectedIds
      .map(id => agents.find(a => a.id === id))
      .filter((a): a is Agent => a !== undefined);
  }, [session.selected_specialists, agents]);

  // Look up agent color from file-based agents
  const fileAgent = fileBasedAgents?.find(a => a.id === session.agent_id);
  const agentColor = fileAgent?.icon_color || DEFAULT_AGENT_COLOR;

  // Get status-based color for the badge
  const statusColor = getStatusColor(session.status);

  // Determine if status should be animated
  const isStatusAnimated = isAnimatedStatus(session.status);

  // Memoized delete handler
  const handleDelete = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(session.instance_id);
    }
  }, [onDelete, session.instance_id]);

  const CardWrapper = showAnimation ? motion.div : 'div';
  const animationProps = showAnimation ? {
    layout: true,
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 },
    whileHover: { scale: 1.02 },
  } : {};

  return (
    <CardWrapper
      {...animationProps}
      className={cn(
        'group relative p-2 rounded-lg border cursor-pointer transition-all bg-white',
        isSelected
          ? 'border-primary shadow-md'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
      )}
      role="button"
      aria-label={`Session: ${session.current_session_description || session.context?.description || 'No description'}, status: ${session.status}`}
    >
      {/* Delete Button */}
      {onDelete && (
        <DeleteButton
          onClick={handleDelete}
          title="Delete session"
          ariaLabel="Delete session"
        />
      )}

      {/* Drag Handle Area + Card Content */}
      <div onClick={onClick} {...dragListeners} className="cursor-grab active:cursor-grabbing">
        {/* Avatar and Status Row */}
        <div className="flex items-center gap-2 mb-2">
          <Avatar
            seed={session.agent_id || 'unknown'}
            size={28}
            className="w-7 h-7 flex-shrink-0"
            color={agentColor}
          />
          <div
            className="flex items-center gap-1 type-caption px-2 py-0.5 rounded capitalize"
            style={{
              backgroundColor: statusColor + '20',
              color: statusColor,
            }}
          >
            <StatusIcon
              className={cn(
                'w-3 h-3',
                isStatusAnimated && 'animate-spin'
              )}
            />
            <span>{session.status}</span>
          </div>
        </div>

        {/* Session Description */}
        {(session.current_session_description || session.context?.description) && (
          <p className="type-caption text-gray-600 line-clamp-2 leading-tight">
            {session.current_session_description || session.context?.description}
          </p>
        )}
      </div>
    </CardWrapper>
  );
}
