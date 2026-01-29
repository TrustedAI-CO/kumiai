/**
 * StatusMessage Component
 *
 * Displays success/error/warning/info messages with consistent styling
 */
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, Info, LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

type StatusType = 'success' | 'error' | 'warning' | 'info';

interface StatusMessageProps {
  type: StatusType;
  title: string;
  message?: string;
  icon?: LucideIcon;
  className?: string;
  onClose?: () => void;
}

const statusConfig: Record<StatusType, {
  bgColor: string;
  borderColor: string;
  iconColor: string;
  textColor: string;
  defaultIcon: LucideIcon;
}> = {
  success: {
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    iconColor: 'text-green-600',
    textColor: 'text-green-900',
    defaultIcon: CheckCircle,
  },
  error: {
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    iconColor: 'text-red-600',
    textColor: 'text-red-900',
    defaultIcon: XCircle,
  },
  warning: {
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    iconColor: 'text-yellow-600',
    textColor: 'text-yellow-900',
    defaultIcon: AlertTriangle,
  },
  info: {
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    iconColor: 'text-blue-600',
    textColor: 'text-blue-900',
    defaultIcon: Info,
  },
};

export function StatusMessage({
  type,
  title,
  message,
  icon,
  className,
  onClose,
}: StatusMessageProps) {
  const config = statusConfig[type];
  const Icon = icon || config.defaultIcon;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border',
        config.bgColor,
        config.borderColor,
        className
      )}
    >
      <Icon className={cn('w-5 h-5 flex-shrink-0', config.iconColor)} />
      <div className="flex-1 min-w-0">
        <p className={cn('text-sm font-medium', config.textColor)}>{title}</p>
        {message && (
          <p className={cn('text-sm mt-1', config.textColor, 'opacity-90')}>
            {message}
          </p>
        )}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className={cn(
            'flex-shrink-0 p-1 rounded hover:bg-black/5 transition-colors',
            config.iconColor
          )}
          aria-label="Close message"
        >
          <XCircle className="w-4 h-4" />
        </button>
      )}
    </motion.div>
  );
}
