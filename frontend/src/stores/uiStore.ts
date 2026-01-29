/**
 * UI Store - Manages UI state (sidebars, modals, etc.)
 *
 * Replaces localStorage-based UI state in MainLayout.tsx and other components
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface UIState {
  // Sidebar state
  leftSidebarOpen: boolean;
  rightSidebarOpen: boolean;

  // Modal state
  preferencesModalOpen: boolean;
  fileViewerModal: {
    isOpen: boolean;
    filePath?: string;
    projectId?: string;
    sessionId?: string;
  };

  // Actions - Sidebars
  setLeftSidebarOpen: (open: boolean) => void;
  setRightSidebarOpen: (open: boolean) => void;
  toggleLeftSidebar: () => void;
  toggleRightSidebar: () => void;

  // Actions - Modals
  openPreferencesModal: () => void;
  closePreferencesModal: () => void;
  openFileViewer: (filePath: string, projectId?: string, sessionId?: string) => void;
  closeFileViewer: () => void;

  // Reset
  resetUI: () => void;
}

const defaultState = {
  leftSidebarOpen: true,
  rightSidebarOpen: false,
  preferencesModalOpen: false,
  fileViewerModal: {
    isOpen: false,
    filePath: undefined,
    projectId: undefined,
    sessionId: undefined
  }
};

/**
 * UI store with localStorage persistence for sidebar state
 */
export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      // Initial state
      ...defaultState,

      // Sidebar actions
      setLeftSidebarOpen: (open) =>
        set({ leftSidebarOpen: open }),

      setRightSidebarOpen: (open) =>
        set({ rightSidebarOpen: open }),

      toggleLeftSidebar: () =>
        set((state) => ({ leftSidebarOpen: !state.leftSidebarOpen })),

      toggleRightSidebar: () =>
        set((state) => ({ rightSidebarOpen: !state.rightSidebarOpen })),

      // Modal actions
      openPreferencesModal: () =>
        set({ preferencesModalOpen: true }),

      closePreferencesModal: () =>
        set({ preferencesModalOpen: false }),

      openFileViewer: (filePath, projectId, sessionId) =>
        set({
          fileViewerModal: {
            isOpen: true,
            filePath,
            projectId,
            sessionId
          }
        }),

      closeFileViewer: () =>
        set({
          fileViewerModal: {
            isOpen: false,
            filePath: undefined,
            projectId: undefined,
            sessionId: undefined
          }
        }),

      // Reset
      resetUI: () => set(defaultState)
    }),
    {
      name: 'kumiai-ui-storage', // localStorage key
      storage: createJSONStorage(() => {
        try {
          return localStorage;
        } catch {
          // Fallback to in-memory storage if localStorage is not available
          return {
            getItem: () => null,
            setItem: () => {},
            removeItem: () => {}
          };
        }
      }),

      // Only persist sidebar state, not modals
      partialize: (state) => ({
        leftSidebarOpen: state.leftSidebarOpen,
        rightSidebarOpen: state.rightSidebarOpen
      }),

      // Handle errors gracefully
      onRehydrateStorage: () => (state, error) => {
        if (error) {
          console.warn('Failed to rehydrate UI store:', error);
        }
      }
    }
  )
);
