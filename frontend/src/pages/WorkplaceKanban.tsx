import { useState, useEffect, useRef, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Search, FolderOpen, Trash2, ChevronLeft, ChevronRight, Pencil, Folder, Briefcase, LayoutGrid, Table2 } from 'lucide-react';
import { LoadingState, EmptyState } from '@/components/ui';
import { api, type Agent, type AgentInstance, type Project, type SkillMetadata } from '@/lib/api';
import { KanbanCard } from '@/components/features/kanban';
import { UnifiedChatSessionModal } from '@/components/features/sessions';
import { PMChat } from '@/components/features/chat';
import { ProjectCard, ProjectsList } from '@/components/features/projects';
import { Avatar } from '@/ui';
import { Input } from '@/components/ui/primitives/input';
import { Textarea } from '@/components/ui/primitives/textarea';
import { Button } from '@/components/ui/primitives/button';
import { ModalActionButton } from '@/ui';
import { ProjectModal } from '@/components/modals';
import { MainLayout } from '@/components/layout';
import { MainHeader } from '@/components/layout';
import { SidebarNav } from '@/components/layout';
import { SidebarFooter } from '@/components/layout';
import { FileViewerModal } from '@/components/features/files';
import { SessionListMobile, SessionsTable } from '@/components/features/sessions';
import { MobileHeader } from '@/components/layout';
import { AgentSelectorPanel } from '@/components/features/agents';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/primitives/toggle-group';
import { cn, layout } from '@/styles/design-system';
import { getSkillIcon } from '@/constants/skillIcons';
import type { ChatContext } from '@/types/chat';
import { paths } from '@/lib/utils/config';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import {
  DndContext,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  pointerWithin,
  useDroppable,
} from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useIsMobile } from '@/hooks';

// Workflow stage column configuration
const COLUMNS = [
  { id: 'backlog', label: 'Backlog', color: 'bg-gray-50' },
  { id: 'active', label: 'Active', color: 'bg-orange-100 dark:bg-orange-900/30' },
  { id: 'waiting', label: 'Waiting', color: 'bg-gray-100' },
  { id: 'done', label: 'Done', color: 'bg-green-100 dark:bg-green-900/30' },
] as const;

type ColumnId = typeof COLUMNS[number]['id'];

// Draggable card wrapper
function DraggableCard({
  agent,
  agentDefinitions,
  onClick,
  onDelete,
  fileBasedAgents
}: {
  agent: AgentInstance;
  agentDefinitions: Agent[];
  onClick: () => void;
  onDelete?: (agentId: string) => void;
  fileBasedAgents?: Agent[];
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: agent.instance_id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <KanbanCard
        agent={agent}
        agentDefinitions={agentDefinitions}
        onClick={onClick}
        onDelete={onDelete}
        dragListeners={listeners}
        fileBasedAgents={fileBasedAgents}
      />
    </div>
  );
}

interface WorkplaceKanbanProps {
  onChatContextChange?: (context: ChatContext) => void;
  currentProjectId?: string;
  onProjectChange?: (projectId: string) => void;
}

export default function WorkplaceKanban({ onChatContextChange, currentProjectId, onProjectChange }: WorkplaceKanbanProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentInstances, setAgentInstances] = useState<AgentInstance[]>([]);
  const [fileBasedAgents, setFileBasedAgents] = useState<Agent[]>([]);  // File-based agents for looking up colors
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<AgentInstance | null>(null);
  const [showSpawnDialog, setShowSpawnDialog] = useState(false);
  const [spawnDialogInitialStage, setSpawnDialogInitialStage] = useState<string>('backlog');
  const [showCreateProjectDialog, setShowCreateProjectDialog] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);

  // Project management state
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [projectSearchQuery, setProjectSearchQuery] = useState('');
  const [projectsReloadTrigger, setProjectsReloadTrigger] = useState(0);

  // Get session ID from URL
  const sessionIdFromUrl = searchParams.get('session');

  // File explorer state
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  // Use workspace store for view state management
  const viewMode = useWorkspaceStore((state) => state.viewMode);
  const setViewMode = useWorkspaceStore((state) => state.setViewMode);
  const boardViewMode = useWorkspaceStore((state) => state.boardViewMode);
  const setBoardViewMode = useWorkspaceStore((state) => state.setBoardViewMode);
  const isPMExpanded = useWorkspaceStore((state) => state.isPMExpanded);
  const setPMExpanded = useWorkspaceStore((state) => state.setPMExpanded);

  // Handle Esc key to close session
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && viewMode === 'chat' && selectedAgent) {
        setSelectedAgent(null);
        setViewMode('kanban');
        updateSessionInUrl(null);
      }
    };

    window.addEventListener('keydown', handleEscKey);
    return () => window.removeEventListener('keydown', handleEscKey);
  }, [viewMode, selectedAgent]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  // Load agents and projects on mount only
  useEffect(() => {
    api.getAgents().then(agents => {
      setAgents(agents);
      setFileBasedAgents(agents);
    }).catch(error => {
      console.error('[FRONTEND] Failed to load agents:', error);
    });

    // Load projects from API
    api.getProjects().then(fetchedProjects => {
      setProjects(fetchedProjects);
      // Auto-select based on currentProjectId or first project
      if (fetchedProjects.length > 0) {
        const projectToSelect = currentProjectId
          ? fetchedProjects.find(p => p.id === currentProjectId) || fetchedProjects[0]
          : fetchedProjects[0];
        setSelectedProject(projectToSelect);
      }
      setProjectsLoading(false);
    }).catch(error => {
      console.error('[FRONTEND] Failed to load projects:', error);
      setProjectsLoading(false);
    });
  }, []);

  // Load sessions when currentProjectId changes (on mount and when switching projects)
  useEffect(() => {
    // Load sessions - filter by current project to avoid mixing PM sessions
    const loadSessions = currentProjectId
      ? api.getSessions(currentProjectId)
      : api.getSessions();

    loadSessions.then(sessions => {
      // Defensive: ensure sessions is an array
      const sessionsArray = Array.isArray(sessions) ? sessions : [];
      if (!Array.isArray(sessions)) {
        console.warn('[FRONTEND] getSessions returned non-array:', sessions);
      }
      setAgentInstances(sessionsArray);
      setSessionsLoading(false);
    }).catch(error => {
      console.error('[FRONTEND] Failed to load sessions:', error);
      setAgentInstances([]); // Set empty array on error
      setSessionsLoading(false);
    });

    // Poll for task updates - filter by current project to avoid mixing PM sessions
    const interval = setInterval(() => {
      if (currentProjectId) {
        api.getSessions(currentProjectId).then(sessions => {
          setAgentInstances(sessions);
        });
      } else {
        api.getSessions().then(sessions => {
          setAgentInstances(sessions);
        });
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [currentProjectId]);

  // Update selectedProject when currentProjectId prop changes
  useEffect(() => {
    if (currentProjectId && projects.length > 0) {
      const project = projects.find(p => p.id === currentProjectId);
      if (project && project.id !== selectedProject?.id) {
        setSelectedProject(project);
        // Note: Session remains open when switching projects to allow
        // continued streaming/interaction with sessions from other projects
      }
    }
  }, [currentProjectId, projects]);

  // Sync selectedAgent with updated agent data from polling
  useEffect(() => {
    if (selectedAgent) {
      const updatedAgent = agentInstances.find(a => a.instance_id === selectedAgent.instance_id);
      if (updatedAgent) {
        // Update agent data (allow cross-project sessions to remain open)
        setSelectedAgent(updatedAgent);
      }
    }
  }, [agentInstances, selectedAgent]);

  // Restore selected session from URL on mount or when agentInstances load
  useEffect(() => {
    if (sessionIdFromUrl && agentInstances.length > 0 && !selectedAgent) {
      const sessionToRestore = agentInstances.find(a => a.instance_id === sessionIdFromUrl);
      // Only restore if the session belongs to the currently selected project
      if (sessionToRestore && (!selectedProject || sessionToRestore.project_id === selectedProject.id)) {
        setSelectedAgent(sessionToRestore);
        setViewMode('chat');
      } else if (sessionToRestore && selectedProject && sessionToRestore.project_id !== selectedProject.id) {
        // Session is from a different project, clear it from URL
        updateSessionInUrl(null);
      }
    }
  }, [sessionIdFromUrl, agentInstances, selectedProject]);

  // Update URL when session selection changes
  const updateSessionInUrl = (sessionId: string | null) => {
    const params = new URLSearchParams(searchParams);
    if (sessionId) {
      params.set('session', sessionId);
    } else {
      params.delete('session');
    }
    if (currentProjectId) {
      params.set('project', currentProjectId);
    }
    setSearchParams(params, { replace: true });
  };

  // Detect PM session and set chat context
  useEffect(() => {
    if (!onChatContextChange || !selectedProject) {
      return;
    }

    // Find PM session for the selected project
    // IMPORTANT: Double-check project_id to prevent mixing PM sessions between projects
    const pmSession = agentInstances.find(agent =>
      agent.role === 'pm' &&
      agent.project_id === selectedProject.id
    );

    if (pmSession) {
      // Extra safety check: Ensure PM session belongs to current project
      if (pmSession.project_id !== selectedProject.id) {
        console.warn('[WorkplaceKanban] PM session project_id mismatch:', {
          pmSessionProjectId: pmSession.project_id,
          selectedProjectId: selectedProject.id
        });
        return;
      }

      // PM exists for this project - set context
      onChatContextChange({
        role: 'pm',
        name: `PM for ${selectedProject.name}`,
        description: `Project Manager for ${selectedProject.name}. The PM coordinates multi-agent workflows, spawns specialist sessions, manages project status, and tracks progress through the kanban board.`,
        data: {
          project_path: selectedProject.path,
          project_id: selectedProject.id,
          pm_session_id: pmSession.instance_id,
        },
      });
    } else {
      // No PM session found - should have been auto-created when project was created
      // Clear context
      onChatContextChange({
        role: null,
      });
    }
  }, [agentInstances, selectedProject, onChatContextChange]);

  // Filter agent instances by selected project (exclude PM sessions)
  // Defensive: ensure agentInstances is always an array before filtering
  const projectAgents = selectedProject
    ? (Array.isArray(agentInstances) ? agentInstances : []).filter(agent =>
        agent.project_id === selectedProject.id &&
        agent.role !== 'pm'  // Filter out PM sessions - they appear in sidebar
      )
    : [];

  // Group agent instances by kanban stage (default to 'backlog' if not set)
  // Defensive: ensure agentInstances is array
  const safeAgents = Array.isArray(agentInstances) ? agentInstances : [];
  const agentsByStage = COLUMNS.reduce((acc, col) => {
    acc[col.id] = projectAgents.filter(a => (a.kanban_stage || 'backlog') === col.id);
    return acc;
  }, {} as Record<ColumnId, AgentInstance[]>);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    // Check if dropped on a column
    const overId = over.id as string;
    const targetColumn = COLUMNS.find(col => col.id === overId);

    if (targetColumn && active.id !== targetColumn.id) {
      try {
        // Optimistically update UI
        setAgentInstances(prev => prev.map(a =>
          a.instance_id === active.id
            ? { ...a, kanban_stage: targetColumn.id as ColumnId }
            : a
        ));

        // Call backend to persist the change
        await api.updateSessionStage(active.id as string, targetColumn.id);
      } catch (error) {
        console.error('Failed to update session stage:', error);
        // Revert on error
        api.getSessions().then(setAgentInstances);
      }
    }
  };

  const handleDragCancel = () => {
    setActiveId(null);
  };

  const handleDelete = async (agentId: string) => {
    if (!confirm('Are you sure you want to delete this session?')) {
      return;
    }

    try {
      await api.deleteSession(agentId);
      // Remove from local state
      setAgentInstances(prev => prev.filter(a => a.instance_id !== agentId));
      // Close modal if this agent is selected
      if (selectedAgent?.instance_id === agentId) {
        setSelectedAgent(null);
      }
    } catch (error) {
      console.error('Failed to delete agent:', error);
      alert('Failed to delete session. Please try again.');
    }
  };

  const handleDeleteProject = async (projectId: string, projectName: string) => {
    if (!confirm(`Are you sure you want to delete project "${projectName}"?\n\nThis will delete all sessions associated with this project.`)) {
      return;
    }

    try {
      // First, delete all sessions for this project
      const projectSessions = agentInstances.filter(a => a.project_id === projectId);
      await Promise.all(
        projectSessions.map(session => api.deleteSession(session.instance_id))
      );

      // Then delete the project itself
      await api.deleteProject(projectId);

      // Update local state
      setAgentInstances(prev => prev.filter(a => a.project_id !== projectId));
      setProjects(prev => prev.filter(p => p.id !== projectId));
      setProjectsReloadTrigger(prev => prev + 1); // Trigger reload

      // Clear selection if this project was selected
      if (selectedProject?.id === projectId) {
        setSelectedProject(projects.find(p => p.id !== projectId) || null);
      }
    } catch (error) {
      console.error('Failed to delete project:', error);
      alert('Failed to delete project. Please try again.');
    }
  };

  const activeAgent = activeId ? agentInstances.find(a => a.instance_id === activeId) : null;

  // Filter projects by search query
  const filteredProjects = projects.filter(project => {
    if (!projectSearchQuery) return true;
    const query = projectSearchQuery.toLowerCase();
    return (
      project.name.toLowerCase().includes(query) ||
      (project.description && project.description.toLowerCase().includes(query))
    );
  });

  // Common handler for selecting/opening projects
  const handleProjectSelection = (projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    if (project) {
      setSelectedProject(project);
      setSelectedAgent(null);
      setViewMode('kanban');
      setPMExpanded(false); // FIX: Reset PM expansion when switching projects
      updateSessionInUrl(null);
      if (onProjectChange) {
        onProjectChange(project.id);
      }
    }
  };

  return (
    <MainLayout
      leftSidebarNav={<SidebarNav />}
      leftSidebarContent={
        <ProjectsList
          currentProjectId={selectedProject?.id}
          reloadTrigger={projectsReloadTrigger}
          onSelectProject={handleProjectSelection}
          onOpenProject={handleProjectSelection}
          onCreateProject={() => setShowCreateProjectDialog(true)}
          onEditProject={(project) => setEditingProject(project)}
          onDeleteProject={(projectId) => {
            const project = projects.find(p => p.id === projectId);
            if (project) {
              handleDeleteProject(projectId, project.name);
            }
          }}
          onUnarchiveProject={() => {}} // Not used in WorkplaceKanban
          onPermanentDeleteProject={() => {}} // Not used in WorkplaceKanban
        />
      }
      leftSidebarFooter={<SidebarFooter />}
      rightSidebarContent={
        !isPMExpanded && selectedProject ? (
          <PMChat
            key={selectedProject.id}
            isOpen={true}
            onToggle={() => {}}
            projectId={selectedProject.id}
            projectPath={selectedProject.path}
            projectName={selectedProject.name}
            onSessionJump={(sessionId) => {
              // Find the session in agentInstances list
              const targetAgent = agentInstances.find(a => a.instance_id === sessionId);
              if (targetAgent) {
                setSelectedAgent(targetAgent);
                setViewMode('chat');
                updateSessionInUrl(sessionId);
              } else {
                console.warn(`[WorkplaceKanban] Session ${sessionId} not found in agentInstances list`);
              }
            }}
            className="bg-gray-50"
            isExpanded={false}
            onToggleExpand={() => setPMExpanded(true)}
          />
        ) : undefined
      }
    >
      {({ leftSidebarOpen, rightSidebarOpen, toggleLeftSidebar, toggleRightSidebar }) => (
        <>
          <div className="flex-1 flex overflow-hidden bg-white relative">
            {/* When PM is expanded, it takes over the entire center+right area */}
            {isPMExpanded && selectedProject ? (
              <div className="flex-1 flex flex-col bg-white overflow-hidden">
                <PMChat
                  key={selectedProject.id}
                  isOpen={true}
                  onToggle={() => {}}
                  projectId={selectedProject.id}
                  projectPath={selectedProject.path}
                  projectName={selectedProject.name}
                  onSessionJump={(sessionId) => {
                    const targetAgent = agentInstances.find(a => a.instance_id === sessionId);
                    if (targetAgent) {
                      setSelectedAgent(targetAgent);
                      setViewMode('chat');
                      setPMExpanded(false);
                      updateSessionInUrl(sessionId);
                    }
                  }}
                  className="bg-white"
                  isExpanded={true}
                  onToggleExpand={() => setPMExpanded(false)}
                />
              </div>
            ) : (
              <>
                {/* Center: Kanban Board or Chat Session */}
                <div className="flex-1 flex flex-col bg-white overflow-hidden max-w-full">
                  {viewMode === 'chat' && selectedAgent ? (
                    // Show chat session inline
                    <>
                      <MainHeader
                        breadcrumb={selectedProject?.name || "Project"}
                        title={selectedAgent.current_session_description || selectedAgent.context?.description || selectedAgent.context?.task_description || selectedAgent.session_id || "New Session"}
                        showBackButton={true}
                        onBack={() => {
                          setSelectedAgent(null);
                          setViewMode('kanban');
                          updateSessionInUrl(null);
                        }}
                        leftSidebarOpen={leftSidebarOpen}
                        onToggleLeftSidebar={toggleLeftSidebar}
                        rightSidebarOpen={rightSidebarOpen}
                        onToggleRightSidebar={toggleRightSidebar}
                      />
                      <div className="flex-1 overflow-hidden">
                        <UnifiedChatSessionModal
                          agent={selectedAgent}
                          agents={agents}
                          onClose={() => {
                            setSelectedAgent(null);
                            setViewMode('kanban');
                            updateSessionInUrl(null);
                          }}
                          onSessionJump={(sessionId) => {
                            // Find the session in agentInstances list
                            const targetAgent = agentInstances.find(a => a.instance_id === sessionId);
                            if (targetAgent) {
                              setSelectedAgent(targetAgent);
                              setViewMode('chat');
                            }
                          }}
                          inline={true}
                        />
                      </div>
                    </>
                  ) : projectsLoading && currentProjectId ? (
                    // Loading project
                    <LoadingState message="Loading project..." />
                  ) : selectedProject && viewMode === 'kanban' ? (
                    <>
                      <MainHeader
                        title={selectedProject.name}
                        leftSidebarOpen={leftSidebarOpen}
                        onToggleLeftSidebar={toggleLeftSidebar}
                        rightSidebarOpen={rightSidebarOpen}
                        onToggleRightSidebar={toggleRightSidebar}
                        actions={
                          <div className="hidden lg:flex items-center gap-3">
                            {/* Edit Project Button */}
                            <button
                              onClick={() => setEditingProject(selectedProject)}
                              className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-white hover:bg-gray-50 transition-colors text-gray-700 text-sm font-medium border border-gray-300"
                              title="Edit project"
                            >
                              <Pencil className="w-4 h-4" />
                              <span>Edit Project</span>
                            </button>

                            {/* New Session Button */}
                            <button
                              onClick={() => {
                                setSpawnDialogInitialStage('backlog');
                                setShowSpawnDialog(true);
                              }}
                              className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-black hover:bg-gray-800 transition-colors text-white text-sm font-medium"
                              title="Create new session"
                            >
                              <Plus className="w-4 h-4" />
                              <span>New Session</span>
                            </button>

                            {/* View Toggle */}
                            <ToggleGroup
                              type="single"
                              value={boardViewMode}
                              onValueChange={(value) => {
                                if (value) setBoardViewMode(value as 'kanban' | 'table');
                              }}
                              className="border rounded-lg bg-white"
                            >
                              <ToggleGroupItem value="kanban" aria-label="Kanban view" className="gap-2">
                                <LayoutGrid className="h-4 w-4" />
                                <span className="text-sm">Board</span>
                              </ToggleGroupItem>
                              <ToggleGroupItem value="table" aria-label="Table view" className="gap-2">
                                <Table2 className="h-4 w-4" />
                                <span className="text-sm">Table</span>
                              </ToggleGroupItem>
                            </ToggleGroup>
                          </div>
                        }
                      />

                      {/* Mobile: Session List View */}
                      <div className="flex-1 lg:hidden overflow-hidden">
                        <SessionListMobile
                          sessions={projectAgents}
                          agents={agents}
                          selectedSessionId={selectedAgent?.instance_id}
                          onSessionSelect={(agent) => {
                            setSelectedAgent(agent);
                            setViewMode('chat');
                            updateSessionInUrl(agent.instance_id);
                          }}
                          onSessionDelete={handleDelete}
                          onSessionCreate={() => {
                            setSpawnDialogInitialStage('backlog');
                            setShowSpawnDialog(true);
                          }}
                          loading={sessionsLoading}
                          fileBasedAgents={fileBasedAgents}
                        />
                      </div>

                      {/* Desktop: Kanban Board or Table View */}
                      <div className="hidden lg:block flex-1 overflow-hidden">
                        {boardViewMode === 'kanban' ? (
                          <div className="h-full overflow-x-auto overflow-y-hidden pl-6 pt-2 pb-6">
                            <DndContext
                              sensors={sensors}
                              collisionDetection={pointerWithin}
                              onDragStart={handleDragStart}
                              onDragEnd={handleDragEnd}
                              onDragCancel={handleDragCancel}
                            >
                              <div className="flex gap-4 h-full w-full pr-6">
                                {COLUMNS.map((column, index) => (
                                  <KanbanColumn
                                    key={column.id}
                                    column={column}
                                    agents={agentsByStage[column.id]}
                                    agentDefinitions={agents}
                                    onCardClick={(agent) => {
                                      setSelectedAgent(agent);
                                      setViewMode('chat');
                                      updateSessionInUrl(agent.instance_id);
                                    }}
                                    onDeleteCard={handleDelete}
                                    isLast={index === COLUMNS.length - 1}
                                    fileBasedAgents={fileBasedAgents}
                                  />
                                ))}
                              </div>

                              <DragOverlay>
                                {activeAgent ? (
                                  <div className="opacity-80">
                                    <KanbanCard
                                      agent={activeAgent}
                                      agentDefinitions={agents}
                                      onClick={() => {}}
                                      fileBasedAgents={fileBasedAgents}
                                    />
                                  </div>
                                ) : null}
                              </DragOverlay>
                            </DndContext>
                          </div>
                        ) : (
                          <div className="h-full overflow-hidden pl-6 pr-6 pt-2 pb-6">
                            <SessionsTable
                              sessions={projectAgents}
                              agents={agents}
                              onSessionSelect={(agent) => {
                                setSelectedAgent(agent);
                                setViewMode('chat');
                                updateSessionInUrl(agent.instance_id);
                              }}
                              fileBasedAgents={fileBasedAgents}
                            />
                          </div>
                        )}
                      </div>
                    </>
                  ) : projectsLoading ? (
                    // Loading initial projects
                    <LoadingState message="Loading..." />
                  ) : (
                    // No project selected
                    <EmptyState
                      icon={FolderOpen}
                      title="No project selected"
                      description="Use Cmd/Ctrl + P to select a project"
                      centered
                    />
                  )}
                </div>
              </>
            )}
          </div>

          {/* Modals - Positioned absolutely, outside flex layout */}
          <AnimatePresence>
            {showSpawnDialog && (
              <SpawnDialog
                selectedProject={selectedProject}
                initialStage={spawnDialogInitialStage}
                onClose={() => setShowSpawnDialog(false)}
                onSpawn={(agent) => {
                  setAgentInstances([...agentInstances, agent]);
                  // Auto-open if created in active stage
                  if (agent.kanban_stage === 'active') {
                    setSelectedAgent(agent);
                    setViewMode('chat');
                    updateSessionInUrl(agent.instance_id);
                  }
                  setShowSpawnDialog(false);
                }}
              />
            )}
          </AnimatePresence>

          {showCreateProjectDialog && (
            <ProjectModal
              project={null}
              onClose={() => setShowCreateProjectDialog(false)}
              onSave={async (data) => {
                try {
                  const project = await api.createProject(data as any);
                  setProjects([...projects, project]);
                  setSelectedProject(project);

                  // Close any open session and show kanban/table view
                  setSelectedAgent(null);
                  setViewMode('kanban');
                  updateSessionInUrl(null);
                  setPMExpanded(false);

                  setShowCreateProjectDialog(false);
                  setProjectsReloadTrigger(prev => prev + 1); // Trigger reload
                  if (onProjectChange) {
                    onProjectChange(project.id);
                  }
                } catch (error) {
                  alert('Failed to create project: ' + error);
                }
              }}
            />
          )}

          {editingProject && (
            <ProjectModal
              project={editingProject}
              onClose={() => setEditingProject(null)}
              onSave={async (data) => {
                try {
                  const updatedProject = await api.updateProject(editingProject.id, data as any);
                  setProjects(projects.map(p => p.id === updatedProject.id ? updatedProject : p));
                  if (selectedProject?.id === updatedProject.id) {
                    setSelectedProject(updatedProject);
                  }
                  setProjectsReloadTrigger(prev => prev + 1); // Trigger reload
                  setEditingProject(null);
                } catch (error) {
                  alert('Failed to update project: ' + error);
                }
              }}
            />
          )}

          {/* File Viewer Modal */}
          <FileViewerModal
            mode={selectedAgent ? 'session' : 'project'}
            projectId={selectedProject?.id}
            sessionId={selectedAgent?.instance_id}
            filePath={selectedFile}
            onClose={() => setSelectedFile(null)}
          />
        </>
      )}
    </MainLayout>
  );
}

// Kanban Column Component
function KanbanColumn({
  column,
  agents,
  agentDefinitions,
  onCardClick,
  onDeleteCard,
  isLast,
  fileBasedAgents,
}: {
  column: typeof COLUMNS[number];
  agents: AgentInstance[];
  agentDefinitions: Agent[];
  onCardClick: (agent: AgentInstance) => void;
  onDeleteCard?: (agentId: string) => void;
  isLast?: boolean;
  fileBasedAgents?: Agent[];
}) {
  const { setNodeRef, isOver } = useDroppable({ id: column.id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex flex-col flex-1 min-w-[260px] bg-white rounded-lg border shadow-sm transition-all",
        isOver ? "border-primary bg-muted/50" : "border-gray-200",
        isLast && "mr-6"
      )}
    >
      {/* Column Header */}
      <div className={`p-2 rounded-t-lg border-b border-gray-200 ${column.color}`}>
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-sm text-gray-700">{column.label}</h4>
          <span className="type-caption font-medium text-gray-600 bg-white px-2 py-0.5 rounded-full">
            {agents.length}
          </span>
        </div>
      </div>

      {/* Cards - Full height droppable area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-[200px]">
        <SortableContext
          items={agents.map(a => a.instance_id)}
          strategy={verticalListSortingStrategy}
        >
          {agents.length === 0 ? (
            <div className="text-center text-gray-400 text-sm py-8">
            </div>
          ) : (
            agents.map((agent) => (
              <DraggableCard
                key={agent.instance_id}
                agent={agent}
                agentDefinitions={agentDefinitions}
                onClick={() => onCardClick(agent)}
                onDelete={onDeleteCard}
                fileBasedAgents={fileBasedAgents}
              />
            ))
          )}
        </SortableContext>
      </div>
    </div>
  );
}

// Spawn Dialog - full implementation from original Workplace
function SpawnDialog({
  selectedProject,
  initialStage = 'backlog',
  onClose,
  onSpawn,
}: {
  selectedProject: Project | null;
  initialStage?: string;
  onClose: () => void;
  onSpawn: (agent: AgentInstance) => void;
}) {
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');  // Changed to single agent selection
  const [sessionDescription, setSessionDescription] = useState('');
  const [kanbanStage, setKanbanStage] = useState(initialStage);
  const [spawning, setSpawning] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);  // Load agents from file system
  const [skills, setSkills] = useState<SkillMetadata[]>([]);
  const isMobile = useIsMobile();

  // Load agents and skills on mount
  useEffect(() => {
    api.getAgents().then(setAgents).catch(console.error);
    api.getSkills().then(setSkills).catch(console.error);
  }, []);

  // Handle Esc key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Filter agents to only show those belonging to the current project
  const projectAgents = useMemo(() => {
    if (!selectedProject) return agents;

    const allowedAgentIds = new Set([
      ...(selectedProject.team_member_ids || []),
      ...(selectedProject.pm_agent_id ? [selectedProject.pm_agent_id] : []),
    ]);

    return agents.filter(agent => allowedAgentIds.has(agent.id));
  }, [agents, selectedProject]);

  const handleToggleAgent = (agentId: string) => {
    // Single selection - just set the selected agent
    setSelectedAgentId(agentId === selectedAgentId ? '' : agentId);
  };

  const handleSpawn = async () => {
    if (!selectedAgentId || !sessionDescription) return;

    console.log('[FRONTEND] Creating session with agent:', selectedAgentId);
    setSpawning(true);
    try {
      // Use the new createSession API
      const payload = {
        agent_id: selectedAgentId,
        project_id: selectedProject?.id,
        session_type: 'specialist',  // Default to specialist type
        context: {
          description: sessionDescription,
          kanban_stage: kanbanStage,
          project_path: selectedProject?.path || paths.projectRoot,
        },
      };
      console.log('[FRONTEND] Sending payload:', payload);
      const session = await api.createSession(payload);
      onSpawn(session);
    } catch (error) {
      alert('Failed to launch session: ' + error);
    } finally {
      setSpawning(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-0 lg:p-4" onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} className="bg-white rounded-none lg:rounded-lg shadow-xl max-w-6xl w-full h-full lg:h-[70vh] flex flex-col">
        {/* Header */}
        <div className="px-4 lg:px-6 py-2.5 lg:py-3 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">New session</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5 text-gray-500 rotate-45" />
          </button>
        </div>

        {/* Two-column layout */}
        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          {/* Left: Agent Selector */}
          <div className="flex lg:w-1/2 border-b lg:border-b-0 lg:border-r border-gray-200 flex-col" style={{ maxHeight: isMobile ? '40vh' : 'auto' }}>
            <AgentSelectorPanel
              agents={projectAgents}
              skills={skills}
              selectedAgentIds={selectedAgentId ? [selectedAgentId] : []}
              onToggleAgent={handleToggleAgent}
              searchPlaceholder="Search agents..."
              multiSelect={false}
            />
          </div>

          {/* Right: Configuration */}
          <div className="flex lg:w-1/2 flex-col">
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Session Description */}
              <div>
                <label className="block type-label text-gray-700 mb-1.5">
                  Session Description <span className="text-red-500">*</span>
                </label>
                <Textarea
                  value={sessionDescription}
                  onChange={(e) => setSessionDescription(e.target.value)}
                  placeholder="What should this agent do?"
                  rows={6}
                  className="px-4 py-2 resize-none"
                />
              </div>

              {/* Selected Agent */}
              <div>
                <label className="block type-label text-gray-700 mb-2">
                  Selected Agent
                  {selectedAgentId && (
                    <span className="ml-2 type-caption px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                      Specialist
                    </span>
                  )}
                </label>
                <div className="h-[88px]">
                  {!selectedAgentId ? (
                    <div className="h-full flex items-center justify-center rounded-lg border-2 border-dashed border-gray-300">
                      <div className="text-center text-gray-500">
                        <p className="type-body-sm">No agent selected</p>
                        <p className="type-caption text-gray-400 mt-1">Select an agent from the left panel</p>
                      </div>
                    </div>
                  ) : (
                    <div className="h-full p-3 bg-gray-50 rounded-lg border border-gray-200">
                      {(() => {
                        const selectedAgent = agents.find(a => a.id === selectedAgentId);
                        if (!selectedAgent) return null;
                        return (
                          <div className="relative h-full rounded-lg border border-gray-200 bg-white p-3">
                            <button
                              onClick={() => setSelectedAgentId('')}
                              className="absolute top-2 right-2 w-5 h-5 bg-white hover:bg-red-500 rounded-full flex items-center justify-center border border-gray-300 hover:border-red-500 transition-all shadow-sm group z-10"
                              title="Deselect agent"
                            >
                              <Plus className="w-3 h-3 text-gray-600 group-hover:text-white rotate-45 transition-colors" />
                            </button>
                            <div className="flex items-start gap-3">
                              <Avatar seed={selectedAgent.name} size={40} className="w-10 h-10 flex-shrink-0" color={selectedAgent.icon_color || '#4A90E2'} />
                              <div className="flex-1 min-w-0 pr-6">
                                <div className="type-subtitle text-gray-900 truncate">
                                  {selectedAgent.name}
                                </div>
                                <div className="type-caption text-gray-500 line-clamp-2 mt-0.5">
                                  {selectedAgent.description || 'No description'}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-4 py-4 flex justify-center">
              <ModalActionButton
                type="button"
                onClick={handleSpawn}
                disabled={!selectedAgentId || !sessionDescription || spawning}
                icon={Plus}
              >
                {spawning ? 'Creating...' : 'Create Session'}
              </ModalActionButton>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
