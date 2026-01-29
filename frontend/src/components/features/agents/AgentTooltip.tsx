import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import type { Agent } from '@/lib/api';

interface AgentTooltipProps {
  agent: Agent;
  targetRef: React.RefObject<HTMLDivElement>;
}

export function AgentTooltip({ agent, targetRef }: AgentTooltipProps) {
  const [position, setPosition] = useState({ top: 0, left: 0 });

  useEffect(() => {
    if (targetRef.current) {
      const rect = targetRef.current.getBoundingClientRect();
      setPosition({
        top: rect.top - 10,
        left: rect.left + rect.width / 2,
      });
    }
  }, [targetRef]);

  return createPortal(
    <div
      className="fixed z-[9999] w-64 pointer-events-none"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
        transform: 'translate(-50%, -100%)',
      }}
      role="tooltip"
      aria-label={`${agent.name} details`}
    >
      <div className="bg-gray-900 text-white text-xs rounded-lg p-3 shadow-xl pointer-events-auto">
        <div className="font-bold mb-1">{agent.name}</div>
        <div className="text-gray-300 mb-2">{agent.description}</div>
        {agent.skills && agent.skills.length > 0 && (
          <div>
            <div className="font-medium text-gray-400 mb-1">Skills:</div>
            <div className="flex flex-wrap gap-1">
              {agent.skills.map(skill => (
                <span key={skill} className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-200">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
        {/* Arrow */}
        <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
      </div>
    </div>,
    document.body
  );
}
