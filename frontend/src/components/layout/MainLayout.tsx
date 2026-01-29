import { ReactNode } from 'react';
import { LeftSidebar } from '@/components/layout/LeftSidebar';
import { RightSidebar } from '@/components/layout/RightSidebar';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores/uiStore';

interface MainLayoutProps {
  children: ReactNode | ((props: {
    leftSidebarOpen: boolean;
    rightSidebarOpen: boolean;
    toggleLeftSidebar: () => void;
    toggleRightSidebar: () => void;
  }) => ReactNode);
  leftSidebarContent?: ReactNode;
  leftSidebarNav?: ReactNode;
  leftSidebarFooter?: ReactNode;
  rightSidebarContent?: ReactNode;
}

export function MainLayout({
  children,
  leftSidebarContent,
  leftSidebarNav,
  leftSidebarFooter,
  rightSidebarContent
}: MainLayoutProps) {
  // Use UI store for sidebar state management
  const leftSidebarOpen = useUIStore((state) => state.leftSidebarOpen);
  const rightSidebarOpen = useUIStore((state) => state.rightSidebarOpen);
  const toggleLeftSidebar = useUIStore((state) => state.toggleLeftSidebar);
  const toggleRightSidebar = useUIStore((state) => state.toggleRightSidebar);

  return (
    <div className="h-screen flex overflow-hidden bg-background">
      {/* Left Sidebar */}
      <LeftSidebar
        isOpen={leftSidebarOpen}
        onToggle={toggleLeftSidebar}
        nav={leftSidebarNav}
        footer={leftSidebarFooter}
      >
        {leftSidebarContent}
      </LeftSidebar>

      {/* Main Content Area */}
      <main className={cn(
        "flex-1 flex flex-col overflow-hidden transition-all duration-300",
        leftSidebarOpen && "lg:ml-0",
        !leftSidebarOpen && "lg:ml-0"
      )}>
        {typeof children === 'function'
          ? children({
              leftSidebarOpen,
              rightSidebarOpen,
              toggleLeftSidebar,
              toggleRightSidebar
            })
          : children}
      </main>

      {/* Right Sidebar - only render if there's content */}
      {rightSidebarContent && (
        <RightSidebar
          isOpen={rightSidebarOpen}
          onToggle={toggleRightSidebar}
        >
          {rightSidebarContent}
        </RightSidebar>
      )}
    </div>
  );
}
