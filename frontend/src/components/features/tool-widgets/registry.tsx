/**
 * Widget Registry - Maps tool names to widget components
 *
 * Uses a factory pattern to select the appropriate widget for each tool type
 */

import React, { lazy, Suspense } from 'react';
import type { ToolWidgetProps } from './types';

// Import all widget components
import { BashWidget } from './BashWidget';
import { ReadWidget } from './ReadWidget';
import { WriteWidget } from './WriteWidget';
import { EditWidget } from './EditWidget';
import { TodoWriteWidget } from './TodoWriteWidget';
import { ContactPMWidget } from './ContactPMWidget';
import { ShowFileWidget } from './ShowFileWidget';
import { DefaultToolWidget } from './DefaultToolWidget';

// TODO: Extract these complex widgets from old ToolWidgets.tsx
// For now, use DefaultToolWidget as fallback
const ContactSessionWidget = DefaultToolWidget;
const SpawnSessionWidget = DefaultToolWidget;
const RemindWidget = DefaultToolWidget;
const GetProjectStatusWidget = DefaultToolWidget;
const UpdateInstanceStageWidget = DefaultToolWidget;
const FileUploadWidget = DefaultToolWidget;

/**
 * Loading fallback for lazy-loaded widgets
 */
const WidgetLoader: React.FC = () => (
  <div className="rounded-lg border border-gray-200 bg-white p-4">
    <div className="flex items-center gap-2 text-gray-500">
      <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
      <span className="type-caption">Loading widget...</span>
    </div>
  </div>
);

/**
 * Widget registry type - maps tool name patterns to widget components
 */
type WidgetComponent = React.FC<ToolWidgetProps>;
type WidgetMatcher = (toolName: string) => boolean;

interface WidgetRegistryEntry {
  matcher: WidgetMatcher;
  component: WidgetComponent;
}

/**
 * Widget registry - ordered list of matchers
 * First match wins, so order is important
 */
const widgetRegistry: WidgetRegistryEntry[] = [
  // File operation tools
  {
    matcher: (name) => name === 'bash',
    component: BashWidget
  },
  {
    matcher: (name) => name === 'read',
    component: ReadWidget
  },
  {
    matcher: (name) => name === 'write',
    component: WriteWidget
  },
  {
    matcher: (name) => name === 'edit',
    component: EditWidget
  },

  // Show file tool (supports MCP server prefixes)
  {
    matcher: (name) =>
      name === 'show_file' ||
      name === 'showfile' ||
      name.includes('__show_file'),
    component: ShowFileWidget
  },

  // TodoWrite tool
  {
    matcher: (name) => name === 'todowrite',
    component: TodoWriteWidget
  },

  // Communication tools
  {
    matcher: (name) =>
      name === 'contact_pm' ||
      name === 'mcp__common_tools__contact_pm',
    component: ContactPMWidget
  },
  {
    matcher: (name) =>
      name === 'contact_instance' ||
      name === 'mcp__pm_management__contact_instance' ||
      name === 'mcp__common_tools__contact_instance',
    component: ContactSessionWidget
  },
  {
    matcher: (name) =>
      name === 'spawn_instance' ||
      name === 'mcp__pm_management__spawn_instance',
    component: SpawnSessionWidget
  },

  // Remind tool
  {
    matcher: (name) =>
      name === 'remind' ||
      name === 'mcp__common_tools__remind',
    component: RemindWidget
  },

  // Project management tools
  {
    matcher: (name) =>
      name === 'get_project_status' ||
      name === 'mcp__pm_management__get_project_status',
    component: GetProjectStatusWidget
  },
  {
    matcher: (name) =>
      name === 'update_instance_stage' ||
      name === 'mcp__pm_management__update_instance_stage',
    component: UpdateInstanceStageWidget
  },

  // File upload tools (Playwright and Chrome DevTools)
  {
    matcher: (name) =>
      name === 'browser_file_upload' ||
      name === 'mcp__playwright__browser_file_upload' ||
      name === 'upload_file' ||
      name === 'mcp__chrome-devtools__upload_file',
    component: FileUploadWidget
  }
];

/**
 * Select and render the appropriate widget for a tool
 */
export function renderToolWidget(props: ToolWidgetProps): React.ReactNode {
  const toolName = props.toolName?.toLowerCase();

  // Find first matching widget
  for (const entry of widgetRegistry) {
    if (entry.matcher(toolName)) {
      const WidgetComponent = entry.component;

      // Wrap lazy-loaded components in Suspense
      return (
        <Suspense fallback={<WidgetLoader />}>
          <WidgetComponent {...props} />
        </Suspense>
      );
    }
  }

  // Default widget for unknown tools
  return <DefaultToolWidget {...props} />;
}

/**
 * Register a custom widget for a tool name pattern
 * Allows extending the widget system dynamically
 */
export function registerWidget(matcher: WidgetMatcher, component: WidgetComponent): void {
  widgetRegistry.unshift({ matcher, component });
}
