import { Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DeleteButtonProps {
  onClick: (e: React.MouseEvent) => void;
  title?: string;
  ariaLabel?: string;
  disabled?: boolean;
  absolute?: boolean;
  className?: string;
}

/**
 * DeleteButton - Reusable delete button component
 *
 * A consistent delete button with hover reveal behavior.
 * Used across SessionCard, ProjectCard, SkillsList, and AgentsList.
 */
export function DeleteButton({
  onClick,
  title = 'Delete',
  ariaLabel,
  disabled = false,
  absolute = true,
  className,
}: DeleteButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'p-1.5 rounded-md bg-background border border-border text-muted-foreground',
        'hover:bg-destructive/10 hover:border-destructive hover:text-destructive',
        'opacity-0 group-hover:opacity-100 transition-all shadow-sm',
        absolute && 'absolute top-2 right-2 z-10',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      title={title}
      aria-label={ariaLabel || title}
    >
      <Trash2 className="w-4 h-4" />
    </button>
  );
}
