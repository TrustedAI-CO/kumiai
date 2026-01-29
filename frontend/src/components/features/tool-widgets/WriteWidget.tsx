/**
 * Write Tool Widget - displays file write operation
 */

import React from 'react';
import { FilePlus } from 'lucide-react';
import { CollapsibleWidget } from './CollapsibleWidget';
import { parseResultContent, WIDGET_HEADER_TEXT_SIZE } from './utils';
import type { ToolWidgetProps } from './types';

export const WriteWidget: React.FC<ToolWidgetProps> = ({
  toolArgs,
  result
}) => {
  const filePath = toolArgs.file_path as string;
  const content = toolArgs.content as string;
  const { content: resultContent, isError } = parseResultContent(result);

  const previewContent = content && content.length > 200
    ? content.substring(0, 200) + '\n...'
    : content || '';

  const header = (
    <>
      <FilePlus className="h-3.5 w-3.5 text-primary flex-shrink-0" />
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 flex-shrink-0`}>Write:</span>
      <code className={`${WIDGET_HEADER_TEXT_SIZE} font-mono text-gray-600 truncate`} title={filePath}>{filePath}</code>
    </>
  );

  return (
    <CollapsibleWidget header={header} toolArgs={toolArgs} result={result}>
      <div className="p-4 space-y-2">
        <div className="type-caption text-gray-500 uppercase tracking-wide">Preview</div>
        <div className="p-2 bg-gray-50 rounded border border-gray-200">
          <pre className="type-caption font-mono overflow-x-auto text-gray-700">
            {previewContent}
          </pre>
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
