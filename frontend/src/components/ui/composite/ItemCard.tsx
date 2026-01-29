import { ReactNode, memo } from 'react';
import { cn } from '@/lib/utils';
import { BaseCard } from '@/ui';
import { CardHeader, CardContent } from '@/components/ui/primitives/card';

interface ItemCardProps {
  id: string;
  name: string;
  description?: string;
  icon: ReactNode;
  iconColor?: string;
  onClick?: () => void;
  onRemove?: () => void;
  showRemoveButton?: boolean;
  isSelected?: boolean;
  className?: string;
}

/**
 * Shared card component for displaying items (skills, agents, etc.) with consistent layout
 */
export const ItemCard = memo(function ItemCard({
  id,
  name,
  description,
  icon,
  iconColor,
  onClick,
  onRemove,
  showRemoveButton = false,
  isSelected = false,
  className = '',
}: ItemCardProps) {
  const handleClick = () => {
    if (onRemove && showRemoveButton) {
      onRemove();
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <BaseCard
      onClick={handleClick}
      isSelected={isSelected}
      isDanger={showRemoveButton}
      className={cn('w-full', className)}
      title={description ? `${name} - ${description}` : name}
      role="button"
      aria-label={showRemoveButton ? `Remove ${name}` : `Select ${name}`}
    >
      <CardHeader className={cn("p-3", description ? "pb-2" : "pb-3")}>
        <div className="flex items-center gap-2.5">
          <div
            className={cn(
              'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
              iconColor ? '' : 'bg-secondary'
            )}
            style={iconColor ? { backgroundColor: iconColor } : undefined}
          >
            {icon}
          </div>
          <h3 className="type-subtitle truncate flex-1 min-w-0">
            {name}
          </h3>
        </div>
      </CardHeader>

      {description && (
        <CardContent className="p-3 pt-0">
          <div className="type-caption line-clamp-1">
            {description}
          </div>
        </CardContent>
      )}
    </BaseCard>
  );
});
