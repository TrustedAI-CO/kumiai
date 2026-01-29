/**
 * TodoWrite Widget - displays todo list with status indicators
 */

import React from 'react';
import { ListChecks, CheckCircle2, Clock, Circle } from 'lucide-react';
import { CollapsibleWidget } from './CollapsibleWidget';
import { parseResultContent, WIDGET_HEADER_TEXT_SIZE } from './utils';
import type { ToolWidgetProps } from './types';

export const TodoWriteWidget: React.FC<ToolWidgetProps> = ({
  toolArgs,
  result
}) => {
  const todos = toolArgs.todos as any[] | undefined;
  const { content: resultContent, isError } = parseResultContent(result);

  const statusIcons = {
    completed: <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />,
    in_progress: <Clock className="h-3.5 w-3.5 animate-pulse text-primary" />,
    pending: <Circle className="h-3.5 w-3.5 text-gray-400" />
  };

  const todoCount = todos?.length || 0;
  const completedCount = todos?.filter(t => t.status === 'completed').length || 0;

  const header = (
    <>
      <ListChecks className="h-3.5 w-3.5 text-primary flex-shrink-0" />
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 flex-shrink-0`}>Tasks:</span>
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 flex-shrink-0`}>
        {todoCount > 0 ? `${completedCount}/${todoCount} completed` : 'No tasks'}
      </span>
    </>
  );

  if (!todos || todos.length === 0) {
    return (
      <CollapsibleWidget header={header} toolArgs={toolArgs} result={result}>
        <div className="p-4 type-caption text-gray-500">No todos</div>
      </CollapsibleWidget>
    );
  }

  return (
    <CollapsibleWidget header={header} toolArgs={toolArgs} result={result}>
      <div className="p-4 space-y-2">
        {todos.map((todo, idx) => (
          <div
            key={idx}
            className={`flex items-start gap-2 p-2 rounded border ${
              todo.status === 'completed' ? 'bg-gray-50 opacity-60' : 'bg-white'
            }`}
          >
            <div className="mt-0.5 flex-shrink-0">
              {statusIcons[todo.status as keyof typeof statusIcons] || statusIcons.pending}
            </div>
            <div className="flex-1 min-w-0">
              <p className={`type-caption ${todo.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                {todo.content}
              </p>
              {todo.activeForm && todo.status === 'in_progress' && (
                <p className="type-caption text-blue-600 mt-0.5">{todo.activeForm}</p>
              )}
            </div>
          </div>
        ))}
        {result && resultContent && (
          <div className={`p-2 rounded border type-caption mt-2 ${
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
