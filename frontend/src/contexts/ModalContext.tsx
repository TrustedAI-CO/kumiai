/**
 * ModalContext - Global modal state management
 *
 * Ensures only one modal can be open at a time across the entire application.
 * Provides a centralized way to manage modal states.
 */
import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

type ModalType =
  | 'project-switcher'
  | 'session-switcher'
  | 'project-modal'
  | 'session-modal'
  | 'skill-modal'
  | 'agent-modal'
  | 'file-viewer-modal'
  | 'welcome-modal'
  | null;

interface ModalContextType {
  currentModal: ModalType;
  openModal: (modal: ModalType) => void;
  closeModal: () => void;
  isModalOpen: (modal: ModalType) => boolean;
}

const ModalContext = createContext<ModalContextType | undefined>(undefined);

export function ModalProvider({ children }: { children: ReactNode }) {
  const [currentModal, setCurrentModal] = useState<ModalType>(null);

  const openModal = useCallback((modal: ModalType) => {
    // Close any existing modal and open the new one
    setCurrentModal(modal);
  }, []);

  const closeModal = useCallback(() => {
    setCurrentModal(null);
  }, []);

  const isModalOpen = useCallback((modal: ModalType) => {
    return currentModal === modal;
  }, [currentModal]);

  return (
    <ModalContext.Provider value={{ currentModal, openModal, closeModal, isModalOpen }}>
      {children}
    </ModalContext.Provider>
  );
}

export function useModal() {
  const context = useContext(ModalContext);
  if (context === undefined) {
    throw new Error('useModal must be used within a ModalProvider');
  }
  return context;
}
