import { Project, Agent } from '@/lib/api';
import { BaseCard, DeleteButton, Avatar } from '@/ui';
import { CardHeader, CardContent } from '@/components/ui/primitives/card';

interface ProjectCardProps {
  project: Project;
  agents: Agent[];
  isSelected: boolean;
  runningSessionsCount?: number;
  onClick: () => void;
  onDelete: () => void;
}

const isProjectArchived = (project: Project): boolean => {
  return !!project.deleted_at;
};

export function ProjectCard({
  project,
  agents,
  isSelected,
  runningSessionsCount = 0,
  onClick,
  onDelete,
}: ProjectCardProps) {
  const archived = isProjectArchived(project);

  // Get assigned agents (team members)
  const assignedAgents = agents.filter(agent =>
    project.team_member_ids?.includes(agent.id)
  );

  // Build description text
  let descriptionText = project.description || '';
  if (archived) {
    descriptionText = descriptionText ? `Archived • ${descriptionText}` : 'Archived';
  }

  return (
    <div className="group relative">
      <BaseCard
        onClick={onClick}
        isSelected={isSelected}
        className="w-full"
      >
        <CardHeader className="p-3 pb-2">
          {/* Row 1: Name + Agents - with space for delete button */}
          <div className="flex items-center justify-between gap-2 pr-8">
            <h3 className="type-subtitle truncate flex-1 min-w-0">
              {project.name}
            </h3>

            {/* Assigned Agents */}
              {assignedAgents.length > 0 ? (
                <div className="flex -space-x-2 flex-shrink-0">
                  {assignedAgents.slice(0, 3).map((agent, index) => (
                    <div
                      key={agent.id}
                      className="w-6 h-6 rounded-full border-2 border-white"
                      style={{ zIndex: assignedAgents.length - index }}
                      title={agent.name}
                    >
                      <Avatar
                        seed={agent.id}
                        size={24}
                        className="w-full h-full"
                        color={agent.icon_color}
                      />
                    </div>
                  ))}
                  {assignedAgents.length > 3 && (
                    <div
                      className="w-6 h-6 rounded-full border-2 border-white bg-gray-300 flex items-center justify-center text-[10px] font-bold text-gray-700"
                      style={{ zIndex: 0 }}
                      title={`+${assignedAgents.length - 3} more agents`}
                    >
                      +{assignedAgents.length - 3}
                    </div>
                  )}
                </div>
              ) : (
                <div
                  className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 text-xs flex-shrink-0"
                  title="No agents assigned"
                >
                  ?
                </div>
              )}
          </div>
        </CardHeader>

        <CardContent className="p-3 pt-0">
          {/* Row 2: Description + Running Sessions Badge - extends to edge, below delete button */}
          <div className="flex items-center justify-between gap-2">
              <p className="type-caption truncate flex-1 min-w-0">
                {descriptionText || '\u00A0'}
              </p>

              {/* Running Sessions Badge - on the right */}
              {runningSessionsCount > 0 && (
                <div className="flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs font-medium flex-shrink-0">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
                  {runningSessionsCount}
                </div>
              )}
          </div>
        </CardContent>
      </BaseCard>

      <DeleteButton
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        title={`Delete ${project.name}`}
      />
    </div>
  );
}
