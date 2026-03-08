import { Plus, Ellipsis, LayoutGrid, Table2, Pencil } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from '@/components/ui/primitives/dropdown-menu';

interface ProjectHeaderActionsProps {
  viewMode: 'kanban' | 'task-sessions' | 'chat';
  boardViewMode: 'kanban' | 'table';
  onBoardViewModeChange: (mode: 'kanban' | 'table') => void;
  onEditProject: () => void;
  onNewTask?: () => void;
  onNewSession?: () => void;
}

export function ProjectHeaderActions({
  viewMode,
  boardViewMode,
  onBoardViewModeChange,
  onEditProject,
  onNewTask,
  onNewSession,
}: ProjectHeaderActionsProps) {
  const newButton = onNewTask
    ? { label: 'New Task', onClick: onNewTask }
    : onNewSession
      ? { label: 'New Session', onClick: onNewSession }
      : null;

  return (
    <div className="flex items-center gap-2">
      {newButton && (
        <button
          type="button"
          onClick={newButton.onClick}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-black hover:bg-gray-800 transition-colors text-white text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">{newButton.label}</span>
        </button>
      )}

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            aria-label="Project actions"
            className="p-1.5 rounded-md hover:bg-gray-100 transition-colors text-gray-600"
          >
            <Ellipsis className="w-4 h-4" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-44">
          {viewMode === 'kanban' && (
            <>
              <DropdownMenuLabel className="text-xs text-gray-500 font-normal">View</DropdownMenuLabel>
              <DropdownMenuRadioGroup
                value={boardViewMode}
                onValueChange={(v) => onBoardViewModeChange(v as 'kanban' | 'table')}
              >
                <DropdownMenuRadioItem value="kanban" className="gap-2">
                  <LayoutGrid className="w-4 h-4" />
                  Board
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="table" className="gap-2">
                  <Table2 className="w-4 h-4" />
                  Table
                </DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
              <DropdownMenuSeparator />
            </>
          )}
          <DropdownMenuItem onClick={onEditProject} className="gap-2">
            <Pencil className="w-4 h-4" />
            Edit Project
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
