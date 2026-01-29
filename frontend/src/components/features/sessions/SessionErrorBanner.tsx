/**
 * SessionErrorBanner Component
 *
 * Error banner for sessions in error state
 * Consolidates duplicate banners from PMChat, SkillAssistantChat, AgentAssistantChat
 */
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SessionErrorBannerProps {
  error?: string | null;
  defaultMessage?: string;
  className?: string;
}

export function SessionErrorBanner({
  error,
  defaultMessage = 'This session encountered an error. Chat history is read-only.',
  className,
}: SessionErrorBannerProps) {
  return (
    <div className={cn('flex-shrink-0 bg-red-50 border-b border-red-200 px-4 py-2', className)}>
      <div className="flex items-start gap-2">
        <div className="w-5 h-5 mt-0.5 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
          <X className="w-3 h-3 text-red-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-red-900">Session Error</p>
          <p className="text-xs text-red-700 mt-0.5">
            {error || defaultMessage}
          </p>
        </div>
      </div>
    </div>
  );
}
