import { ReactNode } from 'react';
import { PanelLeft, PanelRight, PanelLeftClose, PanelRightClose, ChevronRight, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BreadcrumbSegment {
  label: string;
  onClick?: () => void;
}

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
  breadcrumb?: string;
  breadcrumbOnClick?: () => void;
  breadcrumbs?: BreadcrumbSegment[];
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
  breadcrumb,
  breadcrumbOnClick,
  breadcrumbs,
}: MainHeaderProps) {
  const hasBreadcrumb = !!(breadcrumb || breadcrumbs?.length);

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

          {hasBreadcrumb ? (
            <div className="flex items-center gap-2 min-w-0 flex-1">
              {breadcrumbs
                ? breadcrumbs.map((segment, i) => (
                    <span key={i} className="flex items-center gap-2 flex-shrink-0">
                      <button
                        type="button"
                        onClick={segment.onClick}
                        disabled={!segment.onClick}
                        className={cn(
                          'type-body-sm text-muted-foreground',
                          segment.onClick && 'hover:text-foreground transition-colors cursor-pointer'
                        )}
                      >
                        {segment.label}
                      </button>
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    </span>
                  ))
                : (
                    <span className="flex items-center gap-2 flex-shrink-0">
                      <button
                        type="button"
                        onClick={breadcrumbOnClick}
                        disabled={!breadcrumbOnClick}
                        className={cn(
                          'type-body-sm text-muted-foreground',
                          breadcrumbOnClick && 'hover:text-foreground transition-colors cursor-pointer'
                        )}
                      >
                        {breadcrumb}
                      </button>
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    </span>
                  )
              }
              <h1 className="type-body-sm text-muted-foreground truncate">{title}</h1>
            </div>
          ) : (
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
          {hasBreadcrumb && (
            <>
              {icon && <div className="flex-shrink-0">{icon}</div>}
              {showBackButton && onBack && (
                <button
                  onClick={onBack}
                  className="p-1.5 hover:bg-muted rounded-md transition-colors"
                  aria-label="Close"
                  title="Close"
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
