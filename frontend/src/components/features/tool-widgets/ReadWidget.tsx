/**
 * Read Tool Widget - displays file read operation
 */

import React from 'react';
import { FileText } from 'lucide-react';
import { WIDGET_HEADER_TEXT_SIZE } from './utils';
import type { ToolWidgetProps } from './types';

export const ReadWidget: React.FC<ToolWidgetProps> = ({
  toolArgs
}) => {
  const filePath = toolArgs.file_path as string;

  const header = (
    <>
      <FileText className="h-3.5 w-3.5 text-primary flex-shrink-0" />
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 flex-shrink-0`}>Read:</span>
      <code className={`${WIDGET_HEADER_TEXT_SIZE} font-mono text-gray-600 truncate`} title={filePath}>{filePath}</code>
    </>
  );

  return (
    <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
      <div className="px-4 py-2 bg-gray-50 flex items-center gap-2 min-w-0">
        {header}
      </div>
    </div>
  );
};
