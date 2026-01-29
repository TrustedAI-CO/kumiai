/**
 * Shared types for tool widgets
 */

export interface ToolWidgetProps {
  toolName: string;
  toolArgs: Record<string, unknown>;
  toolId?: string;
  result?: any;
  isLoading?: boolean;
}

export interface ParsedResult {
  content: string;
  isError: boolean;
}
