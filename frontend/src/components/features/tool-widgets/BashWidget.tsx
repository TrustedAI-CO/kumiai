/**
 * Bash Tool Widget - displays bash command execution
 */

import React from 'react';
import { Terminal } from 'lucide-react';
import { CollapsibleWidget } from './CollapsibleWidget';
import { parseResultContent, WIDGET_HEADER_TEXT_SIZE } from './utils';
import type { ToolWidgetProps } from './types';

export const BashWidget: React.FC<ToolWidgetProps> = ({
  toolArgs,
  result
}) => {
  const command = toolArgs.command as string;
  const description = toolArgs.description as string | undefined;
  const { content: resultContent, isError } = parseResultContent(result);

  const header = (
    <>
      <Terminal className="h-3.5 w-3.5 flex-shrink-0 text-primary" />
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 flex-shrink-0`}>Exec:</span>
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 truncate`} title={description || command}>
        {description || command}
      </span>
    </>
  );

  return (
    <CollapsibleWidget header={header} toolArgs={toolArgs} result={result}>
      <div className="p-4 space-y-3">
        <div>
          <div className="type-caption text-gray-500 uppercase tracking-wide mb-1">Command</div>
          <code className="type-caption font-mono text-primary bg-muted px-2 py-1 rounded block">
            $ {command}
          </code>
        </div>

        {/* Result */}
        {result && (
          <div className={`p-3 rounded border type-caption font-mono whitespace-pre-wrap overflow-x-auto ${
            isError
              ? 'border-red-200 bg-red-50 text-red-700'
              : 'bg-green-50 border-green-200 text-green-700'
          }`}>
            {resultContent || (isError ? 'Command failed' : 'Command completed')}
          </div>
        )}
      </div>
    </CollapsibleWidget>
  );
};
