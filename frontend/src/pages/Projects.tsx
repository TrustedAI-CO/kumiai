/**
 * Projects - Project management page with PM chat integration
 *
 * Two-column layout:
 * - Left: Projects sidebar with compact cards
 * - Right: PM chat session for selected project
 */
import { useState, useEffect } from 'react';
import { Plus, Edit2, Archive, Folder, ExternalLink, Briefcase, Search, List, ArchiveRestore, Trash2, Loader2, X } from 'lucide-react';
import { LoadingState, EmptyState, Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui';
import { api, Project, CreateProjectRequest, UpdateProjectRequest, AgentInstance, Agent } from '@/lib/api';
import { cn } from '@/lib/utils';
import { layout } from '@/styles/design-system';
import { Avatar } from '@/ui';
import { UnifiedSessionChat } from '@/components/features/sessions';
import { ProjectCard } from '@/components/features/projects';
import { ProjectModal } from '@/components/modals';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/primitives/button';
import { useUser } from '@/contexts/UserContext';
import { MobileHeader } from '@/components/layout';
import { useIsDesktop, useIsMobile } from '@/hooks';

interface ProjectsProps {
  currentProjectId?: string;
  onProjectSelect?: (projectId: string | null) => void;
}

// Helper to check if project is archived (soft deleted)
const isProjectArchived = (project: Project): boolean => {
  return !!project.deleted_at;
};

export function Projects({ currentProjectId, onProjectSelect }: ProjectsProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  // PM Chat state
  const [pmSession, setPmSession] = useState<AgentInstance | null>(null);
  const [pmSessionLoading, setPmSessionLoading] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Track all sessions for running count
  const [allSessions, setAllSessions] = useState<AgentInstance[]>([]);

  const navigate = useNavigate();
  const { profile } = useUser();

  // Responsive hooks
  const isDesktop = useIsDesktop();
  const isMobile = useIsMobile();

  // Helper function to update selected project (uses URL for both mobile and desktop)
  const selectProject = (projectId: string | null) => {
    if (projectId) {
      navigate(`/projects?project=${projectId}`, { replace: true });
      onProjectSelect?.(projectId);
    } else {
      navigate('/projects', { replace: true });
      onProjectSelect?.(null); // Notify parent that no project is selected
    }
  };

  useEffect(() => {
    loadProjects();
    loadAgents();
    loadAllPmSessions();
  }, [showArchived]);

  // Poll for session status updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadAllPmSessions();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Load PM session when project is selected
  useEffect(() => {
    if (currentProjectId) {
      loadPmSession(currentProjectId);
    } else {
      setPmSession(null);
    }
  }, [currentProjectId]);

  // Auto-select first project on desktop when none selected
  useEffect(() => {
    if (isDesktop && !currentProjectId && projects.length > 0 && !isProjectArchived(projects[0])) {
      selectProject(projects[0].id);
    }
  }, [isDesktop, currentProjectId, projects]);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await api.getProjects(showArchived);
      setProjects(data);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAgents = async () => {
    try {
      const agentsData = await api.getAgents();
      console.log('[Projects] Loaded agents:', agentsData.map(a => ({ id: a.id, name: a.name })));
      setAgents(agentsData);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const loadAllPmSessions = async () => {
    try {
      const sessions = await api.getSessions();
      // Defensive: ensure sessions is an array
      const sessionsArray = Array.isArray(sessions) ? sessions : [];
      if (!Array.isArray(sessions)) {
        console.warn('[Projects] getSessions returned non-array:', sessions);
      }

      console.log('[Projects] All sessions loaded:', sessionsArray.length);

      // Store all sessions for running count display
      setAllSessions(sessionsArray);
    } catch (error) {
      console.error('Failed to load all sessions:', error);
    }
  };

  const loadPmSession = async (projectId: string) => {
    setPmSessionLoading(true);
    try {
      console.log('[Projects] loadPmSession called for project:', projectId);

      // Query for existing PM session for this project (filtered by backend)
      const sessions = await api.getSessions(projectId);

      // Find all PM sessions for this project
      const pmSessions = sessions.filter(s => s.role === 'pm');

      // Warn about duplicates
      if (pmSessions.length > 1) {
        console.warn(`[Projects] Found ${pmSessions.length} PM sessions for project ${projectId}. Using the last one.`);
      }

      // Use the most recent PM session (or last in array)
      const session = pmSessions.length > 0 ? pmSessions[pmSessions.length - 1] : null;
      console.log('[Projects] Found session for project:', projectId, session ? session.instance_id : 'null');

      setPmSession(session || null);
    } catch (error) {
      console.error('Failed to load PM session:', error);
      setPmSession(null);
    } finally {
      setPmSessionLoading(false);
    }
  };

  const handleRecreatePmSession = async (projectId: string) => {
    if (!confirm('This will recreate the PM session. All existing conversation history will be lost. Continue?')) {
      return;
    }

    setPmSessionLoading(true);
    try {
      // Get the current PM session via direct API call
      const sessions = await api.getSessions(projectId);
      const pmSessions = sessions.filter(s => s.role === 'pm');
      const currentPmSession = pmSessions.length > 0 ? pmSessions[pmSessions.length - 1] : null;

      if (!currentPmSession) {
        alert('No PM session found for this project');
        setPmSessionLoading(false);
        return;
      }

      // Get the project to find the PM agent ID
      const project = projects.find(p => p.id === projectId);
      if (!project || !project.pm_agent_id) {
        alert('Project has no PM agent assigned');
        setPmSessionLoading(false);
        return;
      }

      // Step 1: Delete the old PM session
      console.log(`Deleting old PM session ${currentPmSession.instance_id}...`);
      await api.deleteSession(currentPmSession.instance_id);

      // Step 2: Create a new PM session
      console.log(`Creating new PM session for project ${projectId}...`);
      const newSession = await api.createSession({
        agent_id: project.pm_agent_id,
        project_id: projectId,
        session_type: 'pm',
      });

      console.log(`New PM session created: ${newSession.instance_id}`);

      // Reload all PM sessions to update running counts
      await loadAllPmSessions();
      // Reload the PM session for this project (will force UnifiedSessionChat to remount)
      await loadPmSession(projectId);

      alert('PM session recreated successfully!');
    } catch (error) {
      console.error('Failed to recreate PM session:', error);
      alert(error instanceof Error ? error.message : 'Failed to recreate PM session');
    } finally {
      setPmSessionLoading(false);
    }
  };

  const handleCreateProject = async (data: CreateProjectRequest) => {
    try {
      const newProject = await api.createProject(data);
      await loadProjects();
      setIsCreating(false);

      // Navigate to kanban/table view with the new project
      if (newProject.id) {
        navigate(`/?project=${newProject.id}`, { replace: true });
      }
    } catch (error) {
      console.error('Failed to create project:', error);
      alert(error instanceof Error ? error.message : 'Failed to create project');
    }
  };

  const handleUpdateProject = async (projectId: string, data: UpdateProjectRequest) => {
    try {
      await api.updateProject(projectId, data);
      await loadProjects();
      setEditingProject(null);
    } catch (error) {
      console.error('Failed to update project:', error);
      alert(error instanceof Error ? error.message : 'Failed to update project');
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to archive this project?')) {
      return;
    }

    try {
      await api.deleteProject(projectId);
      await loadProjects();

      // Clear selection if current project was deleted
      if (currentProjectId === projectId) {
        onProjectSelect?.('');
        navigate('/projects', { replace: true });
      }
    } catch (error) {
      console.error('Failed to delete project:', error);
      alert(error instanceof Error ? error.message : 'Failed to archive project');
    }
  };

  const handleUnarchiveProject = async (projectId: string) => {
    try {
      await api.unarchiveProject(projectId);
      await loadProjects();
    } catch (error) {
      console.error('Failed to unarchive project:', error);
      alert(error instanceof Error ? error.message : 'Failed to unarchive project');
    }
  };

  const handlePermanentlyDeleteProject = async (projectId: string) => {
    const userConfirmation = prompt(
      '⚠️ WARNING: This will permanently remove the project from the app.\n\n' +
      'Project files on disk will NOT be deleted.\n' +
      'This action CANNOT be undone!\n\n' +
      'Type "DELETE" to confirm:'
    );

    if (userConfirmation !== 'DELETE') {
      return;
    }

    try {
      await api.permanentlyDeleteProject(projectId);
      await loadProjects();

      // Clear selection if current project was deleted
      if (currentProjectId === projectId) {
        onProjectSelect?.('');
        navigate('/projects', { replace: true });
      }
    } catch (error) {
      console.error('Failed to permanently delete project:', error);
      alert(error instanceof Error ? error.message : 'Failed to permanently delete project');
    }
  };

  const handleOpenProject = (projectId: string) => {
    navigate(`/?project=${projectId}`);
  };

  // Filter projects by search query
  const filteredProjects = projects.filter(project => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      project.name.toLowerCase().includes(query) ||
      (project.description && project.description.toLowerCase().includes(query))
    );
  });

  // Projects Sidebar Content (shared between desktop and mobile)
  const projectsSidebarContent = (
    <>
      {/* Search Bar */}
      <div className="h-12 px-2 lg:px-3 bg-white flex items-center flex-shrink-0">
        <div className="flex items-center gap-2 w-full">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search projects..."
              className="input-search"
            />
          </div>
          <button
            onClick={() => setIsCreating(true)}
            className="flex-shrink-0 p-1.5 bg-primary text-white hover:bg-primary transition-colors"
            title="New Project"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Projects List */}
      <div className="flex-1 overflow-y-auto p-2 pb-24">
        {loading && (
          <LoadingState message="Loading projects..." />
        )}

        {!loading && filteredProjects.length === 0 && (
          <div className="p-6 text-center text-gray-500">
            <Folder className="w-12 h-12 mx-auto mb-2.5 text-gray-400" />
            <p className="text-sm">{searchQuery ? 'No projects found' : showArchived ? 'No archived projects' : 'No projects yet'}</p>
            <p className="text-xs text-gray-400 mt-1">
              {searchQuery ? 'Try a different search term' : 'Create one to get started'}
            </p>
          </div>
        )}

        {!loading && filteredProjects.length > 0 && (
          <div className="flex flex-col">
            {filteredProjects.map((project) => {
              const runningCount = allSessions.filter(
                s => s.project_id === project.id && s.status === 'working'
              ).length;

              return (
                <ProjectCard
                  key={project.id}
                  project={project}
                  isSelected={currentProjectId === project.id}
                  agents={agents}
                  runningSessionsCount={runningCount}
                  onSelect={() => {
                    selectProject(project.id);
                  }}
                  onEdit={() => setEditingProject(project)}
                  onDelete={() => handleDeleteProject(project.id)}
                  onUnarchive={() => handleUnarchiveProject(project.id)}
                  onPermanentDelete={() => handlePermanentlyDeleteProject(project.id)}
                  onOpen={() => handleOpenProject(project.id)}
                />
              );
            })}
          </div>
        )}
      </div>

      {/* Bottom Action Container */}
      <div className="flex-shrink-0 bg-white p-4">
        {/* Show archived checkbox - Desktop only */}
        <label className="hidden lg:flex items-center gap-2 text-xs text-gray-600 px-3 py-2 rounded-md border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
            className="rounded"
          />
          Show archived
        </label>
      </div>
    </>
  );

  return (
    <div className="flex-1 flex overflow-hidden bg-white">
      {/* Mobile: Project List Sheet */}
      <Sheet open={isMobile && !currentProjectId} onOpenChange={(open) => {
        if (!open && currentProjectId) {
          selectProject(null);
        }
      }}>
        <SheetContent side="left" className="w-full p-0">
          <div className="flex flex-col h-full">
            {projectsSidebarContent}
          </div>
        </SheetContent>
      </Sheet>

      {/* Desktop Sidebar: Projects List */}
      <div className="hidden lg:flex border-r-2 border-primary flex-col relative" style={{ width: layout.sidebarWidth }}>
        {projectsSidebarContent}
      </div>

      {/* Main Content: PM Chat */}
      <div className={cn(
        "flex-1 flex flex-col min-w-0 overflow-hidden",
        currentProjectId ? "pt-0" : "hidden lg:flex lg:pt-0"
      )}>
        {currentProjectId && pmSession && pmSession.status !== 'initializing' ? (
          <UnifiedSessionChat
            key={pmSession.instance_id}
            instanceId={pmSession.instance_id}
            role="pm"
            showHeader={true}
            userAvatar={profile?.avatar || undefined}
            onClose={() => selectProject(null)}
            onSessionJump={(sessionId) => {
              // When jumping to a session from Projects page, navigate to the Workspace
              // with the session opened
              const project = projects.find(p => p.id === currentProjectId);
              if (project) {
                navigate(`/?project=${project.id}&session=${sessionId}`);
              }
            }}
          />
        ) : currentProjectId && pmSession && pmSession.status === 'initializing' ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="w-8 h-8 mx-auto mb-3 text-primary animate-spin" />
              <p className="text-gray-700 font-medium">Initializing PM session...</p>
              <p className="text-sm text-gray-500 mt-2">Connecting to Claude and setting up workspace</p>
              <p className="text-xs text-gray-400 mt-1">This usually takes 2-5 seconds</p>
            </div>
          </div>
        ) : currentProjectId && pmSessionLoading ? (
          <LoadingState message="Loading PM session..." />
        ) : currentProjectId && !pmSession ? (
          <EmptyState
            icon={Briefcase}
            title="No PM session available"
            description="The project may not have a PM agent assigned"
            centered
          />
        ) : (
          <EmptyState
            icon={Briefcase}
            title="Select a project"
            description="Choose a project from the sidebar to chat with its PM"
            centered
          />
        )}
      </div>

      {/* Create/Edit Modal */}
      {(isCreating || editingProject) && (
        <ProjectModal
          project={editingProject}
          onSave={(data) => {
            if (editingProject) {
              handleUpdateProject(editingProject.id, data);
            } else {
              handleCreateProject(data as CreateProjectRequest);
            }
          }}
          onClose={() => {
            setIsCreating(false);
            setEditingProject(null);
          }}
        />
      )}
    </div>
  );
}
