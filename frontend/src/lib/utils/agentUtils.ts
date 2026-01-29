import type { Agent, AgentInstance } from '@/lib/api';

/**
 * Agent display information extracted from agent instance and metadata
 */
export interface AgentDisplayInfo {
  name: string;
  avatar: string;
  color: string;
}

/**
 * Get display information for an agent instance.
 * Looks up agent metadata to get proper name, color, and avatar.
 *
 * @param agentInstance - The agent instance (can be null/undefined)
 * @param agents - Optional array of agent metadata to look up colors and names
 * @returns Display information with name, avatar seed, and color
 */
export function getAgentDisplayInfo(
  agentInstance: AgentInstance | null | undefined,
  agents?: Agent[]
): AgentDisplayInfo {
  // Default values
  const defaultInfo: AgentDisplayInfo = {
    name: 'Unknown Agent',
    avatar: 'default',
    color: '#4A90E2',
  };

  if (!agentInstance) {
    return defaultInfo;
  }

  // Start with agent_id as avatar seed
  const avatar = agentInstance.agent_id || 'default';
  let name = agentInstance.agent_id || 'Unknown Agent';
  let color = '#4A90E2';

  // Look up agent metadata if available
  if (agentInstance.agent_id && agents) {
    const agentMetadata = agents.find(a => a.id === agentInstance.agent_id);
    if (agentMetadata) {
      name = agentMetadata.name;
      color = agentMetadata.icon_color || '#4A90E2';
    }
  }

  return { name, avatar, color };
}

/**
 * Get display information for a message sender (from agent_id in message).
 * Used by message components that need to show agent info.
 *
 * @param agentId - The agent ID from the message
 * @param agentName - Optional agent name from the message
 * @param agents - Optional array of agent metadata
 * @returns Display information with name, avatar seed, and color
 */
export function getMessageSenderDisplayInfo(
  agentId: string | null | undefined,
  agentName: string | null | undefined,
  agents?: Agent[]
): AgentDisplayInfo {
  // For messages without agentId (e.g., system reminders), use agent_name as avatar seed
  const isReminder = agentName?.toLowerCase().includes('reminder');

  // If no agentId, return default info based on agent_name
  if (!agentId) {
    const avatarSeed = agentName?.toLowerCase().replace(/\s+/g, '-') || 'default';
    return {
      name: agentName || 'Agent',
      avatar: avatarSeed,
      color: isReminder ? '#F59E0B' : '#4A90E2', // Amber for reminders, blue for others
    };
  }

  // When agentId exists, always use it as avatar seed for consistency
  let name = agentName || agentId;
  let color = '#4A90E2';

  // Look up agent metadata if available
  if (agents) {
    const agentMetadata = agents.find(a => a.id === agentId);
    if (agentMetadata) {
      // Use agent_name from message if available, otherwise use metadata name
      name = agentName || agentMetadata.name;
      color = agentMetadata.icon_color || '#4A90E2';
    }
  }

  return {
    name,
    avatar: agentId, // Always use agentId as avatar seed for consistency
    color,
  };
}
