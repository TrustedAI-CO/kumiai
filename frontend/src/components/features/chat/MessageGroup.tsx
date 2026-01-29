/**
 * MessageGroup component
 *
 * Displays multiple messages (text + tools) from the same response_id in a unified bubble.
 */

import { motion } from 'framer-motion';
import { Avatar } from '@/ui';
import type { Message } from '@/types/chat';
import type { Agent } from '@/lib/api';
import type { SessionRole } from '@/types/session';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { renderToolWidget } from '@/features/tool-widgets';
import { markdownComponents } from '@/lib/utils/markdownComponents';
import { getMessageSenderDisplayInfo } from '@/lib/utils/agentUtils';
import { CrossInstanceIndicator } from './CrossInstanceIndicator';

interface MessageGroupProps {
  messages: Message[];
  role: SessionRole;
  agentColor: string;
  agentAvatar: string;
  agents: Agent[];
  onSessionJump?: (sessionId: string) => void;
}

export function MessageGroup({ messages, role, agentColor, agentAvatar, agents, onSessionJump }: MessageGroupProps) {
  if (messages.length === 0) return null;

  // Get display info from first message
  // Both assistant and tool messages can have agent_id/agent_name
  const firstMessage = messages[0];
  const displayInfo = (firstMessage.role === 'assistant' || firstMessage.role === 'tool')
    ? getMessageSenderDisplayInfo(firstMessage.agent_id, firstMessage.agent_name, agents)
    : { name: 'Agent', avatar: agentAvatar, color: agentColor };

  const displayAvatar = displayInfo.avatar;
  const displayColor = displayInfo.color;
  const displayName = displayInfo.name;
  const isPM = role === 'pm';

  // Use timestamp from first message
  const timestamp = firstMessage.timestamp;

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="group px-5 py-1"
    >
      <div className="w-full max-w-full flex items-start gap-2">
        {/* Avatar */}
        <Avatar
          seed={displayAvatar}
          size={32}
          className="w-8 h-8 flex-shrink-0 rounded-lg"
          color={displayColor}
        />

        {/* Content column */}
        <div className="flex-1 min-w-0">
          {/* Name and Timestamp */}
          <div className="flex items-baseline gap-2 mb-1">
            <span className="type-subtitle text-gray-900 font-sans">
              {displayName}{isPM && ' (PM)'}
            </span>
            <span className="type-caption text-gray-600">
              {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>

          {/* Show sender instance for cross-instance messages */}
          {firstMessage.from_instance_id && (
            <CrossInstanceIndicator
              fromInstanceId={firstMessage.from_instance_id}
              onSessionJump={onSessionJump}
            />
          )}

          {/* Render all messages in sequence */}
          <div className="space-y-2">
            {messages.map((msg, index) => {
              if (msg.role === 'assistant' && msg.content) {
                // Text content
                return (
                  <div key={msg.id || index} className="type-body-sm leading-relaxed break-words overflow-x-auto">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents} skipHtml>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                );
              } else if (msg.role === 'tool') {
                // Tool use - render using widget system
                return (
                  <div key={msg.id || index}>
                    {renderToolWidget({
                      toolName: msg.toolName || 'Unknown Tool',
                      toolArgs: msg.toolArgs || {},
                      toolId: msg.toolId,
                      result: msg.toolResult,
                      isLoading: !msg.toolResult && !msg.toolError, // Loading if no result yet
                    })}
                  </div>
                );
              }
              return null;
            })}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
