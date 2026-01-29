/**
 * CrossInstanceIndicator Component
 *
 * Displays "From instance" badge for cross-session messages
 * Consolidates duplicate code from MessageBubble.tsx (appears 3x)
 */
import { cn } from '@/lib/utils';

interface CrossInstanceIndicatorProps {
  fromInstanceId: string;
  onSessionJump?: (sessionId: string) => void;
  className?: string;
}

export function CrossInstanceIndicator({
  fromInstanceId,
  onSessionJump,
  className,
}: CrossInstanceIndicatorProps) {
  return (
    <div className={cn('text-xs text-gray-500 mb-1.5 italic', className)}>
      <span className="font-medium">From</span>{' '}
      {onSessionJump ? (
        <button
          onClick={() => onSessionJump(fromInstanceId)}
          className="font-mono text-blue-600 hover:text-blue-800 hover:underline"
          title={`Jump to instance ${fromInstanceId}`}
        >
          {fromInstanceId.slice(0, 8)}
        </button>
      ) : (
        <span className="font-mono" title={fromInstanceId}>
          {fromInstanceId.slice(0, 8)}
        </span>
      )}
    </div>
  );
}
