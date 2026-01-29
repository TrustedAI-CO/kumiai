import { Server } from 'lucide-react';
import { GenericListSelector } from '@/ui';
import type { McpServer } from '@/lib/api';

interface McpServerSelectorProps {
  availableServers: McpServer[];
  selectedServerIds: string[];
  onAddServer: (serverId: string) => void;
  onRemoveServer: (serverId: string) => void;
  isEditing: boolean;
}

/**
 * MCP server selector component using the generic list selector.
 * Displays available MCP servers and allows adding/removing them.
 */
export function McpServerSelector({
  availableServers,
  selectedServerIds,
  onAddServer,
  onRemoveServer,
  isEditing,
}: McpServerSelectorProps) {
  return (
    <GenericListSelector
      availableItems={availableServers}
      selectedItemIds={selectedServerIds}
      onAddItem={onAddServer}
      onRemoveItem={onRemoveServer}
      isEditing={isEditing}
      searchPlaceholder="Search MCP servers to add"
      emptySelectedMessage="No MCP servers added yet"
      renderIcon={() => <Server className="w-4 h-4 text-gray-500" />}
    />
  );
}
