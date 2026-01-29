/**
 * Shared Component Constants
 *
 * Common mappings and constants used across multiple components
 */
import {
  Moon,
  Loader2,
  Settings,
  MessageCircle,
  CheckCircle,
  XCircle,
  Ban,
  Sparkles,
} from 'lucide-react';

/**
 * Status icon mapping
 * Used by AgentCard, SessionCard, and other status-displaying components
 */
export const STATUS_ICONS = {
  idle: Moon,
  thinking: Loader2,
  working: Settings,
  waiting: MessageCircle,
  completed: CheckCircle,
  error: XCircle,
  cancelled: Ban,
  initializing: Sparkles,
} as const;

export type StatusType = keyof typeof STATUS_ICONS;

/**
 * Determine if a status should have animated icon
 */
export const isAnimatedStatus = (status: string): boolean => {
  return status === 'thinking' || status === 'working';
};

/**
 * Default agent color
 */
export const DEFAULT_AGENT_COLOR = '#4A90E2';

/**
 * Status color mapping
 * Used to style status badges based on status type
 */
export const STATUS_COLORS = {
  idle: '#6B7280',        // Gray - neutral, not active
  thinking: '#3B82F6',    // Blue - processing, cognitive work
  working: '#F59E0B',     // Orange - active work in progress
  waiting: '#EAB308',     // Yellow - waiting for something
  completed: '#10B981',   // Green - success
  error: '#EF4444',       // Red - error state
  cancelled: '#9CA3AF',   // Light gray - cancelled
  initializing: '#8B5CF6', // Purple - initializing
} as const;

/**
 * Get status color by status string
 */
export const getStatusColor = (status: string): string => {
  return STATUS_COLORS[status as StatusType] || STATUS_COLORS.idle;
};
