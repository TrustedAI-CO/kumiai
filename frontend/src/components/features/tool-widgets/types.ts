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
}

export interface ParsedResult {
  content: string;
  isError: boolean;
}
