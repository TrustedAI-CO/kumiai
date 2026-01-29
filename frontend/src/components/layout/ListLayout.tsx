import { ReactNode } from 'react';
import { Search, LucideIcon } from 'lucide-react';
import { LoadingState, EmptyState } from '@/components/ui';
import { cn } from '@/lib/utils';

interface ActionButton {
  icon: LucideIcon;
  onClick: () => void;
  title: string;
  variant?: 'primary' | 'secondary';
}

interface ListLayoutProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  searchPlaceholder: string;
  loading: boolean;
  isEmpty: boolean;
  emptyIcon: LucideIcon;
  emptyTitle: string;
  emptyDescription: string;
  actionButtons: ActionButton[];
  children: ReactNode;
  isMobile?: boolean;
}

/**
 * Shared layout component for list views (Projects, Agents, Skills)
 * Provides consistent search bar, loading/empty states, and action buttons
 */
export function ListLayout({
  searchQuery,
  onSearchChange,
  searchPlaceholder,
  loading,
  isEmpty,
  emptyIcon,
  emptyTitle,
  emptyDescription,
  actionButtons,
  children,
  isMobile = false,
}: ListLayoutProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Search Bar */}
      <div className={cn(
        "sticky top-0 z-10 flex-shrink-0 bg-gray-50 flex items-center",
        isMobile ? "p-4" : "h-12 px-2 lg:px-3"
      )}>
        <div className="flex items-center gap-2 w-full">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder={searchPlaceholder}
              className={cn(
                "input-search",
                isMobile && "py-2 rounded-lg"
              )}
            />
          </div>
          {actionButtons.map((button, index) => {
            const Icon = button.icon;
            const isPrimary = button.variant === 'primary';
            return (
              <button
                key={index}
                onClick={button.onClick}
                className={cn(
                  "flex-shrink-0 p-1.5 transition-colors rounded-md",
                  isPrimary
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "bg-background border border-border text-foreground hover:bg-muted"
                )}
                title={button.title}
              >
                <Icon className="w-4 h-4" />
              </button>
            );
          })}
        </div>
      </div>

      {/* List Content */}
      <div className={cn("flex-1 overflow-y-auto", isMobile ? "p-2" : "p-2")}>
        {loading ? (
          <LoadingState message={`Loading ${searchPlaceholder.toLowerCase().replace('search ', '')}...`} />
        ) : isEmpty ? (
          <EmptyState
            icon={emptyIcon}
            title={emptyTitle}
            description={emptyDescription}
            centered
          />
        ) : (
          children
        )}
      </div>
    </div>
  );
}
