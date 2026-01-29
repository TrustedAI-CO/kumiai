import { ReactNode, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '../primitives/card';

export type ModalSize = 'small' | 'medium' | 'large';

interface StandardModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  size?: ModalSize;
  className?: string;
  disableEscapeKey?: boolean;
}

const sizeClasses: Record<ModalSize, string> = {
  small: 'max-w-3xl',
  medium: 'max-w-5xl',
  large: 'max-w-6xl',
};

export function StandardModal({
  isOpen,
  onClose,
  children,
  size = 'small',
  className = '',
  disableEscapeKey = false,
}: StandardModalProps) {
  useEffect(() => {
    if (!isOpen || disableEscapeKey) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, disableEscapeKey]);

  const modalContent = (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-[100]"
            onClick={onClose}
          />
          {/* Modal Content */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 flex items-center justify-center z-[101] p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <Card
              className={`w-full ${sizeClasses[size]} bg-white shadow-2xl h-[70vh] overflow-hidden flex flex-col ${className}`}
            >
              {children}
            </Card>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );

  return createPortal(modalContent, document.body);
}
