import { Button } from '@/components/ui/primitives/button';
import type { LucideIcon } from 'lucide-react';

interface ModalActionButtonProps {
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  icon: LucideIcon;
  children: React.ReactNode;
  type?: 'button' | 'submit';
}

/**
 * Standardized action button for modal footers
 * - Consistent size, color, and layout
 * - Icon + text structure
 * - Responsive (full-width on mobile, auto-width on desktop)
 */
export function ModalActionButton({
  onClick,
  disabled = false,
  loading = false,
  icon: Icon,
  children,
  type = 'button',
}: ModalActionButtonProps) {
  return (
    <Button
      type={type}
      variant="default"
      size="default"
      onClick={onClick}
      disabled={disabled}
      loading={loading}
      className="w-full lg:w-auto px-6"
    >
      <Icon className="w-4 h-4" />
      {children}
    </Button>
  );
}
