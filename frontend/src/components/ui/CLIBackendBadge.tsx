import { cn } from '@/lib/utils';

const BACKEND_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  claude: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Claude' },
  codex: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Codex' },
  gemini: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Gemini' },
  opencode: { bg: 'bg-violet-100', text: 'text-violet-700', label: 'OpenCode' },
};

interface CLIBackendBadgeProps {
  backend?: string;
  model?: string;
  size?: 'sm' | 'md';
}

export function CLIBackendBadge({ backend = 'claude', model, size = 'sm' }: CLIBackendBadgeProps) {
  const style = BACKEND_STYLES[backend] || BACKEND_STYLES.claude;
  const isSm = size === 'sm';

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full font-medium whitespace-nowrap',
        style.bg,
        style.text,
        isSm ? 'px-1.5 py-0.5 text-[9px]' : 'px-2 py-0.5 text-[10px]'
      )}
      title={`${style.label}${model ? ` / ${model}` : ''}`}
    >
      <span className="font-semibold">{style.label}</span>
      {model && (
        <>
          <span className={cn('opacity-40', isSm ? 'text-[8px]' : 'text-[9px]')}>/</span>
          <span className="font-mono opacity-75">{model}</span>
        </>
      )}
    </span>
  );
}
