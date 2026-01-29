/**
 * Chat and messaging type definitions
 */

export interface ChatContext {
  role: 'specialist' | 'pm' | 'assistant' | 'agent_assistant' | 'skill_assistant' | null;
  name?: string;
  description?: string;
  data?: Record<string, unknown>;
}

export interface ToolUse {
  toolName: string;
  toolArgs?: Record<string, unknown>;
  toolResult?: string; // Tool execution result text (for extracting metadata like instance_id)
}

export interface FileAttachment {
  path: string;
  name: string;
  size: number;
  mimeType?: string;
  thumbnail?: string; // Optional thumbnail URL for images
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  toolName?: string; // For tool messages
  toolArgs?: Record<string, unknown>; // For tool messages
  toolId?: string; // For tool messages - Claude's tool use ID
  toolResult?: string; // For tool messages - Tool execution result
  toolError?: boolean; // For tool messages - Whether the tool execution failed
  attachments?: FileAttachment[]; // Structured file attachments
  timestamp: Date;
  isStreaming?: boolean;
  agentName?: string; // Name of the subagent that sent this message (deprecated - use agent_name)
  streamedViaDeltas?: boolean; // True if message was built via stream_delta events
  agent_id?: string; // Source of truth for which agent sent the message
  agent_name?: string; // Display name of the sending agent
  from_instance_id?: string; // Session ID where message originated (for cross-session routing)
}
