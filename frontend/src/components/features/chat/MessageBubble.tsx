import { motion } from 'framer-motion';
import { Avatar } from '@/ui';
import type { Message, FileAttachment as StructuredFileAttachment } from '@/types/chat';
import type { Agent } from '@/lib/api';
import type { SessionRole } from '@/types/session';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { memo } from 'react';
import { File } from '@/components/features/files/File';
import { FileErrorBoundary } from '@/components/features/files/FileErrorBoundary';
import { useOptionalFileContext } from '@/contexts/FileContext';
import { renderToolWidget } from '@/features/tool-widgets';
import { markdownComponents } from '@/lib/utils/markdownComponents';
import { getMessageSenderDisplayInfo } from '@/lib/utils/agentUtils';
import { CrossInstanceIndicator } from './CrossInstanceIndicator';

// Parse file attachments from message content
function parseFileAttachments(content: string): { text: string; files: StructuredFileAttachment[] } {
  // Match new format: [ATTACHED_FILES]...FILE_ATTACHMENT::...[/ATTACHED_FILES]
  // Allow optional whitespace/newlines around the content
  const fileAttachmentMatch = content.match(/\[ATTACHED_FILES\]\s*((?:FILE_ATTACHMENT::.+\s*)+)\[\/ATTACHED_FILES\]/);

  if (!fileAttachmentMatch) {
    // Debug: log when pattern doesn't match
    if (content.includes('FILE_ATTACHMENT::')) {
      console.log('[DEBUG] File attachment pattern found but regex failed to match');
      console.log('[DEBUG] Content:', content);
    }
    return { text: content, files: [] };
  }

  const [fullMatch, fileList] = fileAttachmentMatch;
  const messageText = content.replace(fullMatch, '').trim();

  console.log('[DEBUG] Matched file attachments:', fullMatch);
  console.log('[DEBUG] File list:', fileList);

  const files = fileList
    .split('\n')
    .filter(line => line.startsWith('FILE_ATTACHMENT::'))
    .map(line => {
      // Format: FILE_ATTACHMENT::filename.ext::12.3KB::/full/path/to/file.ext
      const parts = line.replace('FILE_ATTACHMENT::', '').split('::');
      if (parts.length !== 3) {
        console.log('[DEBUG] Invalid file line:', line, 'parts:', parts);
        return null;
      }

      const [name, sizeStr, path] = parts;
      // Convert size string to bytes (approximate)
      const size = parseSizeString(sizeStr);

      console.log('[DEBUG] Parsed file:', { name, size, path });
      return { name, size, path };
    })
    .filter((f): f is StructuredFileAttachment => f !== null);

  console.log('[DEBUG] Total files parsed:', files.length);
  return { text: messageText, files };
}

// Helper to convert size strings like "12.3KB" to bytes
function parseSizeString(sizeStr: string): number {
  const match = sizeStr.match(/^([\d.]+)(B|KB|MB)$/);
  if (!match) return 0;

  const [, numStr, unit] = match;
  const num = parseFloat(numStr);

  switch (unit) {
    case 'B': return num;
    case 'KB': return num * 1024;
    case 'MB': return num * 1024 * 1024;
    default: return 0;
  }
}

// File attachments display component
function FileAttachmentsDisplay({ files }: { files: StructuredFileAttachment[] }) {
  const fileContext = useOptionalFileContext();

  if (!fileContext?.isReady) {
    return (
      <div className="mt-2 type-body-sm text-amber-600 bg-amber-50 border border-amber-200 rounded p-2">
        ⚠️ Cannot display {files.length} file{files.length > 1 ? 's' : ''}: File context not available
      </div>
    );
  }

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {files.map((file, i) => (
        <FileErrorBoundary key={`${file.path}-${i}`}>
          <File attachment={file} mode="compact" />
        </FileErrorBoundary>
      ))}
    </div>
  );
}

// Tool call bubble component (for role='tool' messages)
function ToolCallBubble({ message }: { message: Message }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="px-5 py-2"
    >
      {renderToolWidget({
        toolName: message.toolName || 'Unknown Tool',
        toolArgs: message.toolArgs || {},
        toolId: message.toolId,
        result: message.toolResult,
        isLoading: !message.toolResult && !message.toolError, // Loading if no result yet
      })}
    </motion.div>
  );
}


// Simple content renderer without tool marker processing
function MessageContent({ content }: { content: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents} skipHtml>
      {content}
    </ReactMarkdown>
  );
}


interface MessageBubbleProps {
  message: Message;
  role?: SessionRole;
  agentColor?: string;
  agentAvatar?: string;
  agents: Agent[];
  isTyping?: boolean;
  onSessionJump?: (sessionId: string) => void;
  sessionId?: string; // Session ID for file operations
  userAvatar?: string; // User profile avatar (base64 or URL)
}

export const MessageBubble = memo(function MessageBubble({ message, role, agents, isTyping = false, userAvatar, onSessionJump }: MessageBubbleProps) {
  // Get display info for assistant messages
  const displayInfo = message.role === 'assistant'
    ? getMessageSenderDisplayInfo(message.agent_id, message.agent_name, agents)
    : { name: 'Agent', avatar: 'default-avatar', color: '#4A90E2' };

  const displayAvatar = displayInfo.avatar;
  const displayColor = displayInfo.color;
  const displayName = displayInfo.name;

  if (message.role === 'user') {
    // For cross-session messages or system messages (like reminders), show agent info instead of "You"
    // Check both from_instance_id and agent_name to handle:
    // 1. Cross-session messages (have from_instance_id)
    // 2. System messages like reminders (have agent_name but no from_instance_id)
    const isCrossSession = !!message.from_instance_id || !!message.agent_name;
    const senderInfo = isCrossSession
      ? getMessageSenderDisplayInfo(message.agent_id, message.agent_name, agents)
      : { name: 'You', avatar: 'user', color: '#6B7280' };

    return (
      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="group px-5 py-1"
      >
        <div className="w-full max-w-full flex items-start gap-2">
          {/* Avatar */}
          {isCrossSession ? (
            // Check if it's a reminder message - use alarm emoji instead of avatar
            senderInfo.name.toLowerCase().includes('reminder') ? (
              <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-amber-100 flex-shrink-0 text-xl">
                ⏰
              </div>
            ) : (
              <Avatar
                seed={senderInfo.avatar}
                size={32}
                className="w-8 h-8 flex-shrink-0 rounded-lg"
                color={senderInfo.color}
              />
            )
          ) : userAvatar && (userAvatar.startsWith('data:') || userAvatar.startsWith('http')) ? (
            <div className="w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center bg-muted/50 flex-shrink-0">
              <img
                src={userAvatar}
                alt="User"
                className="w-full h-full object-cover"
              />
            </div>
          ) : (
            <Avatar
              seed="user"
              size={32}
              className="w-8 h-8 flex-shrink-0 rounded-lg"
              color="#6B7280"
            />
          )}

          {/* Content column */}
          <div className="flex-1 min-w-0">
            {/* Name and Timestamp */}
            <div className="flex items-baseline gap-2 mb-1">
              <span className="type-subtitle text-gray-900 font-sans">{senderInfo.name}</span>
              <span className="type-caption text-gray-600">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>

            {/* Show sender instance for cross-instance messages */}
            {message.from_instance_id && (
              <CrossInstanceIndicator
                fromInstanceId={message.from_instance_id}
                onSessionJump={onSessionJump}
              />
            )}

            {/* Message Content */}
            <div className="type-body-sm leading-relaxed break-words overflow-x-auto">
              {(() => {
                const { text, files } = parseFileAttachments(message.content);
                // Combine structured attachments with legacy parsed attachments
                const allFiles = [...(message.attachments || []), ...files];

                return (
                  <>
                    {text && (
                      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents} skipHtml>
                        {text}
                      </ReactMarkdown>
                    )}
                    {allFiles.length > 0 && <FileAttachmentsDisplay files={allFiles} />}
                  </>
                );
              })()}
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  if (message.role === 'assistant') {
    // displayName is already calculated from agent_name or agent.name
    const assistantName = displayName;
    const isPM = role === 'pm';

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
                {assistantName}{isPM && ' (PM)'}
              </span>
              <span className="type-caption text-gray-600">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>

            {/* Show sender instance for cross-instance messages */}
            {message.from_instance_id && (
              <CrossInstanceIndicator
                fromInstanceId={message.from_instance_id}
                onSessionJump={onSessionJump}
              />
            )}

            {/* Message content or typing indicator */}
            {isTyping ? (
              <div className="flex gap-1">
                <motion.div
                  className="w-2 h-2 rounded-full bg-gray-400"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ repeat: Infinity, duration: 1.2, delay: 0 }}
                />
                <motion.div
                  className="w-2 h-2 rounded-full bg-gray-400"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ repeat: Infinity, duration: 1.2, delay: 0.2 }}
                />
                <motion.div
                  className="w-2 h-2 rounded-full bg-gray-400"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ repeat: Infinity, duration: 1.2, delay: 0.4 }}
                />
              </div>
            ) : message.content && (
              <div className="type-body-sm leading-relaxed break-words overflow-x-auto">
                {(() => {
                  const { text, files } = parseFileAttachments(message.content);
                  // Combine structured attachments with legacy parsed attachments
                  const allFiles = [...(message.attachments || []), ...files];

                  return (
                    <>
                      <MessageContent content={text} />
                      {allFiles.length > 0 && <FileAttachmentsDisplay files={allFiles} />}
                    </>
                  );
                })()}
              </div>
            )}
          </div>
        </div>
      </motion.div>
    );
  }

  if (message.role === 'tool') {
    return <ToolCallBubble message={message} />;
  }

  if (message.role === 'system') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="px-5 py-2"
      >
        <div className="flex items-center justify-center">
          <div className="px-4 py-1.5 bg-yellow-50 border border-yellow-200 rounded-full">
            <p className="type-caption text-yellow-800 text-center whitespace-pre-wrap">
              {message.content}
            </p>
          </div>
        </div>
      </motion.div>
    );
  }

  return null;
}, (prevProps, nextProps) => {
  // Custom comparison: only re-render if message content, id, or typing status changes
  return (
    prevProps.message.id === nextProps.message.id &&
    prevProps.message.content === nextProps.message.content &&
    prevProps.message.role === nextProps.message.role &&
    prevProps.isTyping === nextProps.isTyping &&
    prevProps.userAvatar === nextProps.userAvatar
    // Deliberately ignore agents array - doesn't affect individual message rendering
  );
});
