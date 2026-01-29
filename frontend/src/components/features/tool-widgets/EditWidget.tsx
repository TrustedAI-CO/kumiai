/**
 * Edit Tool Widget - displays file edit operation
 */

import React from 'react';
import { Edit3 } from 'lucide-react';
import { CollapsibleWidget } from './CollapsibleWidget';
import { parseResultContent, WIDGET_HEADER_TEXT_SIZE } from './utils';
import type { ToolWidgetProps } from './types';

export const EditWidget: React.FC<ToolWidgetProps> = ({
  toolArgs,
  result
}) => {
  const filePath = toolArgs.file_path as string;
  const oldString = toolArgs.old_string as string;
  const newString = toolArgs.new_string as string;
  const { content: resultContent, isError } = parseResultContent(result);

  const header = (
    <>
      <Edit3 className="h-3.5 w-3.5 text-primary flex-shrink-0" />
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 flex-shrink-0`}>Edit:</span>
      <code className={`${WIDGET_HEADER_TEXT_SIZE} font-mono text-gray-600 truncate`} title={filePath}>{filePath}</code>
    </>
  );

  return (
    <CollapsibleWidget header={header} toolArgs={toolArgs} result={result}>
      <div className="p-4 space-y-3">
        {/* Old and New content side by side */}
        <div className="grid grid-cols-2 gap-3">
          {/* Old content */}
          <div>
            <div className="type-caption text-gray-500 uppercase tracking-wide mb-1">Old</div>
            <div className="p-2 bg-red-50 border border-red-200 rounded">
              <pre className="type-caption font-mono overflow-x-auto text-red-700">
                {oldString}
              </pre>
            </div>
          </div>

          {/* New content */}
          <div>
            <div className="type-caption text-gray-500 uppercase tracking-wide mb-1">New</div>
            <div className="p-2 bg-green-50 border border-green-200 rounded">
              <pre className="type-caption font-mono overflow-x-auto text-green-700">
                {newString}
              </pre>
            </div>
          </div>
        </div>

        {/* Result */}
        {result && resultContent && (
          <div className={`p-2 rounded border type-caption ${
            isError
              ? 'bg-red-50 border-red-200 text-red-700'
              : 'bg-green-50 border-green-200 text-green-700'
          }`}>
            {resultContent}
          </div>
        )}
      </div>
    </CollapsibleWidget>
  );
};
