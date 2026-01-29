import { useState, useMemo, useCallback } from 'react';
import { Plus, X, Wrench, Search } from 'lucide-react';
import { Input } from '@/components/ui/primitives/input';
import { EmptyState } from '@/components/ui';
import { LAYOUT, EMPTY_STATE_MESSAGE } from '@/constants/ui';
import type { CustomTool } from '@/lib/api';

// Local constants
const TOOL_LIST_HEIGHT = LAYOUT.SKILL_LIST_HEIGHT;

interface CustomToolSelectorProps {
  availableTools: CustomTool[];
  selectedToolIds: string[];
  onAddTool: (toolId: string) => void;
  onRemoveTool: (toolId: string) => void;
  isEditing: boolean;
}

// Utility function to get display name (remove provider prefix)
function getToolDisplayName(toolId: string): string {
  // Format: provider__category__name -> category/name
  const parts = toolId.split('__');
  if (parts.length >= 3) {
    return `${parts[1]}/${parts[2]}`;
  }
  return toolId;
}

// Extracted Components
interface ToolCardProps {
  tool: CustomTool;
  onRemove?: (toolId: string) => void;
  showRemoveButton?: boolean;
}

function ToolCard({ tool, onRemove, showRemoveButton = true }: ToolCardProps) {
  const displayName = getToolDisplayName(tool.id);

  return (
    <button
      type="button"
      onClick={() => onRemove?.(tool.id)}
      className="w-full px-3 py-2 rounded-lg border border-gray-200 bg-white hover:border-red-300 hover:bg-red-50 transition-all text-left group"
      title={`${displayName} - click to remove`}
      aria-label={`Remove ${displayName}`}
    >
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-gray-900 flex-1 group-hover:text-red-600 transition-colors">
          {displayName}
        </span>
        <X className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </button>
  );
}

interface AvailableToolCardProps {
  tool: CustomTool;
  onAdd: (toolId: string) => void;
}

function AvailableToolCard({ tool, onAdd }: AvailableToolCardProps) {
  const displayName = getToolDisplayName(tool.id);

  return (
    <button
      type="button"
      onClick={() => onAdd(tool.id)}
      className="w-full px-3 py-3 rounded-lg border border-gray-200 bg-white hover:border-border hover:bg-muted/50 transition-all text-left"
      aria-label={`Add ${displayName}`}
    >
      <div className="flex items-center gap-3">
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-900 text-sm mb-0.5">
            {displayName}
          </div>
          <div className="text-xs text-gray-600 line-clamp-2">
            {tool.description}
          </div>
        </div>
        <div className="flex-shrink-0 opacity-60">
          <Plus className="w-4 h-4 text-primary" />
        </div>
      </div>
    </button>
  );
}


// Main Component
export function CustomToolSelector({
  availableTools,
  selectedToolIds,
  onAddTool,
  onRemoveTool,
  isEditing,
}: CustomToolSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // Memoized computations
  const validTools = useMemo(
    () => selectedToolIds
      .map((toolId) => availableTools.find((t) => t.id === toolId))
      .filter((tool): tool is CustomTool => tool !== undefined),
    [selectedToolIds, availableTools]
  );

  const unselectedTools = useMemo(
    () => availableTools.filter((tool) => !selectedToolIds.includes(tool.id)),
    [availableTools, selectedToolIds]
  );

  const filteredAvailableTools = useMemo(() => {
    if (!searchQuery) return unselectedTools;
    const query = searchQuery.toLowerCase();
    return unselectedTools.filter(
      (tool) => {
        const displayName = getToolDisplayName(tool.id).toLowerCase();
        return (
          displayName.includes(query) ||
          tool.name.toLowerCase().includes(query) ||
          tool.description.toLowerCase().includes(query) ||
          tool.category.toLowerCase().includes(query) ||
          tool.provider.toLowerCase().includes(query)
        );
      }
    );
  }, [unselectedTools, searchQuery]);

  // Memoized callbacks
  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value),
    []
  );

  // Render helpers
  const renderToolsList = useCallback(
    (tools: CustomTool[]) => {
      if (tools.length === 0) {
        return (
          <EmptyState
            icon={Wrench}
            title="No tools added yet"
          />
        );
      }

      return tools.map((tool) => (
        <ToolCard
          key={tool.id}
          tool={tool}
          onRemove={onRemoveTool}
          showRemoveButton
        />
      ));
    },
    [onRemoveTool]
  );

  const renderAvailableTools = useCallback(() => {
    if (filteredAvailableTools.length === 0) {
      if (searchQuery) {
        return <EmptyState icon={Search} title={EMPTY_STATE_MESSAGE.NO_RESULTS} />;
      }
      return <EmptyState icon={Wrench} title={EMPTY_STATE_MESSAGE.ALL_ADDED} />;
    }

    return filteredAvailableTools.map((tool) => (
      <AvailableToolCard key={tool.id} tool={tool} onAdd={onAddTool} />
    ));
  }, [filteredAvailableTools, searchQuery, onAddTool]);

  // Common selected tools panel
  const selectedToolsPanel = (
    <div className={`border border-gray-200 rounded-lg p-4 bg-gray-50 ${TOOL_LIST_HEIGHT} overflow-y-auto w-80 flex-shrink-0`}>
      <div className="space-y-2">
        {renderToolsList(validTools)}
      </div>
    </div>
  );

  // Read-only view
  if (!isEditing) {
    return (
      <div className="flex gap-3">
        {selectedToolsPanel}
      </div>
    );
  }

  // Edit mode view
  return (
    <div className="flex gap-3">
      {selectedToolsPanel}

      {/* Available Tools Panel */}
      <div className={`border border-gray-200 rounded-lg p-4 bg-gray-50 ${TOOL_LIST_HEIGHT} flex flex-col flex-1`}>
        <Input
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder="Search custom tools to add"
          className="mb-2.5 flex-shrink-0"
          aria-label="Search available custom tools"
        />

        <div className="space-y-2 flex-1 overflow-y-auto scrollbar-hide">
          {renderAvailableTools()}
        </div>
      </div>
    </div>
  );
}
