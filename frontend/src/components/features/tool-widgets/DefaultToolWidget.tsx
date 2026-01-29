/**
 * Default Tool Widget - fallback for unknown tools
 */

import React from 'react';
import { Wrench } from 'lucide-react';
import { CollapsibleWidget } from './CollapsibleWidget';
import { parseResultContent, WIDGET_HEADER_TEXT_SIZE } from './utils';
import { truncateMcpPrefix } from '@/lib/utils';
import type { ToolWidgetProps } from './types';

export const DefaultToolWidget: React.FC<ToolWidgetProps> = ({
  toolName,
  toolArgs,
  result
}) => {
  const { content: resultContent, isError } = parseResultContent(result);

  const header = (
    <>
      <Wrench className="w-3.5 h-3.5 text-primary flex-shrink-0" />
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 truncate`} title={toolName}>
        {truncateMcpPrefix(toolName)}
      </span>
    </>
  );

  return (
    <CollapsibleWidget header={header} toolArgs={toolArgs} result={result}>
      <div className="p-4 space-y-3">
        {/* Tool arguments */}
        {Object.keys(toolArgs).length > 0 && (
          <div className="p-2 bg-gray-50 rounded border border-gray-200">
            <pre className="type-caption font-mono overflow-x-auto text-gray-800">
              {JSON.stringify(toolArgs, null, 2)}
            </pre>
          </div>
        )}

        {/* Tool result */}
        {result && resultContent && (
          <div className={`p-2 rounded border type-caption ${
            isError
              ? 'bg-red-50 border-red-200 text-red-800'
              : 'bg-green-50 border-green-200 text-green-800'
          }`}>
            <pre className="font-mono overflow-x-auto whitespace-pre-wrap">
              {resultContent}
            </pre>
          </div>
        )}
      </div>
    </CollapsibleWidget>
  );
};
