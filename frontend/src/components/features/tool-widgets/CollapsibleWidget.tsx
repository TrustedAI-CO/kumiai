/**
 * Collapsible Widget Wrapper
 *
 * Provides consistent collapsible behavior for all tool widgets
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface CollapsibleWidgetProps {
  header: React.ReactNode;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  collapsible?: boolean;
  toolArgs?: Record<string, unknown>;
  result?: any;
}

export const CollapsibleWidget: React.FC<CollapsibleWidgetProps> = ({
  header,
  children,
  defaultExpanded = false,
  collapsible,
  toolArgs = {},
  result
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  // Check if there are actual arguments (not just empty object)
  const hasArgs = toolArgs && Object.keys(toolArgs).length > 0;

  // Check if there's actual result content (not just empty object)
  const hasResult = result && (
    // Has content property with value
    (result.content && (
      typeof result.content === 'string' ? result.content.trim().length > 0 : true
    )) ||
    // Has is_error flag
    result.is_error ||
    // Has other meaningful properties (not just empty {})
    (typeof result === 'object' &&
     Object.keys(result).length > 0 &&
     Object.keys(result).some(key => result[key] !== undefined && result[key] !== null && result[key] !== ''))
  );

  const hasContent = hasArgs || hasResult;

  // Determine rendering mode:
  // 1. If collapsible explicitly set to false: Always expanded (show content, no chevron)
  // 2. If collapsible explicitly set to true: Collapsible (show chevron)
  // 3. If collapsible undefined (auto-detect):
  //    - If has content: Collapsible (show chevron)
  //    - If no content: Header only (no children, no chevron)

  const isCollapsible = collapsible !== undefined ? collapsible : hasContent;
  const showContent = collapsible === false || (collapsible === undefined && !hasContent) ? true : isExpanded;
  const headerOnly = collapsible === undefined && !hasContent;

  if (headerOnly) {
    // Header only mode: no content area at all
    return (
      <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
        <div className="px-4 py-2 bg-gray-50 flex items-center gap-2 min-w-0">
          {header}
        </div>
      </div>
    );
  }

  if (collapsible === false) {
    // Always expanded mode: show content, no chevron, no hover
    return (
      <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
        <div className="px-4 py-2 bg-gray-50 flex items-center gap-2 border-b border-gray-200 min-w-0">
          {header}
        </div>
        {children}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
      <div
        className="px-4 py-2 bg-gray-50 flex items-center gap-2 border-b border-gray-200 min-w-0 cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {header}
        {isExpanded ? (
          <ChevronUp className="h-3.5 w-3.5 text-gray-500 ml-auto flex-shrink-0" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-gray-500 ml-auto flex-shrink-0" />
        )}
      </div>
      {isExpanded && children}
    </div>
  );
};
