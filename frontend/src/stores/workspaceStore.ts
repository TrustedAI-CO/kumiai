/**
 * Workspace Store - Unified state management for workspace UI
 *
 * Consolidates:
 * - Project selection (from App.tsx)
 * - View mode state (from WorkplaceKanban.tsx)
 * - PM expansion state (from WorkplaceKanban.tsx)
 * - Session selection (from WorkplaceKanban.tsx)
 * - Chat context (from App.tsx)
 *
 * Benefits:
 * - Single source of truth
 * - Atomic state updates with proper resets
 * - Proper localStorage persistence via Zustand
 * - Type-safe state management
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { ChatContext } from '@/types/chat';

export type ViewMode = 'kanban' | 'chat' | 'file';
export type BoardViewMode = 'kanban' | 'table';

interface WorkspaceState {
  // Project management
  currentProjectId: string | undefined;

  // View state
  viewMode: ViewMode;
  boardViewMode: BoardViewMode;
  isPMExpanded: boolean;

  // Session management
  selectedSessionId: string | null;

  // Chat context
  chatContext: ChatContext | null;

  // Actions - Project
  setCurrentProjectId: (projectId: string | undefined) => void;

  // Actions - View mode
  setViewMode: (mode: ViewMode) => void;
  setBoardViewMode: (mode: BoardViewMode) => void;
  setPMExpanded: (expanded: boolean) => void;

  // Actions - Session
  setSelectedSessionId: (sessionId: string | null) => void;

  // Actions - Chat context
  setChatContext: (context: ChatContext | null) => void;

  // Composite actions that handle dependent state
  switchProject: (projectId: string | undefined) => void;
  openSession: (sessionId: string) => void;
  closeSession: () => void;

  // Reset
  resetWorkspace: () => void;
}

const defaultState = {
  currentProjectId: undefined,
  viewMode: 'kanban' as ViewMode,
  boardViewMode: 'kanban' as BoardViewMode,
  isPMExpanded: false,
  selectedSessionId: null,
  chatContext: null,
};

/**
 * Workspace store with localStorage persistence
 */
export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      // Initial state
      ...defaultState,

      // Simple setters
      setCurrentProjectId: (projectId) =>
        set({ currentProjectId: projectId }),

      setViewMode: (mode) =>
        set({ viewMode: mode }),

      setBoardViewMode: (mode) =>
        set({ boardViewMode: mode }),

      setPMExpanded: (expanded) =>
        set({ isPMExpanded: expanded }),

      setSelectedSessionId: (sessionId) =>
        set({ selectedSessionId: sessionId }),

      setChatContext: (context) =>
        set({ chatContext: context }),

      // Composite actions with proper state resets

      /**
       * Switch to a different project
       * Resets: PM expansion, selected session, view mode
       */
      switchProject: (projectId) =>
        set({
          currentProjectId: projectId,
          isPMExpanded: false,
          selectedSessionId: null,
          viewMode: 'kanban',
          chatContext: null,
        }),

      /**
       * Open a session (agent instance)
       * Sets: selected session, switches to chat view
       */
      openSession: (sessionId) =>
        set({
          selectedSessionId: sessionId,
          viewMode: 'chat',
        }),

      /**
       * Close current session
       * Resets: selected session, returns to kanban view
       */
      closeSession: () =>
        set({
          selectedSessionId: null,
          viewMode: 'kanban',
        }),

      // Reset to defaults
      resetWorkspace: () => set(defaultState),
    }),
    {
      name: 'kumiai-workspace-storage', // localStorage key
      storage: createJSONStorage(() => {
        try {
          return localStorage;
        } catch {
          // Fallback to in-memory storage if localStorage is not available
          return {
            getItem: () => null,
            setItem: () => {},
            removeItem: () => {},
          };
        }
      }),

      // Persist everything except transient UI state
      partialize: (state) => ({
        currentProjectId: state.currentProjectId,
        boardViewMode: state.boardViewMode,
        isPMExpanded: state.isPMExpanded,
        chatContext: state.chatContext,
        // Don't persist: viewMode, selectedSessionId (session-specific)
      }),

      // Handle errors gracefully
      onRehydrateStorage: () => (state, error) => {
        if (error) {
          console.warn('Failed to rehydrate workspace store:', error);
        }
      },
    }
  )
);
