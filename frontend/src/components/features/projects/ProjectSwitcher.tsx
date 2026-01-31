import { useState, useEffect, useRef } from 'react';
import { Search, Folder, Plus, X, Loader2 } from 'lucide-react';
import { api, Project } from '@/lib/api';
import { cn } from '@/lib/utils';

interface ProjectSwitcherProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectProject: (projectId: string) => void;
  onCreateProject: () => void;
  currentProjectId?: string;
}

export function ProjectSwitcher({
  isOpen,
  onClose,
  onSelectProject,
  onCreateProject,
  currentProjectId,
}: ProjectSwitcherProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);

  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      loadProjects();
      setSearchQuery('');
      setSelectedIndex(0);
      setTimeout(() => searchInputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, filteredProjects.length));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (selectedIndex === filteredProjects.length) {
          onCreateProject();
          onClose();
        } else {
          const project = filteredProjects[selectedIndex];
          if (project) {
            onSelectProject(project.id);
            onClose();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, searchQuery]);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await api.getProjects(false);
      setProjects(data);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredProjects = projects.filter((project) => {
    const query = searchQuery.toLowerCase();
    return (
      project.name.toLowerCase().includes(query) ||
      project.description?.toLowerCase().includes(query)
    );
  });

  const sortedProjects = [...filteredProjects].sort((a, b) => {
    if (a.id === currentProjectId) return -1;
    if (b.id === currentProjectId) return 1;
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
  });

  const recentProjects = sortedProjects.slice(0, 5);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed top-20 left-1/2 -translate-x-1/2 w-full max-w-xl bg-white rounded-lg shadow-2xl z-50">
        {/* Search Input */}
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setSelectedIndex(0);
              }}
              placeholder="Search projects..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              onClick={onClose}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Projects List */}
        <div className="max-h-96 overflow-y-auto">
          {loading && (
            <div className="p-8 text-center">
              <Loader2 className="w-8 h-8 mx-auto mb-3 text-gray-400 animate-spin" />
              <p className="text-gray-500">Loading projects...</p>
            </div>
          )}

          {!loading && sortedProjects.length === 0 && (
            <div className="p-8 text-center text-gray-400">
              {searchQuery ? 'No projects found' : 'No projects yet'}
            </div>
          )}

          {!loading && sortedProjects.length > 0 && (
            <>
              {!searchQuery && (
                <div className="p-2">
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Recent Projects
                  </div>
                  {recentProjects.map((project, index) => (
                    <ProjectItem
                      key={project.id}
                      project={project}
                      isSelected={index === selectedIndex}
                      isCurrent={project.id === currentProjectId}
                      onClick={() => {
                        onSelectProject(project.id);
                        onClose();
                      }}
                    />
                  ))}
                </div>
              )}

              {searchQuery && (
                <div className="p-2">
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    All Projects
                  </div>
                  {sortedProjects.map((project, index) => (
                    <ProjectItem
                      key={project.id}
                      project={project}
                      isSelected={index === selectedIndex}
                      isCurrent={project.id === currentProjectId}
                      onClick={() => {
                        onSelectProject(project.id);
                        onClose();
                      }}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {/* Create New Project Option */}
          <div className="p-2 border-t border-gray-200">
            <button
              onClick={() => {
                onCreateProject();
                onClose();
              }}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                selectedIndex === sortedProjects.length
                  ? "bg-primary/10 text-primary"
                  : "hover:bg-gray-100 text-gray-700"
              )}
            >
              <Plus className="w-5 h-5 text-primary" />
              <span className="font-medium">Create New Project</span>
            </button>
          </div>
        </div>

        {/* Footer Hint */}
        <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-500 flex items-center justify-between rounded-b-lg">
          <span>↑↓ Navigate • Enter Select • Esc Close</span>
          <span className="font-mono">Cmd/Ctrl + P</span>
        </div>
      </div>
    </>
  );
}

interface ProjectItemProps {
  project: Project;
  isSelected: boolean;
  isCurrent: boolean;
  onClick: () => void;
}

function ProjectItem({ project, isSelected, isCurrent, onClick }: ProjectItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-left",
        isSelected
          ? "bg-primary/10 text-primary"
          : "hover:bg-gray-100 text-gray-700"
      )}
    >
      <div
        className="w-8 h-8 rounded-md flex items-center justify-center bg-primary text-white text-sm font-bold flex-shrink-0"
      >
        {project.name.substring(0, 2).toUpperCase()}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium truncate">{project.name}</span>
          {isCurrent && (
            <span className="text-xs text-primary bg-primary/10 px-1.5 py-0.5 rounded">
              Current
            </span>
          )}
        </div>
        {project.description && (
          <p className="text-xs text-gray-500 truncate">
            {project.description}
          </p>
        )}
      </div>

      <Folder className="w-4 h-4 text-gray-400 flex-shrink-0" />
    </button>
  );
}
