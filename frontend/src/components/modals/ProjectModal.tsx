import { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { api, Project, CreateProjectRequest, UpdateProjectRequest, Agent, SkillMetadata } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Avatar } from '@/ui';
import { Input } from '@/components/ui/primitives/input';
import { Textarea } from '@/components/ui/primitives/textarea';
import { ModalActionButton } from '@/ui';
import { AgentSelectorPanel } from '@/components/features/agents/AgentSelectorPanel';
import { useIsMobile } from '@/hooks';
import { getSkillIcon } from '@/constants/skillIcons';

export interface ProjectModalProps {
  project: Project | null;
  onSave: (data: CreateProjectRequest | UpdateProjectRequest) => void;
  onClose: () => void;
}

export function ProjectModal({ project, onSave, onClose }: ProjectModalProps) {
  const [formData, setFormData] = useState({
    name: project?.name || '',
    description: project?.description || '',
    pm_id: project?.pm_agent_id || '',
    team_member_ids: project?.pm_agent_id ? [project.pm_agent_id] : [],
    path: project?.path || '',
  });
  const [agents, setAgents] = useState<Agent[]>([]);
  const [skills, setSkills] = useState<SkillMetadata[]>([]);
  const isMobile = useIsMobile();

  useEffect(() => {
    api.getAgents().then(setAgents).catch(console.error);
    api.getSkills().then(setSkills).catch(console.error);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const toggleTeamMember = (agentId: string) => {
    setFormData(prev => {
      const isCurrentlySelected = prev.team_member_ids.includes(agentId);
      const newTeamMemberIds = isCurrentlySelected
        ? prev.team_member_ids.filter(id => id !== agentId)
        : [...prev.team_member_ids, agentId];

      // Auto-set PM when only one agent is selected
      let newPmId = prev.pm_id;
      if (newTeamMemberIds.length === 1) {
        newPmId = newTeamMemberIds[0];
      } else if (isCurrentlySelected && prev.pm_id === agentId) {
        // Clear PM if removing the current PM
        newPmId = '';
      }

      return {
        ...prev,
        team_member_ids: newTeamMemberIds,
        pm_id: newPmId,
      };
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      alert('Project name is required');
      return;
    }

    // Don't send path if empty - let backend auto-generate in ~/.kumiai/projects/
    const projectPath = formData.path.trim() || undefined;

    onSave({
      name: formData.name.trim(),
      description: formData.description.trim() || undefined,
      path: projectPath,
      pm_agent_id: formData.pm_id || undefined,
      team_member_ids: formData.team_member_ids,
    } as CreateProjectRequest);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[101] p-0 lg:p-4">
      <div className="bg-white rounded-none lg:rounded-lg shadow-xl max-w-6xl w-full h-full lg:h-[70vh] flex flex-col">
        <form onSubmit={handleSubmit} className="flex flex-col h-full">
          {/* Header */}
          <div className="px-4 lg:px-6 py-2.5 lg:py-3 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">
              {project ? 'Edit Project' : 'New Project'}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Plus className="w-5 h-5 text-gray-500 rotate-45" />
            </button>
          </div>

          {/* Body - Responsive Layout (stacked on mobile, side-by-side on desktop) */}
          <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
            {/* Team Selection Column */}
            <div className="flex lg:w-1/2 border-b lg:border-b-0 lg:border-r border-gray-200 flex-col" style={{ maxHeight: isMobile ? '40vh' : 'auto' }}>
              <AgentSelectorPanel
                agents={agents}
                skills={skills}
                selectedAgentIds={formData.team_member_ids}
                onToggleAgent={toggleTeamMember}
                searchPlaceholder="Search team members..."
                multiSelect={true}
                showPMControls={true}
                pmId={formData.pm_id}
                onSetPM={(agentId) => setFormData(prev => ({ ...prev, pm_id: agentId }))}
              />
            </div>

            {/* Project Settings Column */}
            <div className="flex lg:w-1/2 flex-col">
              <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-4 min-h-0">
                <div>
                  <label className="block type-label text-gray-700 mb-1">
                    Project Name <span className="text-red-600">*</span>
                  </label>
                  <Input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder={isMobile ? "" : "My Project"}
                    required
                  />
                </div>

                <div>
                  <label className="block type-label text-gray-700 mb-1">
                    Description
                  </label>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder={isMobile ? "" : "What is this project about?"}
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block type-label text-gray-700 mb-1">
                    Project Path {project ? '' : '(Optional)'}
                  </label>
                  <Input
                    type="text"
                    value={formData.path}
                    onChange={(e) => setFormData({ ...formData, path: e.target.value })}
                    className="font-mono text-base md:text-sm"
                    placeholder="Leave empty to auto-generate in ~/.kumiai/projects/"
                    disabled={!!project}
                  />
                  {project && (
                    <p className="type-caption text-gray-500 mt-1">
                      Project path cannot be changed after creation
                    </p>
                  )}
                </div>

                <div className="flex-1 flex flex-col min-h-0">
                  <label className="block type-label text-gray-700 mb-2">
                    Selected Team ({formData.team_member_ids.length}{formData.pm_id ? ', 1 PM' : ''})
                  </label>
                  {formData.team_member_ids.length === 0 ? (
                    <div className="flex-1 flex items-center justify-center rounded-lg border-2 border-dashed border-gray-300 min-h-0">
                      <div className="text-center text-gray-500">
                        <p className="type-body-sm">No team members selected</p>
                        <p className="type-caption text-gray-400 mt-1">Select members from the left panel</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex-1 overflow-y-auto space-y-1.5 p-2 bg-gray-50 rounded-lg border border-gray-200 min-h-0">
                      {formData.team_member_ids.map((agentId) => {
                        const agent = agents.find(a => a.id === agentId);
                        if (!agent) return null;
                        const isPM = formData.pm_id === agentId;
                        return (
                          <div
                            key={agentId}
                            className="relative p-2 rounded-md border border-gray-200 bg-white hover:border-gray-300 transition-all"
                          >
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleTeamMember(agentId);
                              }}
                              className="absolute top-1.5 right-1.5 w-4 h-4 bg-white hover:bg-red-500 rounded-full flex items-center justify-center border border-gray-300 hover:border-red-500 transition-all shadow-sm group z-10"
                              title="Remove from team"
                              type="button"
                            >
                              <Plus className="w-2.5 h-2.5 text-gray-600 group-hover:text-white rotate-45 transition-colors" />
                            </button>
                            <div className="flex items-center gap-2">
                              <Avatar seed={agent.id} size={32} className="w-8 h-8 flex-shrink-0" color={agent.icon_color} />
                              <div className="flex-1 min-w-0 pr-5">
                                <div className="flex items-center gap-1.5">
                                  <div className="type-body-sm font-medium text-gray-900 truncate">
                                    {agent.name}
                                  </div>
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
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="px-4 py-4 flex justify-center">
                <ModalActionButton
                  type="submit"
                  onClick={() => {}}
                  disabled={!formData.name.trim()}
                  icon={Plus}
                >
                  {project ? 'Save Changes' : 'Create Project'}
                </ModalActionButton>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
