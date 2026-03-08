import { motion } from 'framer-motion';
import { Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Task, TaskStatus } from '@/types/task';

const STATUS_STYLES: Record<TaskStatus, { badge: string; dot: string }> = {
  open: { badge: 'bg-gray-100 text-gray-600', dot: 'bg-gray-400' },
  in_progress: { badge: 'bg-blue-100 text-blue-700', dot: 'bg-blue-500' },
  done: { badge: 'bg-green-100 text-green-700', dot: 'bg-green-500' },
  archived: { badge: 'bg-slate-100 text-slate-500', dot: 'bg-slate-400' },
};

const STATUS_LABELS: Record<TaskStatus, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  done: 'Done',
  archived: 'Archived',
};

interface TaskKanbanCardProps {
  task: Task;
  sessionCount: number;
  onClick: () => void;
  onDelete?: (taskId: string) => void;
}

export function TaskKanbanCard({ task, sessionCount, onClick, onDelete }: TaskKanbanCardProps) {
  const styles = STATUS_STYLES[task.status];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      whileHover={{ scale: 1.02 }}
      className="group relative p-3 rounded-lg border cursor-pointer transition-all bg-white border-gray-200 hover:border-gray-300 hover:shadow-md"
      onClick={onClick}
      role="button"
      aria-label={`Task: ${task.name}, status: ${task.status}`}
    >
      {onDelete && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            if (confirm(`Delete task "${task.name}"?`)) onDelete(task.id);
          }}
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all rounded"
          title="Delete task"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      )}

      <p className="text-sm font-medium text-gray-900 pr-6 leading-snug">{task.name}</p>

      {task.description && (
        <p className="text-xs text-gray-500 mt-1 line-clamp-2 leading-tight">{task.description}</p>
      )}

      <div className="flex items-center justify-between mt-2.5">
        <span className={cn('inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium', styles.badge)}>
          <span className={cn('w-1.5 h-1.5 rounded-full', styles.dot)} />
          {STATUS_LABELS[task.status]}
        </span>
        {sessionCount > 0 && (
          <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
            {sessionCount} {sessionCount === 1 ? 'session' : 'sessions'}
          </span>
        )}
      </div>
    </motion.div>
  );
}
