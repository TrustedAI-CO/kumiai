import { useState, useEffect, useMemo } from 'react';
import { Plus, Folder } from 'lucide-react';
import { api, Project, Agent } from '@/lib/api';
import { ListLayout } from '@/components/layout/ListLayout';
import { ProjectCard } from './ProjectCard';
import { cn } from '@/lib/utils';

interface ProjectsListProps {
  currentProjectId?: string;
  onSelectProject: (projectId: string) => void;
  onDeleteProject: (projectId: string) => void;
  onCreateProject: () => void;
  isMobile?: boolean;
  reloadTrigger?: number;
  showArchived?: boolean;
}

export function ProjectsList({
  currentProjectId,
  onSelectProject,
  onDeleteProject,
  onCreateProject,
  isMobile = false,
  reloadTrigger,
  showArchived = false
}: ProjectsListProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [allSessions, setAllSessions] = useState<any[]>([]);

  useEffect(() => {
    loadData();
  }, [showArchived]);

  useEffect(() => {
    if (reloadTrigger !== undefined) {
      loadData();
    }
  }, [reloadTrigger]);

  // Poll for session updates every 5 seconds to keep running count live
  useEffect(() => {
    const interval = setInterval(() => {
      // Only reload sessions, not projects/agents
      api.getSessions().then(sessionsData => {
        setAllSessions(Array.isArray(sessionsData) ? sessionsData : []);
      }).catch(error => {
        console.error('Failed to poll sessions:', error);
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [projectsData, agentsData, sessionsData] = await Promise.all([
        api.getProjects(showArchived),
        api.getAgents(),
        api.getSessions()
      ]);
      setProjects(projectsData);
      setAgents(agentsData);
      setAllSessions(Array.isArray(sessionsData) ? sessionsData : []);
    } catch (error) {
      console.error('Failed to load projects data:', error);
    } finally {
      setLoading(false);
    }
  };


  const filteredProjects = useMemo(() =>
    projects.filter(project =>
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (project.description && project.description.toLowerCase().includes(searchQuery.toLowerCase()))
    ),
    [projects, searchQuery]
  );

  return (
    <ListLayout
      searchQuery={searchQuery}
      onSearchChange={setSearchQuery}
      searchPlaceholder="Search projects..."
      loading={loading}
      isEmpty={filteredProjects.length === 0}
      emptyIcon={Folder}
      emptyTitle={searchQuery ? 'No projects found' : showArchived ? 'No archived projects' : 'No projects yet'}
      emptyDescription={searchQuery ? 'Try a different search term' : 'Create one to get started'}
      actionButtons={[
        { icon: Plus, onClick: onCreateProject, title: 'New Project', variant: 'primary' }
      ]}
      isMobile={isMobile}
    >
      <div className={cn("flex flex-col gap-2")}>
        {filteredProjects.map((project) => {
          const runningCount = allSessions.filter(
            s => s.project_id === project.id && s.status === 'working'
          ).length;

          return (
            <ProjectCard
              key={project.id}
              project={project}
              agents={agents}
              isSelected={currentProjectId === project.id}
              runningSessionsCount={runningCount}
              onClick={() => onSelectProject(project.id)}
              onDelete={() => onDeleteProject(project.id)}
            />
          );
        })}
      </div>
    </ListLayout>
  );
}
