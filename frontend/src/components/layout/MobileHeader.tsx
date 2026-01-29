import { Menu } from 'lucide-react';
import { layout } from '@/styles/design-system';

interface MobileHeaderProps {
  title?: string;
  onMenuClick?: () => void;
  showMenuButton?: boolean;
}

export function MobileHeader({ title, onMenuClick, showMenuButton = false }: MobileHeaderProps) {
  return (
    <header
      className="lg:hidden fixed top-0 left-0 right-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-center z-30"
      style={{ height: layout.mobile.headerHeight }}
    >
      {/* Menu Button (Left) */}
      {showMenuButton && onMenuClick && (
        <button
          onClick={onMenuClick}
          className="absolute left-4 p-2 hover:bg-gray-100 rounded-lg transition-colors touch-target"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5 text-gray-700" />
        </button>
      )}

      {/* Logo and Title (Center) */}
      <div className="flex items-center gap-2">
        <img src="/logo.png" alt="kumiAI" className="w-8 h-8" />
        <h1 className="type-title text-gray-900">
          {title || 'kumiAI'}
        </h1>
      </div>
    </header>
  );
}
