/**
 * ColorPicker Component
 *
 * Color selection popup with predefined palette
 * Consolidates duplicate ColorPicker from Skills.tsx and Agents.tsx
 */
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ColorPickerProps {
  isOpen: boolean;
  onClose: () => void;
  selectedColor: string;
  onSelectColor: (color: string) => void;
  anchorEl?: HTMLElement | null;
  colors?: string[];
}

const DEFAULT_COLORS = [
  '#4A90E2', '#E24A4A', '#4AE290', '#E2904A', '#904AE2',
  '#4AE2E2', '#E2E24A', '#E24A90', '#90E24A', '#4A4AE2',
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
  '#DFE6E9', '#74B9FF', '#A29BFE', '#FD79A8', '#FDCB6E',
];

export function ColorPicker({
  isOpen,
  onClose,
  selectedColor,
  onSelectColor,
  anchorEl,
  colors = DEFAULT_COLORS,
}: ColorPickerProps) {
  // Calculate position based on anchor element
  const getPosition = () => {
    if (!anchorEl) return { top: '100%', left: 0 };

    const rect = anchorEl.getBoundingClientRect();
    return {
      top: rect.bottom + 8,
      left: rect.left,
    };
  };

  const position = getPosition();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={onClose}
          />

          {/* Color Picker Popup */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ type: 'spring', damping: 25, stiffness: 400 }}
            className="fixed z-50 bg-white rounded-lg shadow-xl border border-gray-200 p-3"
            style={{
              top: anchorEl ? position.top : '50%',
              left: anchorEl ? position.left : '50%',
              transform: anchorEl ? 'none' : 'translate(-50%, -50%)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="grid grid-cols-5 gap-2">
              {colors.map((color) => (
                <button
                  key={color}
                  onClick={() => {
                    onSelectColor(color);
                    onClose();
                  }}
                  className={cn(
                    'w-8 h-8 rounded-md transition-all hover:scale-110',
                    selectedColor === color && 'ring-2 ring-offset-2 ring-ring'
                  )}
                  style={{ backgroundColor: color }}
                  title={color}
                  aria-label={`Select color ${color}`}
                />
              ))}
            </div>

            {/* Custom Color Input */}
            <div className="mt-3 pt-3 border-t border-gray-200">
              <input
                type="color"
                value={selectedColor}
                onChange={(e) => onSelectColor(e.target.value)}
                className="w-full h-8 rounded cursor-pointer"
                title="Pick custom color"
              />
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
