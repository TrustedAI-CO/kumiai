import { useState } from 'react';
import { Plus, Trash2, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTasks, useUpdateTask, useDeleteTask } from '@/hooks/queries/useTasks';
import { TaskCreateModal } from './TaskCreateModal';
import type { Task, TaskStatus } from '@/types/task';

const STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'done', label: 'Done' },
  { value: 'archived', label: 'Archived' },
];

const STATUS_COLORS: Record<TaskStatus, string> = {
  open: 'bg-gray-100 text-gray-600',
  in_progress: 'bg-blue-100 text-blue-700',
  done: 'bg-green-100 text-green-700',
  archived: 'bg-slate-100 text-slate-500',
};

interface TaskRowProps {
  task: Task;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onDelete: (taskId: string) => void;
}

function TaskRow({ task, onStatusChange, onDelete }: TaskRowProps) {
  const [showStatusMenu, setShowStatusMenu] = useState(false);

  return (
    <div className="flex items-start gap-3 px-3 py-2.5 hover:bg-gray-50 rounded-lg group">
      {/* Status dropdown */}
      <div className="relative mt-0.5">
        <button
          type="button"
          onClick={() => setShowStatusMenu(!showStatusMenu)}
          className={cn(
            'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap',
            STATUS_COLORS[task.status]
          )}
        >
          {STATUS_OPTIONS.find(s => s.value === task.status)?.label}
          <ChevronDown className="w-3 h-3" />
        </button>
        {showStatusMenu && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setShowStatusMenu(false)} />
            <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1 min-w-[130px]">
              {STATUS_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => {
                    onStatusChange(task.id, opt.value);
                    setShowStatusMenu(false);
                  }}
                  className={cn(
                    'w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 transition-colors',
                    task.status === opt.value && 'font-medium'
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Task info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-900 font-medium truncate">{task.name}</p>
        {task.description && (
          <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{task.description}</p>
        )}
      </div>

      {/* Delete */}
      <button
        type="button"
        onClick={() => {
          if (confirm(`Delete task "${task.name}"?`)) onDelete(task.id);
        }}
        className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
        title="Delete task"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

interface TaskListPanelProps {
  projectId: string;
  onTaskSelect?: (task: Task) => void;
}

export function TaskListPanel({ projectId, onTaskSelect: _onTaskSelect }: TaskListPanelProps) {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');

  const { data: tasks = [], isLoading } = useTasks(projectId);
  const updateTask = useUpdateTask(projectId);
  const deleteTask = useDeleteTask(projectId);

  const filtered = statusFilter === 'all' ? tasks : tasks.filter(t => t.status === statusFilter);

  const handleStatusChange = (taskId: string, status: TaskStatus) => {
    updateTask.mutate({ taskId, req: { status } });
  };

  const handleDelete = (taskId: string) => {
    deleteTask.mutate(taskId);
  };

  return (
    <div className="border-b border-gray-200 bg-gray-50">
      {/* Panel header */}
      <div className="flex items-center justify-between px-6 py-2 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-700">Tasks</span>
          <span className="text-xs text-gray-400 bg-white px-2 py-0.5 rounded-full border border-gray-200">
            {tasks.length}
          </span>
          {/* Status filter */}
          <div className="flex items-center gap-1">
            {(['all', 'open', 'in_progress', 'done'] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setStatusFilter(s)}
                className={cn(
                  'px-2 py-0.5 rounded text-xs transition-colors',
                  statusFilter === s
                    ? 'bg-gray-200 text-gray-800 font-medium'
                    : 'text-gray-500 hover:bg-gray-100'
                )}
              >
                {s === 'all' ? 'All' : s === 'in_progress' ? 'In Progress' : s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>
        <button
          type="button"
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-white border border-gray-200 hover:bg-gray-50 transition-colors text-gray-700"
        >
          <Plus className="w-3.5 h-3.5" />
          New Task
        </button>
      </div>

      {/* Task list */}
      <div className="max-h-[180px] overflow-y-auto px-3 py-1">
        {isLoading ? (
          <div className="text-xs text-gray-400 py-3 text-center">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="text-xs text-gray-400 py-3 text-center">
            {tasks.length === 0 ? 'No tasks yet. Create one to get started.' : 'No tasks match the filter.'}
          </div>
        ) : (
          filtered.map((task) => (
            <TaskRow
              key={task.id}
              task={task}
              onStatusChange={handleStatusChange}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>

      <TaskCreateModal
        projectId={projectId}
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  );
}
