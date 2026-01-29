/**
 * QueuePreview Component
 *
 * Displays pending queued messages with sender, timestamp, and preview
 */

import React from 'react';
import { Clock, User } from 'lucide-react';
import type { QueuedMessagePreview } from '@/types/session';

interface QueuePreviewProps {
  messages: QueuedMessagePreview[];
}

export const QueuePreview: React.FC<QueuePreviewProps> = ({ messages }) => {
  if (messages.length === 0) {
    return null;
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffSecs = Math.floor(diffMs / 1000);

      if (diffSecs < 60) {
        return 'now';
      } else if (diffSecs < 3600) {
        const mins = Math.floor(diffSecs / 60);
        return `${mins}m ago`;
      } else {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
    } catch {
      return 'now';
    }
  };

  return (
    <div className="px-4 pb-2">
      <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-2">
        {/* Header */}
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <Clock className="w-3.5 h-3.5" />
          <span>
            {messages.length === 1 ? '1 message' : `${messages.length} messages`} queued
          </span>
        </div>

        {/* Queued messages */}
        <div className="space-y-1.5 max-h-32 overflow-y-auto">
          {messages.map((msg, index) => (
            <div
              key={index}
              className="flex items-center gap-2 text-sm rounded-md border border-border bg-background px-3 py-2 animate-in fade-in slide-in-from-bottom-1"
            >
              {/* Sender */}
              <div className="flex items-center gap-1.5 shrink-0">
                <User className="w-3 h-3 text-muted-foreground" />
                <span className="font-medium text-foreground">
                  {msg.sender_name || 'User'}
                </span>
                {msg.sender_session_id && (
                  <span className="text-muted-foreground font-mono text-xs">
                    ({msg.sender_session_id.substring(0, 6)})
                  </span>
                )}
              </div>

              {/* Message preview */}
              <span className="truncate text-muted-foreground flex-1">
                {msg.content_preview}
              </span>

              {/* Time */}
              <span className="text-muted-foreground text-xs shrink-0">
                {formatTimestamp(msg.timestamp)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
