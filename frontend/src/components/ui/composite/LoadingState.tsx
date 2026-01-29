/**
 * LoadingState Component
 *
 * Centralized loading state display with spinner and optional message
 */
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingStateProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizes = {
  sm: 'w-5 h-5',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

export function LoadingState({
  message = 'Loading...',
  size = 'md',
  className
}: LoadingStateProps) {
  return (
    <div className={cn('flex items-center justify-center h-full', className)}>
      <div className="text-center">
        <Loader2 className={cn(sizes[size], 'mx-auto mb-3 text-gray-400 animate-spin')} />
        {message && <p className="type-body-sm text-gray-500">{message}</p>}
      </div>
    </div>
  );
}
