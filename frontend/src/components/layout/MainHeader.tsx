import { ReactNode } from 'react';
import { PanelLeft, PanelRight, PanelLeftClose, PanelRightClose, ChevronRight, X } from 'lucide-react';

interface MainHeaderProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  showBackButton?: boolean;
  onBack?: () => void;
  leftSidebarOpen?: boolean;
  onToggleLeftSidebar?: () => void;
  rightSidebarOpen?: boolean;
  onToggleRightSidebar?: () => void;
  breadcrumb?: string; // Optional breadcrumb before title (e.g., project name)
}

export function MainHeader({
  title,
  subtitle,
  icon,
  actions,
  showBackButton,
  onBack,
  leftSidebarOpen,
  onToggleLeftSidebar,
  rightSidebarOpen,
  onToggleRightSidebar,
  breadcrumb
}: MainHeaderProps) {
  return (
    <div className="flex-shrink-0 bg-white h-14 px-6">
      <div className="flex items-center justify-between h-full">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {onToggleLeftSidebar && (
            <button
              onClick={onToggleLeftSidebar}
              className="p-1.5 hover:bg-muted rounded-md transition-colors flex-shrink-0"
              aria-label={leftSidebarOpen ? "Close left sidebar" : "Open left sidebar"}
              title={leftSidebarOpen ? "Close left sidebar" : "Open left sidebar"}
            >
              {leftSidebarOpen ? (
                <PanelLeftClose className="w-4 h-4 text-muted-foreground" />
              ) : (
                <PanelLeft className="w-4 h-4 text-muted-foreground" />
              )}
            </button>
          )}

          {/* Breadcrumb layout for session views */}
          {breadcrumb ? (
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <span className="type-body-sm text-muted-foreground flex-shrink-0">{breadcrumb}</span>
              <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <h1 className="type-body-sm text-muted-foreground truncate">{title}</h1>
            </div>
          ) : (
            /* Standard layout with icon */
            <>
              {icon && <div className="flex-shrink-0">{icon}</div>}
              <div className="min-w-0">
                <h1 className="type-body-sm text-muted-foreground">{title}</h1>
                {subtitle && (
                  <p className="type-caption mt-0.5 truncate">{subtitle}</p>
                )}
              </div>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Avatar and close button for breadcrumb layout */}
          {breadcrumb && (
            <>
              {icon && <div className="flex-shrink-0">{icon}</div>}
              {showBackButton && onBack && (
                <button
                  onClick={onBack}
                  className="p-1.5 hover:bg-muted rounded-md transition-colors"
                  aria-label="Close session"
                  title="Close session"
                >
                  <X className="w-4 h-4 text-muted-foreground" />
                </button>
              )}
            </>
          )}

          {actions}
          {onToggleRightSidebar && (
            <button
              onClick={onToggleRightSidebar}
              className="p-1.5 hover:bg-muted rounded-md transition-colors"
              aria-label={rightSidebarOpen ? "Close right sidebar" : "Open right sidebar"}
              title={rightSidebarOpen ? "Close right sidebar" : "Open right sidebar"}
            >
              {rightSidebarOpen ? (
                <PanelRightClose className="w-4 h-4 text-muted-foreground" />
              ) : (
                <PanelRight className="w-4 h-4 text-muted-foreground" />
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
