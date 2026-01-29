import { ReactNode, useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight, FileQuestion } from 'lucide-react';
import { cn } from '@/lib/utils';
import { EmptyState } from '@/components/ui';

interface LeftSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  children?: ReactNode;
  nav?: ReactNode;
  footer?: ReactNode;
}

const MIN_WIDTH = 200;
const MAX_WIDTH = 500;
const DEFAULT_WIDTH = 256; // 64 * 4 = w-64

export function LeftSidebar({
  isOpen,
  onToggle,
  children,
  nav,
  footer
}: LeftSidebarProps) {
  const [width, setWidth] = useState(() => {
    try {
      const saved = localStorage.getItem('leftSidebarWidth');
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
      localStorage.setItem('leftSidebarWidth', width.toString());
    } catch (error) {
      console.error('Failed to save left sidebar width:', error);
    }
  }, [width]);

  // Handle resize
  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = e.clientX;
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
    <>
      {/* Sidebar */}
      <aside
        ref={sidebarRef}
        className={cn(
          "fixed lg:relative inset-y-0 left-0 z-30",
          "bg-gray-50 border-r border-border",
          "flex flex-col",
          !isOpen && "w-0 lg:w-0"
        )}
        style={isOpen ? { width: `${width}px` } : undefined}
      >
        {/* Sidebar Header */}
        {isOpen && nav && (
          <div className="flex-shrink-0">
            {nav}
          </div>
        )}

        {/* Content */}
        {isOpen && (
          <div className="flex-1 overflow-y-auto">
            {children || (
              <EmptyState
                icon={FileQuestion}
                title="No content available"
                centered
              />
            )}
          </div>
        )}

        {/* Footer */}
        {isOpen && footer && (
          <div className="flex-shrink-0">
            {footer}
          </div>
        )}

        {/* Resize handle */}
        {isOpen && (
          <div
            className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary/20 active:bg-primary/30 transition-colors"
            onMouseDown={(e) => {
              e.preventDefault();
              setIsResizing(true);
            }}
          />
        )}
      </aside>

      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onToggle}
          aria-hidden="true"
        />
      )}
    </>
  );
}
