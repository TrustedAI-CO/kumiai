import { cn } from '@/lib/utils';
import type { TaskStatus } from '@/types/task';

const STATUS_STYLES: Record<TaskStatus, string> = {
  open: 'bg-gray-100 text-gray-600',
  in_progress: 'bg-blue-100 text-blue-700',
  done: 'bg-green-100 text-green-700',
  archived: 'bg-slate-100 text-slate-500',
};

const STATUS_LABELS: Record<TaskStatus, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  done: 'Done',
  archived: 'Archived',
};

interface TaskBadgeProps {
  taskName: string;
  taskStatus: TaskStatus;
  className?: string;
}

export function TaskBadge({ taskName, taskStatus, className }: TaskBadgeProps) {
  return (
    <div className={cn('flex items-center gap-1.5 mt-1.5', className)}>
      <span
        className={cn(
          'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium',
          STATUS_STYLES[taskStatus]
        )}
      >
        {STATUS_LABELS[taskStatus]}
      </span>
      <span className="text-[11px] text-gray-500 truncate max-w-[120px]" title={taskName}>
        {taskName}
      </span>
    </div>
  );
}
