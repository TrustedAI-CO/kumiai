/**
 * Unified session types for all session roles.
 *
 * Defines types for specialist, PM, and assistant sessions.
 */

import { Users, Briefcase, MessageCircle, User, Wrench, LucideIcon } from 'lucide-react';

export type SessionRole = 'pm' | 'specialist' | 'assistant' | 'agent_assistant' | 'skill_assistant';

export type SessionStatus = 'initializing' | 'working' | 'idle' | 'error';

export interface SessionConfig {
  role: SessionRole;
  project_path: string;
  selected_specialists?: string[];
  initial_prompt?: string;
  session_description?: string;
}

export interface SessionInstance {
  instance_id: string;
  role: SessionRole;
  session_id?: string; // Claude SDK session ID
  project_path: string;
  selected_specialists?: string[];
  status: SessionStatus;
  auto_started: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ToolUse {
  name: string;
  id: string;
  input: Record<string, any>;
}

export interface SessionMessage {
  id?: string; // UUID string from database
  instance_id: string;
  role: 'user' | 'tool';
  content: string;
  tool_name?: string; // For tool messages
  tool_args?: ToolUse[]; // Array of tool uses from Claude API (for tool messages)
  tool_result?: string; // For tool messages - Tool execution result
  tool_error?: boolean; // For tool messages - Whether the tool execution failed
  agent_id?: string; // Source of truth for which agent sent the message
  agent_name?: string; // Display name of the sending agent
  from_instance_id?: string; // Session ID where message originated (for cross-session routing)
  sequence?: number; // Execution order within a response (for ordering tools with text)
  timestamp: string;
  content_type?: string; // "text" or "tool_use" - categorizes content blocks
  response_id?: string; // UUID shared by all blocks in same response
}

// Unified event types from SessionStreamManager
export type SessionEventType =
  | 'stream_delta'
  | 'content_block'
  | 'tool_use'
  | 'tool_complete'
  | 'agent_started'
  | 'agent_delta'
  | 'agent_text'
  | 'agent_tool_use'
  | 'agent_response_complete'
  | 'agent_completed'
  | 'result'
  | 'auto_save'
  | 'status_change'
  | 'error'
  | 'message_complete'
  | 'cancelled'
  | 'user_notification'
  | 'user_message'
  | 'queue_status'
  | 'session_status'
  | 'keepalive';

export interface BaseSessionEvent {
  type: SessionEventType;
  role: SessionRole;
  timestamp: string;
  event_id?: string; // Optional unique event ID for deduplication
  sequence?: number; // Optional sequence number for ordering
  metadata?: Record<string, any>;
}

export interface StreamDeltaEvent extends BaseSessionEvent {
  type: 'stream_delta';
  content: string;
}

export interface ContentBlockEvent extends BaseSessionEvent {
  type: 'content_block';
  content: string;
  block_type: 'text' | 'tool';
  agent_id?: string;
  agent_name?: string;
  response_id?: string;
}

export interface ToolUseEvent extends BaseSessionEvent {
  type: 'tool_use';
  tool_use_id: string;
  tool_name: string; // Backend sends snake_case
  tool_input: Record<string, unknown>;
  response_id?: string;
  agent_id?: string;
  agent_name?: string;
}

export interface ToolCompleteEvent extends BaseSessionEvent {
  type: 'tool_complete';
  tool_use_id: string;
  result?: string; // Tool execution result
  is_error?: boolean; // Whether the tool execution failed
}

export interface AgentStartedEvent extends BaseSessionEvent {
  type: 'agent_started';
  agentName: string;
}

export interface AgentDeltaEvent extends BaseSessionEvent {
  type: 'agent_delta';
  agentName: string;
  content: string;
}

export interface AgentTextEvent extends BaseSessionEvent {
  type: 'agent_text';
  agentName: string;
  content: string;
}

export interface AgentToolUseEvent extends BaseSessionEvent {
  type: 'agent_tool_use';
  agentName: string;
  toolName: string;
}

export interface AgentResponseCompleteEvent extends BaseSessionEvent {
  type: 'agent_response_complete';
  agentName: string;
}

export interface AgentCompletedEvent extends BaseSessionEvent {
  type: 'agent_completed';
  agentName: string;
}

export interface ResultEvent extends BaseSessionEvent {
  type: 'result';
  status: 'completed' | 'error';
}

export interface AutoSaveEvent extends BaseSessionEvent {
  type: 'auto_save';
  auto_save_type: 'skill' | 'agent';
  item_id: string;
}

export interface StatusChangeEvent extends BaseSessionEvent {
  type: 'status_change';
  status: SessionStatus;
}

export interface ErrorEvent extends BaseSessionEvent {
  type: 'error';
  error: string;
}

export interface MessageCompleteEvent extends BaseSessionEvent {
  type: 'message_complete';
}

export interface CancelledEvent extends BaseSessionEvent {
  type: 'cancelled';
}

export interface UserNotificationEvent extends BaseSessionEvent {
  type: 'user_notification';
  title: string;
  message: string;
  project_name: string;
  priority: 'low' | 'normal' | 'high';
}

export interface UserMessageEvent extends Omit<BaseSessionEvent, 'role' | 'timestamp'> {
  type: 'user_message';
  role?: SessionRole;
  message_id: string;
  content: string;
  agent_id?: string;
  agent_name?: string;
  from_instance_id?: string;
  timestamp: string;
}

export interface QueuedMessagePreview {
  sender_name?: string;
  sender_session_id?: string;
  content_preview: string;
  timestamp: string;
}

export interface QueueStatusEvent extends BaseSessionEvent {
  type: 'queue_status';
  messages?: QueuedMessagePreview[];
}

export interface KeepaliveEvent {
  type: 'keepalive';
}

export type SessionEvent =
  | StreamDeltaEvent
  | ContentBlockEvent
  | ToolUseEvent
  | ToolCompleteEvent
  | AgentStartedEvent
  | AgentDeltaEvent
  | AgentTextEvent
  | AgentToolUseEvent
  | AgentResponseCompleteEvent
  | AgentCompletedEvent
  | ResultEvent
  | AutoSaveEvent
  | StatusChangeEvent
  | ErrorEvent
  | MessageCompleteEvent
  | CancelledEvent
  | UserNotificationEvent
  | UserMessageEvent
  | QueueStatusEvent
  | KeepaliveEvent;

// Message filtering configuration
export interface MessageFilterConfig {
  showRoles: Array<'user' | 'tool'>;
  showAgentNamesOnly?: string[] | null;
  hideSpecialist: boolean;
}

// Role configuration hints for UI
export interface RoleUIConfig {
  displayName: string;
  icon: string;
  messageFilter: MessageFilterConfig;
  supportsSpecialists: boolean;
  autoSave: boolean;
  autoSaveType?: 'skill' | 'agent';
}

// Role configurations for each session type
export const ROLE_UI_CONFIGS: Record<SessionRole, RoleUIConfig> = {
  specialist: {
    displayName: 'Specialist',
    icon: 'users',
    messageFilter: {
      showRoles: ['user', 'tool'],
      showAgentNamesOnly: null, // Show all specialists
      hideSpecialist: false, // Show all messages including specialist
    },
    supportsSpecialists: true,
    autoSave: false,
  },
  pm: {
    displayName: 'Project Manager',
    icon: 'briefcase',
    messageFilter: {
      showRoles: ['user', 'tool'],
      showAgentNamesOnly: null,
      hideSpecialist: false,
    },
    supportsSpecialists: false,
    autoSave: false,
  },
  skill_assistant: {
    displayName: 'Skill Assistant',
    icon: 'wrench',
    messageFilter: {
      showRoles: ['user', 'tool'],
      showAgentNamesOnly: null,
      hideSpecialist: false,
    },
    supportsSpecialists: false,
    autoSave: true,
    autoSaveType: 'skill',
  },
  agent_assistant: {
    displayName: 'Agent Assistant',
    icon: 'user',
    messageFilter: {
      showRoles: ['user', 'tool'],
      showAgentNamesOnly: null,
      hideSpecialist: false,
    },
    supportsSpecialists: false,
    autoSave: true,
    autoSaveType: 'agent',
  },
  assistant: {
    displayName: 'Assistant',
    icon: 'message-circle',
    messageFilter: {
      showRoles: ['user', 'tool'],
      showAgentNamesOnly: null,
      hideSpecialist: false,
    },
    supportsSpecialists: false,
    autoSave: false,
  },
};

// Helper function to filter messages based on role
export function filterMessagesByRole(
  messages: SessionMessage[],
  role: SessionRole
): SessionMessage[] {
  const config = ROLE_UI_CONFIGS[role];
  const filter = config.messageFilter;

  return messages.filter((msg) => {
    // Filter by role
    if (!filter.showRoles.includes(msg.role as any)) {
      return false;
    }

    // Filter by agent names if specified
    if (filter.showAgentNamesOnly && msg.agent_name) {
      return filter.showAgentNamesOnly.includes(msg.agent_name);
    }

    return true;
  });
}

// Icon mapping for role icons
const ROLE_ICONS: Record<string, LucideIcon> = {
  users: Users,
  briefcase: Briefcase,
  'message-circle': MessageCircle,
  user: User,
  wrench: Wrench,
};

// Helper function to get role icon component
export function getRoleIcon(iconName: string): LucideIcon {
  return ROLE_ICONS[iconName] || MessageCircle;
}

// Helper function to get role config
export function getRoleConfig(role: SessionRole): RoleUIConfig {
  return ROLE_UI_CONFIGS[role];
}
