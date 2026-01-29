/**
 * MessageList Component
 *
 * Renders messages with intelligent grouping:
 * - User messages: Individual bubbles
 * - Assistant responses: Group by response_id to keep text+tools+text in same bubble
 */

import React from 'react';
import { MessageBubble } from '@/components/features/chat/MessageBubble';
import { MessageGroup } from '@/components/features/chat/MessageGroup';
import type { Agent } from '@/lib/api';
import type { LocalMessage } from '@/hooks/api/useLocalMessages';
import type { Message } from '@/types/chat';
import type { SessionRole } from '@/types/session';

interface MessageListProps {
  messages: LocalMessage[];
  instanceId: string;
  role: SessionRole;
  agentColor?: string;
  agentAvatar?: string;
  userAvatar?: string;
  agents: Agent[];
  onSessionJump?: (sessionId: string) => void;
}

/**
 * Group messages by response_id for unified bubble rendering.
 * Messages with same response_id are part of the same logical response (text + tools + text).
 * Cross-session messages (with different from_instance_id) are NOT grouped together.
 */
function groupMessages(messages: LocalMessage[]): (LocalMessage | LocalMessage[])[] {
  const groups: (LocalMessage | LocalMessage[])[] = [];
  let currentGroup: LocalMessage[] = [];
  let currentResponseId: string | null = null;
  let currentFromInstanceId: string | null | undefined = null;

  for (const msg of messages) {
    if (msg.role === 'user') {
      // User message: flush current group and add user message individually
      if (currentGroup.length > 0) {
        groups.push(currentGroup);
        currentGroup = [];
        currentResponseId = null;
        currentFromInstanceId = null;
      }
      groups.push(msg);
    } else {
      // Assistant or tool message
      const msgResponseId = msg.response_id || null;
      const msgFromInstanceId = msg.from_instance_id;

      // Start new group if:
      // 1. No current group
      // 2. response_id changed
      // 3. Current message has no response_id (treat as separate)
      // 4. from_instance_id changed (cross-session boundary)
      if (
        currentGroup.length === 0 ||
        msgResponseId !== currentResponseId ||
        msgResponseId === null ||
        msgFromInstanceId !== currentFromInstanceId
      ) {
        // Flush previous group if it exists
        if (currentGroup.length > 0) {
          groups.push(currentGroup);
        }
        // Start new group
        currentGroup = [msg];
        currentResponseId = msgResponseId;
        currentFromInstanceId = msgFromInstanceId;
      } else {
        // Add to current group (same response_id and same from_instance_id)
        currentGroup.push(msg);
      }
    }
  }

  // Flush remaining group
  if (currentGroup.length > 0) {
    groups.push(currentGroup);
  }

  return groups;
}

/**
 * Convert LocalMessage to Message format for MessageBubble/MessageGroup
 */
function convertToMessage(msg: LocalMessage): Message {
  return {
    id: msg.id,
    role: msg.role,
    content: msg.content,
    timestamp: new Date(msg.timestamp),
    isStreaming: msg.isStreaming || false,
    agent_id: msg.agent_id,
    agent_name: msg.agent_name,
    from_instance_id: msg.from_instance_id,
    toolName: msg.tool_name,
    toolArgs: msg.tool_args,
    toolId: msg.tool_id,
    toolResult: msg.tool_result,
    toolError: msg.tool_error,
  };
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  instanceId,
  role,
  agentColor,
  agentAvatar,
  userAvatar,
  agents,
  onSessionJump,
}) => {
  const grouped = groupMessages(messages);

  return (
    <>
      {grouped.map((item, index) => {
        // Single message (user)
        if (!Array.isArray(item)) {
          return (
            <MessageBubble
              key={item.id}
              message={convertToMessage(item)}
              role={role}
              agentColor={agentColor}
              agentAvatar={agentAvatar}
              userAvatar={userAvatar}
              agents={agents}
              onSessionJump={onSessionJump}
              sessionId={instanceId}
            />
          );
        }

        // Group of messages (assistant + tools)
        return (
          <MessageGroup
            key={`group-${index}`}
            messages={item.map(convertToMessage)}
            role={role}
            agentColor={agentColor || '#4A90E2'}
            agentAvatar={agentAvatar || 'default-avatar'}
            agents={agents}
            onSessionJump={onSessionJump}
          />
        );
      })}
    </>
  );
};
