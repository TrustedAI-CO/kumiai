import { useState, useEffect } from 'react';
import { Routes, Route, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import WorkplaceKanban from './pages/WorkplaceKanban';
import Skills from './pages/Skills';
import Agents from './pages/Agents';
import { ProjectSwitcher } from '@/components/features/projects';
import { SessionSwitcher } from '@/components/features/sessions';
import { ProjectModal } from '@/components/modals';
import { WelcomeModal } from '@/components/modals';
import { ErrorBoundary } from '@/ui';
import { BottomNav } from '@/components/layout';
import { ToastProvider, useToast } from '@/ui';
import { desktopNotifications } from '@/lib/utils';
import { api } from '@/lib/api';
import type { ChatContext } from '@/types/chat';
import { ModalProvider, useModal } from '@/contexts/ModalContext';
import { useWorkspaceStore } from '@/stores/workspaceStore';

function AppContent() {
  const toast = useToast();
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { openModal, closeModal, isModalOpen } = useModal();

  // Use workspace store for state management
  const currentProjectId = useWorkspaceStore((state) => state.currentProjectId);
  const chatContext = useWorkspaceStore((state) => state.chatContext);
  const switchProject = useWorkspaceStore((state) => state.switchProject);
  const setChatContext = useWorkspaceStore((state) => state.setChatContext);

  const [hasCheckedOnboarding, setHasCheckedOnboarding] = useState(false);

  // Sync currentProjectId with URL params changes
  useEffect(() => {
    const urlProjectId = searchParams.get('project');
    if (urlProjectId !== currentProjectId) {
      // Use switchProject to ensure all dependent state is reset
      switchProject(urlProjectId || undefined);
    }
  }, [searchParams, currentProjectId, switchProject]);

  // Validate current project ID
  useEffect(() => {
    if (currentProjectId) {
      import('@/lib/api').then(({ api }) => {
        api.getProject(currentProjectId).catch((err) => {
          console.error('Failed to fetch project:', err);

          // Clear invalid project ID from URL and state
          if (err.message && err.message.includes('not found')) {
            console.warn(`Project ${currentProjectId} not found, clearing from state`);
            switchProject(undefined);

            // Remove project param from URL
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.delete('project');
            navigate(newUrl.pathname + newUrl.search, { replace: true });
          }
        });
      });
    }
  }, [currentProjectId, navigate, switchProject]);

  // Check for onboarding on mount
  useEffect(() => {
    if (!hasCheckedOnboarding) {
      api.getOnboardingStatus().then((status) => {
        setHasCheckedOnboarding(true);
        if (!status.completed) {
          openModal('welcome-modal');
        }
      }).catch(console.error);
    }
  }, [hasCheckedOnboarding, openModal]);

  // Load default project on mount if none selected (only on Workspace page)
  useEffect(() => {
    // Only auto-load project on Workspace page, not on Projects page
    if (!currentProjectId && location.pathname === '/' && hasCheckedOnboarding) {
      import('@/lib/api').then(({ api }) => {
        api.getProjects(false).then((projects) => {
          if (projects.length > 0) {
            const defaultProjectId = projects[0].id;
            switchProject(defaultProjectId);
            navigate(`/?project=${defaultProjectId}`, { replace: true });
          }
        }).catch(console.error);
      });
    }
  }, [currentProjectId, navigate, location.pathname, hasCheckedOnboarding, switchProject]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl+Shift+P - Project Switcher
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'p' || e.key === 'P')) {
        e.preventDefault();
        e.stopPropagation();
        openModal('project-switcher');
      }

      // Cmd/Ctrl+Shift+S - Session Searcher
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 's' || e.key === 'S')) {
        e.preventDefault();
        e.stopPropagation();
        openModal('session-switcher');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [openModal]);

  // Request notification permissions on mount
  useEffect(() => {
    console.log('[App] Notification support:', desktopNotifications.isSupported());
    console.log('[App] Current permission:', desktopNotifications.getPermission());

    if (desktopNotifications.isSupported() && desktopNotifications.getPermission() === 'default') {
      console.log('[App] Requesting notification permission...');
      desktopNotifications.requestPermission()
        .then(granted => console.log('[App] Permission granted:', granted))
        .catch(err => console.error('[App] Permission error:', err));
    }
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-background">
        {/* Main Content Area - Add bottom padding on mobile for bottom nav */}
        <div className="flex-1 flex flex-col overflow-hidden pb-16 lg:pb-0">
          <Routes>
          <Route path="/" element={
            <WorkplaceKanban
              currentProjectId={currentProjectId}
              onChatContextChange={setChatContext}
              onProjectChange={(projectId) => {
                switchProject(projectId);
                navigate(`/?project=${projectId}`, { replace: true });
              }}
            />
          } />
          <Route path="/agents" element={
            <Agents
              onChatContextChange={setChatContext}
            />
          } />
          <Route path="/skills" element={
            <Skills
              onChatContextChange={setChatContext}
            />
          } />
          </Routes>
        </div>

        {/* Project Switcher Modal */}
      <ProjectSwitcher
        isOpen={isModalOpen('project-switcher')}
        onClose={closeModal}
        onSelectProject={(projectId) => {
          switchProject(projectId);
          navigate(`/?project=${projectId}`);
        }}
        onCreateProject={() => {
          openModal('project-modal');
        }}
        currentProjectId={currentProjectId}
      />

      {/* Session Switcher Modal */}
      <SessionSwitcher
        isOpen={isModalOpen('session-switcher')}
        onClose={closeModal}
        onSelectSession={(instanceId) => {
          // Navigate to workspace with session opened
          navigate(`/?session=${instanceId}`);
        }}
        currentProjectId={currentProjectId}
      />

      {/* Project Creation Modal */}
      {isModalOpen('project-modal') && (
        <ProjectModal
          project={null}
          onSave={async (data) => {
            try {
              const newProject = await api.createProject(data as any);
              closeModal();
              switchProject(newProject.id);
              navigate(`/?project=${newProject.id}`);
            } catch (error) {
              console.error('Failed to create project:', error);
              toast.error('Failed to create project', 'Error');
            }
          }}
          onClose={closeModal}
        />
      )}

      {/* Welcome/Onboarding Modal */}
      <WelcomeModal
        isOpen={isModalOpen('welcome-modal')}
        onClose={closeModal}
        onSetupTeam={async (team) => {
          try {
            const result = await api.setupDemo(team);
            toast.success(result.message, 'Success');
            closeModal();

            // Reload the page to show the new demo project
            setTimeout(() => {
              window.location.href = '/';
            }, 500);
          } catch (error) {
            console.error('Failed to setup demo:', error);
            toast.error('Failed to setup demo team', 'Error');
          }
        }}
      />

      {/* Bottom Navigation - Mobile Only */}
      <BottomNav />
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider position="top-right">
        <ModalProvider>
          <AppContent />
        </ModalProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
