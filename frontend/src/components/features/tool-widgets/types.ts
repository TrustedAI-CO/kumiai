/**
 * Shared types for tool widgets
 */

export interface ToolWidgetProps {
  toolName: string;
  toolArgs: Record<string, unknown>;
  toolId?: string;
  result?: any;
  isLoading?: boolean;
  sessionId?: string;
  isLatestMessage?: boolean; // Whether this is the most recent message in the conversation
}

export interface ParsedResult {
  content: string;
  isError: boolean;
}
