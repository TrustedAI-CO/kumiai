/**
 * EmptyState Component
 *
 * Centralized empty state display using shadcn Empty components
 */
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from '../primitives/empty';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  isLoading?: boolean;
  className?: string;
  centered?: boolean;
  iconSize?: 'sm' | 'md' | 'lg';
  action?: React.ReactNode;
}

const iconSizeClasses = {
  sm: 'size-4',
  md: 'size-6',
  lg: 'size-8',
};

export function EmptyState({
  icon: Icon,
  title,
  description,
  isLoading = false,
  className = '',
  centered = false,
  iconSize = 'md',
  action
}: EmptyStateProps) {
  return (
    <Empty
      className={cn(
        centered && 'h-full',
        className
      )}
    >
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <Icon
            className={cn(
              iconSizeClasses[iconSize],
              isLoading && 'animate-pulse'
            )}
          />
        </EmptyMedia>
        <EmptyTitle>{title}</EmptyTitle>
        {description && <EmptyDescription>{description}</EmptyDescription>}
      </EmptyHeader>
      {action && (
        <EmptyContent>
          {action}
        </EmptyContent>
      )}
    </Empty>
  );
}
