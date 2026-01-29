import { ReactNode, HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface BaseCardProps extends HTMLAttributes<HTMLDivElement> {
  isSelected?: boolean;
  isHoverable?: boolean;
  isDanger?: boolean;
  children: ReactNode;
  className?: string;
}

/**
 * BaseCard - Shared card component with consistent shadcn styling
 *
 * Provides uniform styling for all card components in the left panel.
 * Custom implementation to ensure complete styling consistency.
 */
export function BaseCard({
  isSelected = false,
  isHoverable = true,
  isDanger = false,
  children,
  className,
  ...props
}: BaseCardProps) {
  return (
    <div
      className={cn(
        // Base styles
        'rounded-lg border bg-card text-card-foreground shadow-sm',
        // Interactive styles
        'cursor-pointer transition-all duration-200',
        // Hover state
        isHoverable && 'hover:shadow-md',
        // Selection state
        isSelected && 'border-primary shadow-md bg-primary/5',
        // Default hover for non-selected
        !isSelected && isHoverable && !isDanger && 'hover:border-primary/50',
        // Danger state
        isDanger && 'hover:border-destructive hover:bg-destructive/5',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
