import { ReactNode, useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight, FolderOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import { EmptyState } from '@/components/ui';

interface RightSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  children?: ReactNode;
}

const MIN_WIDTH = 280;
const MAX_WIDTH = 600;
const DEFAULT_WIDTH = 320; // 80 * 4 = w-80

export function RightSidebar({
  isOpen,
  onToggle,
  children
}: RightSidebarProps) {
  const [width, setWidth] = useState(() => {
    try {
      const saved = localStorage.getItem('rightSidebarWidth');
      return saved ? parseInt(saved, 10) : DEFAULT_WIDTH;
    } catch {
      return DEFAULT_WIDTH;
    }
  });
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLElement>(null);

  // Save width to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('rightSidebarWidth', width.toString());
    } catch (error) {
      console.error('Failed to save right sidebar width:', error);
    }
  }, [width]);

  // Handle resize
  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
        setWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  return (
    <aside
      ref={sidebarRef}
      className={cn(
        "fixed lg:relative inset-y-0 right-0 z-30",
        "bg-gray-50 border-l border-border",
        "flex flex-col",
        !isOpen && "w-0 lg:w-0"
      )}
      style={isOpen ? { width: `${width}px` } : undefined}
    >
      {/* Content */}
      {isOpen && (
        <div className="flex-1 flex flex-col min-h-0">
          {children || (
            <EmptyState
              icon={FolderOpen}
              title="No project selected"
              description="Select a project to start chatting with the Project Manager"
              centered
            />
          )}
        </div>
      )}

      {/* Resize handle */}
      {isOpen && (
        <div
          className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary/20 active:bg-primary/30 transition-colors"
          onMouseDown={(e) => {
            e.preventDefault();
            setIsResizing(true);
          }}
        />
      )}
    </aside>
  );
}

// Helper component for session details
interface SessionDetailsProps {
  projectName?: string;
  sessionName?: string;
  members?: Array<{ id: string; name: string; role?: string }>;
  status?: 'running' | 'idle' | 'error';
}

export function SessionDetails({
  projectName,
  sessionName,
  members,
  status
}: SessionDetailsProps) {
  const statusColors = {
    running: 'bg-green-500',
    idle: 'bg-gray-400',
    error: 'bg-red-500'
  };

  const statusLabels = {
    running: 'Running',
    idle: 'Idle',
    error: 'Error'
  };

  return (
    <div className="p-4 space-y-6">
      {/* Breadcrumb */}
      {(projectName || sessionName) && (
        <div>
          <div className="type-label text-muted-foreground mb-2">Location</div>
          <div className="type-body-sm">
            {projectName && <span className="text-foreground">{projectName}</span>}
            {projectName && sessionName && <span className="text-muted-foreground mx-2">›</span>}
            {sessionName && <span className="font-medium text-foreground">{sessionName}</span>}
          </div>
        </div>
      )}

      {/* Status */}
      {status && (
        <div>
          <div className="type-label text-muted-foreground mb-2">Status</div>
          <div className="flex items-center gap-2">
            <div className={cn("w-2 h-2 rounded-full", statusColors[status])} />
            <span className="type-body-sm text-foreground">{statusLabels[status]}</span>
          </div>
        </div>
      )}

      {/* Members */}
      {members && members.length > 0 && (
        <div>
          <div className="type-label text-muted-foreground mb-2">
            Members ({members.length})
          </div>
          <div className="space-y-2">
            {members.map((member) => (
              <div key={member.id} className="flex items-center gap-2 type-body-sm">
                <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center type-label text-primary">
                  {member.name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-foreground truncate">{member.name}</div>
                  {member.role && (
                    <div className="type-caption text-muted-foreground">{member.role}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
