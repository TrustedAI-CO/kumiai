import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Truncate MCP prefix from tool names for cleaner display
 * Patterns:
 * - mcp__servername__toolname → toolname
 * - mcp__toolname → toolname
 *
 * @param toolName - The full tool name (e.g., "mcp__pm_management__spawn_session" or "mcp__spawn_instance")
 * @returns Truncated tool name (e.g., "spawn_session" or "spawn_instance")
 *
 * @example
 * truncateMcpPrefix("mcp__pm_management__spawn_session") // "spawn_session"
 * truncateMcpPrefix("mcp__spawn_instance") // "spawn_instance"
 * truncateMcpPrefix("Read") // "Read"
 * truncateMcpPrefix("mcp__agents__call_agent") // "call_agent"
 */
export function truncateMcpPrefix(toolName: string): string {
  // Handle both mcp__servername__toolname and mcp__toolname patterns
  if (toolName.startsWith('mcp__')) {
    const parts = toolName.split('__');
    // If pattern is mcp__servername__toolname (3 parts), return toolname
    if (parts.length === 3) {
      return parts[2];
    }
    // If pattern is mcp__toolname (2 parts), return toolname
    if (parts.length === 2) {
      return parts[1];
    }
  }
  return toolName;
}

/**
 * Truncate long text with ellipsis if it exceeds max length
 *
 * @param text - The text to truncate
 * @param maxLength - Maximum length before truncation (default: 30)
 * @returns Truncated text with ellipsis if needed
 *
 * @example
 * truncateText("Very long tool name here", 15) // "Very long tool..."
 * truncateText("Short", 15) // "Short"
 */
export function truncateText(text: string, maxLength: number = 30): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}
