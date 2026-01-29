/**
 * ChatHeader Component
 *
 * Displays chat header with title, status, and actions.
 */

import React from 'react';
import { X, Loader2, StopCircle, Plus } from 'lucide-react';
import { Avatar } from '@/ui';

interface ChatHeaderProps {
  title: string;
  subtitle?: string;
  agentAvatar?: string;
  agentColor?: string;
  isProcessing?: boolean;
  onClose?: () => void;
  onInterrupt?: () => void;
  onNewSession?: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  title,
  subtitle,
  agentAvatar,
  agentColor,
  isProcessing = false,
  onClose,
  onInterrupt,
  onNewSession,
}) => {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
      <div className="flex items-center gap-3 flex-1">
        {/* Agent Avatar */}
        {agentAvatar && (
          <Avatar
            seed={agentAvatar}
            size={32}
            className="w-8 h-8 flex-shrink-0 rounded"
            color={agentColor || '#4A90E2'}
          />
        )}

        {/* Title and subtitle */}
        <div className="flex-1">
          <h3 className="type-subtitle text-gray-900">{title}</h3>
          {subtitle && (
            <p className="type-caption text-gray-500 truncate">{subtitle}</p>
          )}
        </div>

        {/* Status indicator */}
        {isProcessing && (
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {/* New Session button */}
        {onNewSession && (
          <button
            onClick={onNewSession}
            className="p-2 hover:bg-gray-100 rounded text-gray-600 hover:text-gray-700 transition-colors"
            aria-label="New Session"
            title="Start new session"
          >
            <Plus className="w-5 h-5" />
          </button>
        )}

        {/* Interrupt button (only shown when processing) */}
        {isProcessing && onInterrupt && (
          <button
            onClick={onInterrupt}
            className="p-2 hover:bg-gray-100 rounded text-red-600 hover:text-red-700 transition-colors"
            aria-label="Interrupt"
            title="Stop current operation"
          >
            <StopCircle className="w-5 h-5" />
          </button>
        )}

        {/* Close button */}
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded text-gray-600 hover:text-gray-700 transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
};
