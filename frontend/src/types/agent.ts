/**
 * Agent-related type definitions
 */

export type AgentStatus = 'idle' | 'thinking' | 'working' | 'waiting' | 'completed' | 'error';

export interface StatusConfig {
  color: string;
  iconKey: AgentStatus;
}

export const STATUS_COLORS: Record<AgentStatus, string> = {
  idle: 'text-gray-500',
  thinking: 'text-blue-500',
  working: 'text-green-500',
  waiting: 'text-yellow-500',
  completed: 'text-emerald-500',
  error: 'text-red-500',
} as const;
