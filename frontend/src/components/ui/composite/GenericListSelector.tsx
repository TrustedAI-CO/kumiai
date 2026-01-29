import { useState, useMemo, useCallback, ReactNode } from 'react';
import { X, Package, Search } from 'lucide-react';
import { Input } from '../primitives/input';
import { ItemCard } from './ItemCard';
import { EmptyState } from './EmptyState';
import { LAYOUT, EMPTY_STATE_MESSAGE } from '@/constants';

// Local constants
const LIST_HEIGHT = LAYOUT.SKILL_LIST_HEIGHT;

/**
 * Base interface for selectable items.
 * All items must have an id, name, and description.
 */
export interface SelectableItem {
  id: string;
  name: string;
  description: string;
}

/**
 * Props for rendering a selected item card.
 */
interface SelectedItemCardProps<T extends SelectableItem> {
  item: T;
  onRemove: (itemId: string) => void;
  renderIcon: (item: T) => ReactNode;
  getIconColor?: (item: T) => string | undefined;
}

/**
 * Default selected item card component.
 */
function SelectedItemCard<T extends SelectableItem>({
  item,
  onRemove,
  renderIcon,
  getIconColor,
}: SelectedItemCardProps<T>) {
  const IconComponent = renderIcon(item);
  const iconColor = getIconColor?.(item);

  return (
    <button
      type="button"
      onClick={() => onRemove(item.id)}
      className="w-full px-3 py-2 rounded-lg border border-gray-200 bg-white hover:border-red-300 hover:bg-red-50 transition-all text-left group"
      title={`${item.name} - click to remove`}
      aria-label={`Remove ${item.name}`}
    >
      <div className="flex items-center gap-3">
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${iconColor ? '' : 'bg-gray-100'}`}
          style={iconColor ? { backgroundColor: iconColor } : undefined}
        >
          {IconComponent}
        </div>
        <span className="text-sm font-medium text-gray-900 flex-1 group-hover:text-red-600 transition-colors">
          {item.name}
        </span>
        <X className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </button>
  );
}

/**
 * Props for rendering an available item card.
 */
interface AvailableItemCardProps<T extends SelectableItem> {
  item: T;
  onAdd: (itemId: string) => void;
  renderIcon: (item: T) => ReactNode;
  getIconColor?: (item: T) => string | undefined;
}

/**
 * Default available item card component.
 */
function AvailableItemCard<T extends SelectableItem>({
  item,
  onAdd,
  renderIcon,
  getIconColor,
}: AvailableItemCardProps<T>) {
  const IconComponent = renderIcon(item);
  const iconColor = getIconColor?.(item);

  return (
    <ItemCard
      id={item.id}
      name={item.name}
      description={item.description}
      icon={IconComponent}
      iconColor={iconColor}
      onClick={() => onAdd(item.id)}
    />
  );
}


/**
 * Generic list selector props.
 */
export interface GenericListSelectorProps<T extends SelectableItem> {
  availableItems: T[];
  selectedItemIds: string[];
  onAddItem: (itemId: string) => void;
  onRemoveItem: (itemId: string) => void;
  isEditing: boolean;
  searchPlaceholder: string;
  emptySelectedMessage?: string;
  emptyAvailableMessage?: string;
  noResultsMessage?: string;
  renderIcon: (item: T) => ReactNode;
  getIconColor?: (item: T) => string | undefined;
  customSelectedCard?: React.ComponentType<SelectedItemCardProps<T>>;
  customAvailableCard?: React.ComponentType<AvailableItemCardProps<T>>;
  filterItem?: (item: T, query: string) => boolean;
}

/**
 * Generic list selector component.
 * Displays a two-panel layout with selected items on the left and available items on the right.
 * Supports search filtering, add/remove operations, and custom rendering.
 *
 * @example
 * ```tsx
 * <GenericListSelector
 *   availableItems={skills}
 *   selectedItemIds={selectedSkillIds}
 *   onAddItem={handleAddSkill}
 *   onRemoveItem={handleRemoveSkill}
 *   isEditing={isEditing}
 *   searchPlaceholder="Search skills to add"
 *   renderIcon={(skill) => <SkillIcon className="w-4 h-4 text-white" />}
 *   getIconColor={(skill) => skill.icon_color}
 * />
 * ```
 */
export function GenericListSelector<T extends SelectableItem>({
  availableItems,
  selectedItemIds,
  onAddItem,
  onRemoveItem,
  isEditing,
  searchPlaceholder,
  emptySelectedMessage = 'No items added yet',
  emptyAvailableMessage = EMPTY_STATE_MESSAGE.ALL_ADDED,
  noResultsMessage = EMPTY_STATE_MESSAGE.NO_RESULTS,
  renderIcon,
  getIconColor,
  customSelectedCard: CustomSelectedCard,
  customAvailableCard: CustomAvailableCard,
  filterItem,
}: GenericListSelectorProps<T>) {
  const [searchQuery, setSearchQuery] = useState('');

  // Default filter function
  const defaultFilterItem = useCallback((item: T, query: string) => {
    const lowerQuery = query.toLowerCase();
    return (
      item.name.toLowerCase().includes(lowerQuery) ||
      item.description.toLowerCase().includes(lowerQuery)
    );
  }, []);

  const filterFn = filterItem || defaultFilterItem;

  // Memoized computations
  const validItems = useMemo(
    () => selectedItemIds
      .map((itemId) => availableItems.find((item) => item.id === itemId))
      .filter((item): item is T => item !== undefined),
    [selectedItemIds, availableItems]
  );

  const unselectedItems = useMemo(
    () => availableItems.filter((item) => !selectedItemIds.includes(item.id)),
    [availableItems, selectedItemIds]
  );

  const filteredAvailableItems = useMemo(() => {
    if (!searchQuery) return unselectedItems;
    return unselectedItems.filter((item) => filterFn(item, searchQuery));
  }, [unselectedItems, searchQuery, filterFn]);

  // Memoized callbacks
  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value),
    []
  );

  // Render helpers
  const renderSelectedList = useCallback(() => {
    if (validItems.length === 0) {
      return <EmptyState icon={Package} title={emptySelectedMessage} />;
    }

    const CardComponent = CustomSelectedCard || SelectedItemCard;

    return validItems.map((item) => (
      <CardComponent
        key={item.id}
        item={item}
        onRemove={onRemoveItem}
        renderIcon={renderIcon}
        getIconColor={getIconColor}
      />
    ));
  }, [validItems, onRemoveItem, renderIcon, getIconColor, emptySelectedMessage, CustomSelectedCard]);

  const renderAvailableList = useCallback(() => {
    if (filteredAvailableItems.length === 0) {
      if (searchQuery) {
        return <EmptyState icon={Search} title={noResultsMessage} />;
      }
      return <EmptyState icon={Package} title={emptyAvailableMessage} />;
    }

    const CardComponent = CustomAvailableCard || AvailableItemCard;

    return filteredAvailableItems.map((item) => (
      <CardComponent
        key={item.id}
        item={item}
        onAdd={onAddItem}
        renderIcon={renderIcon}
        getIconColor={getIconColor}
      />
    ));
  }, [filteredAvailableItems, searchQuery, onAddItem, renderIcon, getIconColor, noResultsMessage, emptyAvailableMessage, CustomAvailableCard]);

  // Common selected items panel
  const selectedItemsPanel = (
    <div className={`border border-gray-200 rounded-lg p-4 bg-gray-50 ${LIST_HEIGHT} overflow-y-auto w-full lg:w-80 flex-shrink-0`}>
      <div className="space-y-2">
        {renderSelectedList()}
      </div>
    </div>
  );

  // Read-only view
  if (!isEditing) {
    return (
      <div className="flex flex-col lg:flex-row gap-3">
        {selectedItemsPanel}
      </div>
    );
  }

  // Edit mode view
  return (
    <div className="flex flex-col lg:flex-row gap-3">
      {selectedItemsPanel}

      {/* Available Items Panel */}
      <div className={`border border-gray-200 rounded-lg p-4 bg-gray-50 ${LIST_HEIGHT} flex flex-col flex-1`}>
        <Input
          value={searchQuery}
          onChange={handleSearchChange}
          placeholder={searchPlaceholder}
          className="mb-2.5 flex-shrink-0"
          aria-label={searchPlaceholder}
        />

        <div className="space-y-2 flex-1 overflow-y-auto scrollbar-hide">
          {renderAvailableList()}
        </div>
      </div>
    </div>
  );
}
