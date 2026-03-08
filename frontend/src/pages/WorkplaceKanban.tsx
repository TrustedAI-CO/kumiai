import { useState, useEffect, useRef, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Search, FolderOpen, Trash2, ChevronLeft, ChevronRight, Folder, Briefcase } from 'lucide-react';
import { LoadingState, EmptyState } from '@/components/ui';
import { api, type Agent, type AgentInstance, type Project, type SkillMetadata } from '@/lib/api';
import { UnifiedChatSessionModal } from '@/components/features/sessions';
import { PMChat } from '@/components/features/chat';
import { ProjectCard, ProjectsList, ProjectHeaderActions } from '@/components/features/projects';
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
import { useTasks, useUpdateTask, useDeleteTask } from '@/hooks/queries/useTasks';
import { TaskKanbanCard, TaskCreateModal } from '@/components/features/tasks';
import type { Task, TaskStatus } from '@/types/task';

// Task status column configuration
const TASK_COLUMNS = [
  { id: 'open', label: 'Open', color: 'bg-gray-50' },
  { id: 'in_progress', label: 'In Progress', color: 'bg-blue-50' },
  { id: 'done', label: 'Done', color: 'bg-green-50' },
  { id: 'archived', label: 'Archived', color: 'bg-slate-50' },
] as const;

type TaskColumnId = typeof TASK_COLUMNS[number]['id'];

// Draggable wrapper for task cards
function DraggableTaskCard({
  task,
  sessionCount,
  onClick,
  onDelete,
}: {
  task: Task;
  sessionCount: number;
  onClick: () => void;
  onDelete?: (taskId: string) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <TaskKanbanCard
        task={task}
        sessionCount={sessionCount}
        onClick={onClick}
        onDelete={onDelete}
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
  const [fileBasedAgents, setFileBasedAgents] = useState<Agent[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<AgentInstance | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [showSpawnDialog, setShowSpawnDialog] = useState(false);
  const [spawnDialogInitialTaskId, setSpawnDialogInitialTaskId] = useState<string | undefined>(undefined);
  const [showCreateProjectDialog, setShowCreateProjectDialog] = useState(false);
  const [showCreateTaskModal, setShowCreateTaskModal] = useState(false);
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

  // Tasks for the current project
  const { data: projectTasks = [] } = useTasks(selectedProject?.id);
  const updateTask = useUpdateTask(selectedProject?.id || '');
  const deleteTask = useDeleteTask(selectedProject?.id || '');

  // Handle Esc key to close session
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && viewMode === 'chat' && selectedAgent) {
        setSelectedAgent(null);
        setViewMode(selectedTaskId ? 'task-sessions' : 'kanban');
        updateSessionInUrl(null);
      } else if (event.key === 'Escape' && viewMode === 'task-sessions') {
        closeTask();
      }
    };

    window.addEventListener('keydown', handleEscKey);
    return () => window.removeEventListener('keydown', handleEscKey);
  }, [viewMode, selectedAgent, selectedTaskId]);

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

    api.getProjects().then(fetchedProjects => {
      setProjects(fetchedProjects);
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

  // Load sessions when currentProjectId changes
  useEffect(() => {
    const loadSessions = currentProjectId
      ? api.getSessions(currentProjectId)
      : api.getSessions();

    loadSessions.then(sessions => {
      const sessionsArray = Array.isArray(sessions) ? sessions : [];
      if (!Array.isArray(sessions)) {
        console.warn('[FRONTEND] getSessions returned non-array:', sessions);
      }
      setAgentInstances(sessionsArray);
      setSessionsLoading(false);
    }).catch(error => {
      console.error('[FRONTEND] Failed to load sessions:', error);
      setAgentInstances([]);
      setSessionsLoading(false);
    });

    let interval: NodeJS.Timeout | null = null;

    const startPolling = () => {
      if (interval) clearInterval(interval);
      interval = setInterval(() => {
        const req = currentProjectId ? api.getSessions(currentProjectId) : api.getSessions();
        req.then(sessions => {
          setAgentInstances(sessions);
        }).catch(error => {
          console.error('[WorkplaceKanban] Failed to poll sessions:', error);
        });
      }, 10000);
    };

    const stopPolling = () => {
      if (interval) { clearInterval(interval); interval = null; }
    };

    const handleVisibilityChange = () => {
      if (document.hidden) stopPolling(); else startPolling();
    };

    if (!document.hidden) startPolling();
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      stopPolling();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [currentProjectId]);

  // Update selectedProject when currentProjectId prop changes
  useEffect(() => {
    if (currentProjectId && projects.length > 0) {
      const project = projects.find(p => p.id === currentProjectId);
      if (project && project.id !== selectedProject?.id) {
        setSelectedProject(project);
      }
    }
  }, [currentProjectId, projects]);

  // Sync selectedAgent with updated agent data from polling
  useEffect(() => {
    if (selectedAgent) {
      const updatedAgent = agentInstances.find(a => a.instance_id === selectedAgent.instance_id);
      if (updatedAgent) {
        setSelectedAgent(updatedAgent);
      }
    }
  }, [agentInstances, selectedAgent]);

  // Restore selected session from URL on mount or when agentInstances load
  useEffect(() => {
    if (sessionIdFromUrl && agentInstances.length > 0 && !selectedAgent) {
      const sessionToRestore = agentInstances.find(a => a.instance_id === sessionIdFromUrl);
      if (sessionToRestore && (!selectedProject || sessionToRestore.project_id === selectedProject.id)) {
        setSelectedAgent(sessionToRestore);
        setViewMode('chat');
      } else if (sessionToRestore && selectedProject && sessionToRestore.project_id !== selectedProject.id) {
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
    if (!onChatContextChange || !selectedProject) return;

    const pmSession = agentInstances.find(agent =>
      agent.role === 'pm' &&
      agent.project_id === selectedProject.id
    );

    if (pmSession) {
      if (pmSession.project_id !== selectedProject.id) {
        console.warn('[WorkplaceKanban] PM session project_id mismatch:', {
          pmSessionProjectId: pmSession.project_id,
          selectedProjectId: selectedProject.id
        });
        return;
      }
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
      onChatContextChange({ role: null });
    }
  }, [agentInstances, selectedProject, onChatContextChange]);

  // Filter agent instances by selected project (exclude PM sessions)
  const projectAgents = selectedProject
    ? (Array.isArray(agentInstances) ? agentInstances : []).filter(agent =>
        agent.project_id === selectedProject.id &&
        agent.role !== 'pm'
      )
    : [];

  // Group tasks by status
  const tasksByStatus = useMemo(() =>
    TASK_COLUMNS.reduce((acc, col) => {
      acc[col.id] = projectTasks.filter(t => t.status === col.id);
      return acc;
    }, {} as Record<TaskColumnId, Task[]>),
    [projectTasks]
  );

  // Count sessions per task
  const sessionCountByTaskId = useMemo(() =>
    projectAgents.reduce((acc, session) => {
      if (session.task_id) {
        acc[session.task_id] = (acc[session.task_id] || 0) + 1;
      }
      return acc;
    }, {} as Record<string, number>),
    [projectAgents]
  );

  // Sessions not assigned to any task
  const unassignedSessions = useMemo(
    () => projectAgents.filter(s => !s.task_id),
    [projectAgents]
  );

  // Selected task
  const selectedTask = selectedTaskId
    ? projectTasks.find(t => t.id === selectedTaskId) ?? null
    : null;

  // Sessions for the selected task
  const selectedTaskSessions = selectedTask
    ? projectAgents.filter(a => a.task_id === selectedTask.id)
    : [];

  // Active task being dragged
  const activeTask = activeId ? projectTasks.find(t => t.id === activeId) : null;

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const targetColumn = TASK_COLUMNS.find(col => col.id === over.id);
    if (targetColumn && active.id !== targetColumn.id) {
      updateTask.mutate({
        taskId: active.id as string,
        req: { status: targetColumn.id as TaskColumnId },
      });
    }
  };

  const handleDragCancel = () => {
    setActiveId(null);
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session?')) return;

    try {
      await api.deleteSession(sessionId);
      setAgentInstances(prev => prev.filter(a => a.instance_id !== sessionId));
      if (selectedAgent?.instance_id === sessionId) {
        setSelectedAgent(null);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      alert('Failed to delete session. Please try again.');
    }
  };

  const handleDeleteProject = async (projectId: string, projectName: string) => {
    if (!confirm(`Are you sure you want to delete project "${projectName}"?\n\nThis will delete all sessions associated with this project.`)) {
      return;
    }

    try {
      const projectSessions = agentInstances.filter(a => a.project_id === projectId);
      await Promise.all(
        projectSessions.map(session => api.deleteSession(session.instance_id))
      );
      await api.deleteProject(projectId);
      setAgentInstances(prev => prev.filter(a => a.project_id !== projectId));
      setProjects(prev => prev.filter(p => p.id !== projectId));
      setProjectsReloadTrigger(prev => prev + 1);
      if (selectedProject?.id === projectId) {
        setSelectedProject(projects.find(p => p.id !== projectId) || null);
      }
    } catch (error) {
      console.error('Failed to delete project:', error);
      alert('Failed to delete project. Please try again.');
    }
  };

  const filteredProjects = projects.filter(project => {
    if (!projectSearchQuery) return true;
    const query = projectSearchQuery.toLowerCase();
    return (
      project.name.toLowerCase().includes(query) ||
      (project.description && project.description.toLowerCase().includes(query))
    );
  });

  const handleProjectSelection = (projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    if (project) {
      setSelectedProject(project);
      setSelectedAgent(null);
      setSelectedTaskId(null);
      setViewMode('kanban');
      setPMExpanded(false);
      updateSessionInUrl(null);
      if (onProjectChange) {
        onProjectChange(project.id);
      }
    }
  };

  const openTask = (taskId: string) => {
    setSelectedTaskId(taskId);
    setViewMode('task-sessions');
  };

  const closeTask = () => {
    setSelectedTaskId(null);
    setViewMode('kanban');
  };

  return (
    <MainLayout
      leftSidebarNav={<SidebarNav />}
      leftSidebarContent={
        <ProjectsList
          currentProjectId={selectedProject?.id}
          reloadTrigger={projectsReloadTrigger}
          onSelectProject={handleProjectSelection}
          onCreateProject={() => setShowCreateProjectDialog(true)}
          onDeleteProject={(projectId) => {
            const project = projects.find(p => p.id === projectId);
            if (project) {
              handleDeleteProject(projectId, project.name);
            }
          }}
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
                <div className="flex-1 flex flex-col bg-white overflow-hidden max-w-full">
                  {viewMode === 'chat' && selectedAgent ? (
                    <>
                      <MainHeader
                        breadcrumbs={
                          selectedTask
                            ? [
                                { label: selectedProject?.name || 'Project', onClick: () => { setSelectedAgent(null); closeTask(); updateSessionInUrl(null); } },
                                { label: selectedTask.name, onClick: () => { setSelectedAgent(null); setViewMode('task-sessions'); updateSessionInUrl(null); } },
                              ]
                            : [
                                { label: selectedProject?.name || 'Project', onClick: () => { setSelectedAgent(null); setViewMode('kanban'); updateSessionInUrl(null); } },
                              ]
                        }
                        title={selectedAgent.current_session_description || selectedAgent.context?.description || selectedAgent.context?.task_description || selectedAgent.session_id || 'New Session'}
                        showBackButton={true}
                        onBack={() => {
                          setSelectedAgent(null);
                          setViewMode(selectedTaskId ? 'task-sessions' : 'kanban');
                          updateSessionInUrl(null);
                        }}
                        leftSidebarOpen={leftSidebarOpen}
                        onToggleLeftSidebar={toggleLeftSidebar}
                        rightSidebarOpen={rightSidebarOpen}
                        onToggleRightSidebar={toggleRightSidebar}
                        actions={
                          <ProjectHeaderActions
                            viewMode="chat"
                            boardViewMode={boardViewMode}
                            onBoardViewModeChange={(v) => setBoardViewMode(v)}
                            onEditProject={() => selectedProject && setEditingProject(selectedProject)}
                          />
                        }
                      />
                      <div className="flex-1 overflow-hidden">
                        <UnifiedChatSessionModal
                          agent={selectedAgent}
                          agents={agents}
                          onClose={() => {
                            setSelectedAgent(null);
                            setViewMode(selectedTaskId ? 'task-sessions' : 'kanban');
                            updateSessionInUrl(null);
                          }}
                          onSessionJump={(sessionId) => {
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
                  ) : viewMode === 'task-sessions' && selectedTask ? (
                    <>
                      <MainHeader
                        breadcrumb={selectedProject?.name || 'Project'}
                        breadcrumbOnClick={closeTask}
                        title={selectedTask.name}
                        showBackButton={true}
                        onBack={closeTask}
                        leftSidebarOpen={leftSidebarOpen}
                        onToggleLeftSidebar={toggleLeftSidebar}
                        rightSidebarOpen={rightSidebarOpen}
                        onToggleRightSidebar={toggleRightSidebar}
                        actions={
                          <ProjectHeaderActions
                            viewMode="task-sessions"
                            boardViewMode={boardViewMode}
                            onBoardViewModeChange={(v) => setBoardViewMode(v)}
                            onEditProject={() => selectedProject && setEditingProject(selectedProject)}
                            onNewSession={() => {
                              setSpawnDialogInitialTaskId(selectedTask.id);
                              setShowSpawnDialog(true);
                            }}
                          />
                        }
                      />
                      <div className="flex-1 overflow-hidden px-6 py-4">
                        <SessionsTable
                          sessions={selectedTaskSessions}
                          agents={agents}
                          fileBasedAgents={fileBasedAgents}
                          onSessionSelect={(agent) => {
                            setSelectedAgent(agent);
                            setViewMode('chat');
                            updateSessionInUrl(agent.instance_id);
                          }}
                        />
                      </div>
                    </>
                  ) : projectsLoading && currentProjectId ? (
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
                          <ProjectHeaderActions
                            viewMode="kanban"
                            boardViewMode={boardViewMode}
                            onBoardViewModeChange={(v) => setBoardViewMode(v)}
                            onEditProject={() => setEditingProject(selectedProject)}
                            onNewTask={() => setShowCreateTaskModal(true)}
                          />
                        }
                      />

                      {/* Mobile: Task list */}
                      <div className="flex-1 lg:hidden overflow-y-auto px-4 py-4 space-y-2">
                        {projectTasks.length === 0 ? (
                          <div className="text-center py-12 text-sm text-gray-400">
                            No tasks yet. Tap "New Task" to create one.
                          </div>
                        ) : (
                          projectTasks.map((task) => (
                            <TaskKanbanCard
                              key={task.id}
                              task={task}
                              sessionCount={sessionCountByTaskId[task.id] || 0}
                              onClick={() => openTask(task.id)}
                              onDelete={(taskId) => deleteTask.mutate(taskId)}
                            />
                          ))
                        )}
                      </div>

                      {/* Desktop: Kanban Board or Table View */}
                      <div className="hidden lg:flex lg:flex-col flex-1 overflow-hidden">
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
                                {TASK_COLUMNS.map((column, index) => (
                                  <TaskKanbanColumn
                                    key={column.id}
                                    column={column}
                                    tasks={tasksByStatus[column.id]}
                                    sessionCountByTaskId={sessionCountByTaskId}
                                    onTaskClick={(taskId) => openTask(taskId)}
                                    onTaskDelete={(taskId) => deleteTask.mutate(taskId)}
                                    isLast={index === TASK_COLUMNS.length - 1}
                                  />
                                ))}
                              </div>

                              <DragOverlay>
                                {activeTask ? (
                                  <div className="opacity-80">
                                    <TaskKanbanCard
                                      task={activeTask}
                                      sessionCount={sessionCountByTaskId[activeTask.id] || 0}
                                      onClick={() => {}}
                                    />
                                  </div>
                                ) : null}
                              </DragOverlay>
                            </DndContext>
                          </div>
                        ) : (
                          <div className="h-full overflow-hidden pl-6 pr-6 pt-2 pb-6 flex flex-col gap-3">
                            <TasksTable
                              tasks={projectTasks}
                              sessionCountByTaskId={sessionCountByTaskId}
                              onTaskClick={(taskId) => openTask(taskId)}
                              onTaskDelete={(taskId) => deleteTask.mutate(taskId)}
                            />
                          </div>
                        )}

                        {/* Unassigned Sessions section */}
                        {unassignedSessions.length > 0 && (
                          <UnassignedSessionsBar
                            sessions={unassignedSessions}
                            agents={agents}
                            fileBasedAgents={fileBasedAgents}
                            onSessionSelect={(agent) => {
                              setSelectedAgent(agent);
                              setViewMode('chat');
                              updateSessionInUrl(agent.instance_id);
                            }}
                          />
                        )}
                      </div>
                    </>
                  ) : projectsLoading ? (
                    <LoadingState message="Loading..." />
                  ) : (
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

          {/* Modals */}
          <AnimatePresence>
            {showSpawnDialog && (
              <SpawnDialog
                selectedProject={selectedProject}
                initialTaskId={spawnDialogInitialTaskId}
                onClose={() => {
                  setShowSpawnDialog(false);
                  setSpawnDialogInitialTaskId(undefined);
                }}
                onSpawn={(agent) => {
                  setAgentInstances([...agentInstances, agent]);
                  setSelectedAgent(agent);
                  setViewMode('chat');
                  updateSessionInUrl(agent.instance_id);
                  setShowSpawnDialog(false);
                  setSpawnDialogInitialTaskId(undefined);
                }}
              />
            )}
          </AnimatePresence>

          {showCreateTaskModal && selectedProject && (
            <TaskCreateModal
              projectId={selectedProject.id}
              isOpen={showCreateTaskModal}
              onClose={() => setShowCreateTaskModal(false)}
            />
          )}

          {showCreateProjectDialog && (
            <ProjectModal
              project={null}
              onClose={() => setShowCreateProjectDialog(false)}
              onSave={async (data) => {
                try {
                  const project = await api.createProject(data as any);
                  setProjects([...projects, project]);
                  setSelectedProject(project);
                  setSelectedAgent(null);
                  setSelectedTaskId(null);
                  setViewMode('kanban');
                  updateSessionInUrl(null);
                  setPMExpanded(false);
                  setShowCreateProjectDialog(false);
                  setProjectsReloadTrigger(prev => prev + 1);
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
                  setProjectsReloadTrigger(prev => prev + 1);
                  setEditingProject(null);
                } catch (error) {
                  alert('Failed to update project: ' + error);
                }
              }}
            />
          )}

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

// Task Kanban Column Component
function TaskKanbanColumn({
  column,
  tasks,
  sessionCountByTaskId,
  onTaskClick,
  onTaskDelete,
  isLast,
}: {
  column: typeof TASK_COLUMNS[number];
  tasks: Task[];
  sessionCountByTaskId: Record<string, number>;
  onTaskClick: (taskId: string) => void;
  onTaskDelete?: (taskId: string) => void;
  isLast?: boolean;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: column.id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'flex flex-col flex-1 min-w-[260px] bg-white rounded-lg border shadow-sm transition-all',
        isOver ? 'border-primary bg-muted/50' : 'border-gray-200',
        isLast && 'mr-6'
      )}
    >
      <div className={`p-2 rounded-t-lg border-b border-gray-200 ${column.color}`}>
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-sm text-gray-700">{column.label}</h4>
          <span className="type-caption font-medium text-gray-600 bg-white px-2 py-0.5 rounded-full">
            {tasks.length}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-[200px]">
        <SortableContext
          items={tasks.map(t => t.id)}
          strategy={verticalListSortingStrategy}
        >
          {tasks.map((task) => (
            <DraggableTaskCard
              key={task.id}
              task={task}
              sessionCount={sessionCountByTaskId[task.id] || 0}
              onClick={() => onTaskClick(task.id)}
              onDelete={onTaskDelete}
            />
          ))}
        </SortableContext>
      </div>
    </div>
  );
}

const TASK_STATUS_COLORS: Record<TaskStatus, string> = {
  open: 'bg-gray-100 text-gray-600',
  in_progress: 'bg-blue-100 text-blue-700',
  done: 'bg-green-100 text-green-700',
  archived: 'bg-slate-100 text-slate-500',
};

const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  done: 'Done',
  archived: 'Archived',
};

// Simple tasks table for table view mode
function TasksTable({
  tasks,
  sessionCountByTaskId,
  onTaskClick,
  onTaskDelete,
}: {
  tasks: Task[];
  sessionCountByTaskId: Record<string, number>;
  onTaskClick: (taskId: string) => void;
  onTaskDelete?: (taskId: string) => void;
}) {
  const STATUS_COLORS = TASK_STATUS_COLORS;
  const STATUS_LABELS = TASK_STATUS_LABELS;

  if (tasks.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
        No tasks yet. Create one to get started.
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto rounded-lg border border-gray-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50">
            <th className="text-left px-4 py-2.5 font-medium text-gray-600">Task</th>
            <th className="text-left px-4 py-2.5 font-medium text-gray-600">Status</th>
            <th className="text-left px-4 py-2.5 font-medium text-gray-600">Sessions</th>
            <th className="w-10" />
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr
              key={task.id}
              className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer group"
              onClick={() => onTaskClick(task.id)}
            >
              <td className="px-4 py-3">
                <p className="font-medium text-gray-900">{task.name}</p>
                {task.description && (
                  <p className="text-xs text-gray-500 mt-0.5 truncate max-w-xs">{task.description}</p>
                )}
              </td>
              <td className="px-4 py-3">
                <span className={cn('text-xs px-2 py-0.5 rounded-full font-medium', STATUS_COLORS[task.status])}>
                  {STATUS_LABELS[task.status]}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-500">
                {sessionCountByTaskId[task.id] || 0}
              </td>
              <td className="px-2 py-3">
                {onTaskDelete && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Delete task "${task.name}"?`)) onTaskDelete(task.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all rounded"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Collapsible bar showing sessions not assigned to any task
function UnassignedSessionsBar({
  sessions,
  agents,
  fileBasedAgents,
  onSessionSelect,
}: {
  sessions: AgentInstance[];
  agents: Agent[];
  fileBasedAgents?: Agent[];
  onSessionSelect: (session: AgentInstance) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-t border-gray-200 bg-gray-50">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-6 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 transition-colors"
      >
        <ChevronRight className={cn('w-4 h-4 transition-transform', expanded && 'rotate-90')} />
        <span className="font-medium">Unassigned Sessions</span>
        <span className="text-xs bg-white border border-gray-200 px-2 py-0.5 rounded-full ml-1">
          {sessions.length}
        </span>
      </button>
      {expanded && (
        <div className="px-6 pb-3 grid grid-cols-3 gap-2 max-h-48 overflow-y-auto">
          {sessions.map((session) => {
            const fileAgent = fileBasedAgents?.find(a => a.id === session.agent_id);
            return (
              <button
                key={session.instance_id}
                type="button"
                onClick={() => onSessionSelect(session)}
                className="flex items-center gap-2 px-3 py-2 bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all text-left"
              >
                <Avatar
                  seed={session.agent_id || 'unknown'}
                  size={20}
                  className="w-5 h-5 flex-shrink-0"
                  color={fileAgent?.icon_color || '#6B7280'}
                />
                <span className="text-xs text-gray-700 truncate">
                  {session.current_session_description || session.context?.description || 'No description'}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Spawn Dialog
function SpawnDialog({
  selectedProject,
  initialTaskId,
  onClose,
  onSpawn,
}: {
  selectedProject: Project | null;
  initialTaskId?: string;
  onClose: () => void;
  onSpawn: (agent: AgentInstance) => void;
}) {
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [sessionDescription, setSessionDescription] = useState('');
  const [selectedTaskId, setSelectedTaskId] = useState<string>(initialTaskId || '');
  const [spawning, setSpawning] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [skills, setSkills] = useState<SkillMetadata[]>([]);
  const isMobile = useIsMobile();

  const { data: availableTasks = [] } = useTasks(selectedProject?.id);
  const activeTaskChoices = availableTasks.filter(t => t.status === 'open' || t.status === 'in_progress');

  useEffect(() => {
    api.getAgents().then(setAgents).catch(console.error);
    api.getSkills().then(setSkills).catch(console.error);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const projectAgents = useMemo(() => {
    if (!selectedProject) return agents;
    const allowedAgentIds = new Set([
      ...(selectedProject.team_member_ids || []),
      ...(selectedProject.pm_agent_id ? [selectedProject.pm_agent_id] : []),
    ]);
    return agents.filter(agent => allowedAgentIds.has(agent.id));
  }, [agents, selectedProject]);

  const handleToggleAgent = (agentId: string) => {
    setSelectedAgentId(agentId === selectedAgentId ? '' : agentId);
  };

  const handleSpawn = async () => {
    if (!selectedAgentId || !sessionDescription) return;

    setSpawning(true);
    try {
      const session = await api.createSession({
        agent_id: selectedAgentId,
        project_id: selectedProject?.id,
        session_type: 'specialist',
        task_id: selectedTaskId || undefined,
        context: {
          description: sessionDescription,
          project_path: selectedProject?.path || paths.projectRoot,
        },
      });
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

        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
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

          <div className="flex lg:w-1/2 flex-col">
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
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

              {activeTaskChoices.length > 0 && (
                <div>
                  <label className="block type-label text-gray-700 mb-1.5">
                    Task <span className="text-gray-400 font-normal">(optional)</span>
                  </label>
                  <select
                    value={selectedTaskId}
                    onChange={(e) => setSelectedTaskId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">No task</option>
                    {activeTaskChoices.map((t) => (
                      <option key={t.id} value={t.id}>
                        [{t.status === 'in_progress' ? 'In Progress' : 'Open'}] {t.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

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
                        const agent = agents.find(a => a.id === selectedAgentId);
                        if (!agent) return null;
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
                              <Avatar seed={agent.name} size={40} className="w-10 h-10 flex-shrink-0" color={agent.icon_color || '#4A90E2'} />
                              <div className="flex-1 min-w-0 pr-6">
                                <div className="type-subtitle text-gray-900 truncate">{agent.name}</div>
                                <div className="type-caption text-gray-500 line-clamp-2 mt-0.5">
                                  {agent.description || 'No description'}
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
