import { useState } from 'react';
import { Plus } from 'lucide-react';
import { Input } from '@/components/ui/primitives/input';
import { Textarea } from '@/components/ui/primitives/textarea';
import { ModalActionButton } from '@/ui';
import { useCreateTask } from '@/hooks/queries/useTasks';
import type { Task } from '@/types/task';

interface TaskCreateModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onCreated?: (task: Task) => void;
}

export function TaskCreateModal({ projectId, isOpen, onClose, onCreated }: TaskCreateModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const createTask = useCreateTask(projectId);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    if (!name.trim()) return;
    try {
      const task = await createTask.mutateAsync({ name: name.trim(), description: description.trim() || undefined });
      setName('');
      setDescription('');
      onCreated?.(task);
      onClose();
    } catch (err) {
      alert('Failed to create task: ' + err);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="px-5 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">New Task</h2>
          <button type="button" onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
            <Plus className="w-4 h-4 text-gray-500 rotate-45" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1.5">
              Name <span className="text-red-500">*</span>
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Task name"
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1.5">Description</label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              rows={3}
              className="resize-none"
            />
          </div>
        </div>

        <div className="px-5 py-4 border-t border-gray-200 flex justify-end">
          <ModalActionButton
            type="button"
            onClick={handleSubmit}
            disabled={!name.trim() || createTask.isPending}
            icon={Plus}
          >
            {createTask.isPending ? 'Creating...' : 'Create Task'}
          </ModalActionButton>
        </div>
      </div>
    </div>
  );
}
