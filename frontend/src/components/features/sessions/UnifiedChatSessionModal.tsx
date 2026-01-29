/**
 * UnifiedChatSessionModal Component
 *
 * Modal wrapper for specialist (multi-agent) sessions using UnifiedSessionChat.
 * Replaces ChatSessionModal with unified architecture.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { UnifiedSessionChat } from '@/components/features/sessions/UnifiedSessionChat';
import { api, type AgentInstance, type Agent } from '@/lib/api';
import { useUser } from '@/contexts/UserContext';
import { LoadingState } from '@/ui';

interface UnifiedChatSessionModalProps {
  agent: AgentInstance | null;
  agents: Agent[];
  onClose: () => void;
  inline?: boolean; // If true, render as inline component instead of modal
  onFilesCommitted?: () => void; // Callback when files are uploaded and committed
  onSessionJump?: (sessionId: string) => void; // Callback to jump to another session
}

export function UnifiedChatSessionModal({
  agent,
  agents,
  onClose,
  inline = false,
  onFilesCommitted,
  onSessionJump,
}: UnifiedChatSessionModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<string>('idle');
  const { profile } = useUser();

  // Update session status when agent changes
  useEffect(() => {
    if (!agent) {
      setSessionStatus('idle');
      setError(null);
      return;
    }

    setSessionStatus(agent.status || 'idle');

    // If session is in error state, set error message
    if (agent.status === 'error') {
      setError('Agent session encountered an error. Chat history is available in read-only mode.');
    } else {
      setError(null);
    }
  }, [agent?.instance_id, agent?.status]);

  // Handle Esc key to close modal
  useEffect(() => {
    if (!agent || inline) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [agent, onClose, inline]);

  if (!agent) return null;

  // Chat content component (shared between inline and modal)
  const chatContent = (
    <div
      className={`bg-white flex flex-col overflow-hidden max-w-full ${
        inline ? 'w-full h-full' : 'rounded-2xl border border-primary shadow-2xl w-full max-w-6xl h-[70vh]'
      }`}
      role="dialog"
      aria-label="Agent chat session"
    >
      {/* Error banner for sessions in error state */}
      {sessionStatus === 'error' && error && (
        <div className="flex-shrink-0 bg-red-50 border-b border-red-200 px-4 py-2 w-full max-w-full">
          <div className="flex items-start gap-2">
            <div className="w-5 h-5 mt-0.5 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
              <X className="w-3 h-3 text-red-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-red-900">Session Error</p>
              <p className="text-xs text-red-700 mt-0.5">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Chat Interface */}
      <div className="flex-1 overflow-hidden w-full max-w-full">
        {isLoading ? (
          <LoadingState message="Loading session..." />
        ) : (
          <UnifiedSessionChat
            instanceId={agent.instance_id}
            role="specialist"
            className="h-full"
            readOnly={sessionStatus === 'error'}
            showHeader={!inline}
            userAvatar={profile?.avatar || undefined}
            onClose={onClose}
            onFilesCommitted={onFilesCommitted}
            onSessionJump={onSessionJump}
            initialSessionDescription={agent.current_session_description}
          />
        )}
      </div>
    </div>
  );

  // Render inline or as modal
  if (inline) {
    return chatContent;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-[101]"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
        >
          {chatContent}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
