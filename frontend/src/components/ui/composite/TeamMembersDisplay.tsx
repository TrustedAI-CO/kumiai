import { useCallback, useState, useRef } from 'react';
import { Avatar } from './Avatar';
import type { Agent } from '@/lib/api';

interface TeamMembersDisplayProps {
  members: Agent[];
  maxDisplay?: number;
  size?: number;
  showNames?: boolean;
  onMemberHover?: (member: Agent | null) => void;
  className?: string;
  tooltipComponent?: React.ComponentType<{ agent: Agent; targetRef: React.RefObject<HTMLDivElement> }>;
}

/**
 * Displays a horizontal list of team member avatars with optional overflow indicator.
 * Supports hover interactions and optional name display.
 */
export function TeamMembersDisplay({
  members,
  maxDisplay = 5,
  size = 40,
  showNames = false,
  onMemberHover,
  className = '',
  tooltipComponent: TooltipComponent,
}: TeamMembersDisplayProps) {
  const [hoveredMember, setHoveredMember] = useState<Agent | null>(null);
  const hoveredRef = useRef<HTMLDivElement>(null);

  const handleMouseEnter = useCallback((member: Agent) => {
    setHoveredMember(member);
    onMemberHover?.(member);
  }, [onMemberHover]);

  const handleMouseLeave = useCallback(() => {
    setHoveredMember(null);
    onMemberHover?.(null);
  }, [onMemberHover]);

  if (members.length === 0) {
    return null;
  }

  const displayedMembers = members.slice(0, maxDisplay);
  const remainingCount = members.length - maxDisplay;

  return (
    <div className={`flex items-center ${className}`}>
      {displayedMembers.map((member, index) => (
        <div
          key={member.id}
          ref={hoveredMember?.id === member.id ? hoveredRef : null}
          className={showNames ? 'text-center' : ''}
          style={{
            marginLeft: index > 0 ? `-${size * 0.3}px` : '0',
            zIndex: index,
          }}
          onMouseEnter={() => handleMouseEnter(member)}
          onMouseLeave={handleMouseLeave}
        >
          <Avatar
            seed={member.id}
            size={size}
            className={showNames ? 'mx-auto ring-2 ring-white' : 'ring-2 ring-white'}
            color={member.icon_color}
          />
          {showNames && (
            <div className="type-label text-gray-700 mt-1 truncate max-w-[60px]">
              {member.name}
            </div>
          )}
        </div>
      ))}

      {TooltipComponent && hoveredMember && (
        <TooltipComponent agent={hoveredMember} targetRef={hoveredRef} />
      )}

      {remainingCount > 0 && (
        <div
          className={showNames ? 'text-center' : ''}
          style={{
            marginLeft: displayedMembers.length > 0 ? `-${size * 0.3}px` : '0',
            zIndex: displayedMembers.length,
          }}
        >
          <div
            className="rounded-full bg-gray-200 flex items-center justify-center type-label text-gray-600 ring-2 ring-white"
            style={{
              width: size,
              height: size,
            }}
            aria-label={`${remainingCount} more team members`}
          >
            +{remainingCount}
          </div>
        </div>
      )}
    </div>
  );
}
