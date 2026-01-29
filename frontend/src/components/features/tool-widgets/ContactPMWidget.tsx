/**
 * Contact PM Widget - for specialists to send messages to PM
 */

import React from 'react';
import { MessageSquare } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CollapsibleWidget } from './CollapsibleWidget';
import { parseResultContent, WIDGET_HEADER_TEXT_SIZE } from './utils';
import type { ToolWidgetProps } from './types';

export const ContactPMWidget: React.FC<ToolWidgetProps> = ({
  toolArgs,
  result
}) => {
  const message = (toolArgs.message as string) || '';
  const { content: resultContent, isError } = parseResultContent(result);

  // Truncate message for header
  const truncatedMessage = message.length > 50 ? message.substring(0, 50) + '...' : message;

  const header = (
    <>
      <MessageSquare className="h-3.5 w-3.5 text-primary flex-shrink-0" />
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 flex-shrink-0`}>Message to PM:</span>
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 truncate`} title={message}>{truncatedMessage}</span>
    </>
  );

  return (
    <CollapsibleWidget header={header} toolArgs={toolArgs} result={result}>
      <div className="p-4 space-y-2">
        <div>
          <div className="type-caption text-gray-500 uppercase tracking-wide mb-1">Message</div>
          <div className="type-body-sm text-gray-700">
            <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>{message}</ReactMarkdown>
          </div>
        </div>
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
