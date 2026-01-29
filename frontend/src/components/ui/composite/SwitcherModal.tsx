/**
 * SwitcherModal - Shared base component for keyboard-accessible switcher modals
 *
 * Provides consistent layout, keyboard navigation, and search functionality
 * for ProjectSwitcher and SessionSwitcher components.
 */
import { useRef, useEffect, ReactNode } from 'react';
import { Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { LoadingState } from '@/ui';

interface SwitcherModalProps {
  isOpen: boolean;
  onClose: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  placeholder: string;
  title: string;
  subtitle: string;
  shortcut: string;
  loading?: boolean;
  children: ReactNode;
  emptyMessage?: string;
}

export function SwitcherModal({
  isOpen,
  onClose,
  searchQuery,
  onSearchChange,
  placeholder,
  title,
  subtitle,
  shortcut,
  loading = false,
  children,
  emptyMessage = 'No results found',
}: SwitcherModalProps) {
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Focus search input when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => searchInputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed top-20 left-1/2 -translate-x-1/2 w-full max-w-xl bg-white rounded-lg shadow-2xl z-50">
        {/* Search Input */}
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder={placeholder}
              className="input-search py-2"
            />
            <button
              onClick={onClose}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="max-h-96 overflow-y-auto">
          {loading ? (
            <LoadingState message={`Loading ${title.toLowerCase()}...`} />
          ) : (
            children
          )}
        </div>

        {/* Footer Hint */}
        <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 type-caption text-gray-500 flex items-center justify-between rounded-b-lg">
          <span>↑↓ Navigate • Enter Select • Esc Close</span>
          <span className="font-mono">{shortcut}</span>
        </div>
      </div>
    </>
  );
}

// Switcher Section Component
interface SwitcherSectionProps {
  title: string;
  children: ReactNode;
}

export function SwitcherSection({ title, children }: SwitcherSectionProps) {
  return (
    <div className="p-2">
      <div className="px-3 py-2 type-label text-gray-500 uppercase tracking-wide">
        {title}
      </div>
      {children}
    </div>
  );
}

// Switcher Empty State Component
interface SwitcherEmptyProps {
  message: string;
}

export function SwitcherEmpty({ message }: SwitcherEmptyProps) {
  return (
    <div className="p-8 text-center type-body-sm text-gray-400">
      {message}
    </div>
  );
}
