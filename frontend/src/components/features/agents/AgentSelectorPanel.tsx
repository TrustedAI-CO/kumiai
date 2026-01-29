import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Avatar } from '@/ui';
import { Input } from '@/components/ui/primitives/input';
import { getSkillIcon } from '@/constants/skillIcons';
import type { Agent, SkillMetadata } from '@/lib/api';

interface AgentSelectorPanelProps {
  agents: Agent[];
  skills: SkillMetadata[];
  selectedAgentIds: string[];
  onToggleAgent: (agentId: string) => void;
  searchPlaceholder?: string;
  multiSelect?: boolean;
  maxHeight?: string;
  showPMControls?: boolean;
  pmId?: string;
  onSetPM?: (agentId: string) => void;
}

export function AgentSelectorPanel({
  agents,
  skills,
  selectedAgentIds,
  onToggleAgent,
  searchPlaceholder = 'Search agents...',
  maxHeight,
  showPMControls = false,
  pmId = '',
  onSetPM,
}: AgentSelectorPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredAgents = agents.filter(agent => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      agent.name.toLowerCase().includes(query) ||
      (agent.description && agent.description.toLowerCase().includes(query))
    );
  });

  return (
    <div className="flex flex-col h-full" style={{ maxHeight }}>
      {/* Agent List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0">
        {filteredAgents.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              <p className="type-body-sm">No agents found</p>
              <p className="type-caption text-gray-400 mt-1">
                Try a different search term or create a new agent
              </p>
            </div>
          </div>
        ) : (
          filteredAgents.map((agent) => {
            const isSelected = selectedAgentIds.includes(agent.id);
            const isPM = showPMControls && pmId === agent.id;

            return (
              <button
                key={agent.id}
                onClick={() => onToggleAgent(agent.id)}
                type="button"
                className={cn(
                  'w-full p-2.5 rounded-lg border text-left transition-all hover:shadow-sm',
                  isSelected
                    ? 'border-primary bg-muted/50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                )}
              >
                {/* Header with Avatar and Name */}
                <div className="flex items-center gap-2.5">
                  <Avatar
                    seed={agent.id}
                    size={36}
                    className="w-9 h-9 flex-shrink-0"
                    color={agent.icon_color}
                  />
                  <div className="flex-1 min-w-0">
                    {/* Name, Skills, and PM badge */}
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <div className="type-body-sm font-medium text-gray-900 truncate">
                        {agent.name}
                      </div>
                      {/* Skills */}
                      {agent.skills && agent.skills.length > 0 && (
                        <div className="flex items-center -space-x-0.5 flex-shrink-0">
                          {agent.skills.slice(0, 3).map((skillId: string) => {
                            const skill = skills.find(s => s.id === skillId);
                            if (!skill) return null;
                            const IconComponent = getSkillIcon(skill.icon);
                            return (
                              <div
                                key={skillId}
                                className={`w-5 h-5 rounded-full flex items-center justify-center transition-all ${
                                  skill.icon_color ? '' : 'bg-gray-100'
                                }`}
                                style={
                                  skill.icon_color
                                    ? { backgroundColor: skill.icon_color }
                                    : undefined
                                }
                                title={skill.name}
                              >
                                <IconComponent className="w-2.5 h-2.5 text-white" />
                              </div>
                            );
                          })}
                          {agent.skills.length > 3 && (
                            <div
                              className={cn(
                                'w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-medium',
                                isSelected
                                  ? 'bg-muted text-primary'
                                  : 'bg-gray-200 text-gray-600'
                              )}
                            >
                              +{agent.skills.length - 3}
                            </div>
                          )}
                        </div>
                      )}
                      {isPM && (
                        <span className="flex-shrink-0 text-[10px] font-medium px-1.5 py-0.5 bg-yellow-100 text-yellow-800 rounded">
                          ★ PM
                        </span>
                      )}
                    </div>
                    <div className="type-caption text-gray-500 line-clamp-1">
                      {agent.description || 'No description'}
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {isSelected && (
                      <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                        <span className="text-white text-xs">✓</span>
                      </div>
                    )}
                    {showPMControls && onSetPM && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (isSelected) {
                            onSetPM(isPM ? '' : agent.id);
                          }
                        }}
                        disabled={!isSelected}
                        className={cn(
                          'w-5 h-5 rounded-full flex items-center justify-center transition-all',
                          isPM
                            ? 'bg-yellow-400 text-white'
                            : isSelected
                            ? 'bg-gray-200 text-gray-400 hover:bg-yellow-200'
                            : 'bg-gray-100 text-gray-300'
                        )}
                        title={isPM ? 'Remove as PM' : 'Set as PM'}
                      >
                        <span className="text-xs">★</span>
                      </button>
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* Search Bar */}
      <div className="p-4">
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={searchPlaceholder}
        />
      </div>
    </div>
  );
}
