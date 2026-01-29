import { cn } from '@/lib/utils';
import type React from 'react';

interface StatusBadgeProps {
  status: string;
  color: string;
  icon: React.ComponentType<{ className?: string }>;
  animated?: boolean;
  showIcon?: boolean;
  className?: string;
  align?: 'left' | 'right';
}

/**
 * Displays a status badge with an icon and label.
 * Used to show agent/session status with consistent styling.
 */
export function StatusBadge({ status, color, icon: Icon, animated = false, showIcon = true, className, align = 'right' }: StatusBadgeProps) {
  return (
    <div className={cn(
      'flex items-center gap-2',
      align === 'right' ? 'justify-end' : 'justify-start',
      className
    )}>
      <span
        className="type-label px-2 py-1 rounded capitalize"
        style={{
          backgroundColor: color + '20',
          color,
        }}
      >
        {status}
      </span>
      {showIcon && (
        <div style={{ color }}>
          <Icon
            className={cn(
              'w-5 h-5',
              animated && 'animate-spin'
            )}
          />
        </div>
      )}
    </div>
  );
}
