import React, { createContext, useContext, useMemo } from 'react';
import { api } from '@/lib/api';
import { config } from '@/lib/utils/config';

export type FileContextType = 'session' | 'project';

export interface FileContextValue {
  contextType: FileContextType;
  contextId: string;
  isReady: boolean;
  getFileUrl: (filePath: string) => string | null;
  downloadFile: (filePath: string) => Promise<Blob>;
  getFileContent: (filePath: string) => Promise<{ content: string; path: string; readonly: boolean }>;
}

const FileContext = createContext<FileContextValue | null>(null);

interface FileContextProviderProps {
  contextType: FileContextType;
  contextId: string;
  children: React.ReactNode;
}

export function FileContextProvider({ contextType, contextId, children }: FileContextProviderProps) {
  const value = useMemo<FileContextValue>(() => {
    const isReady = Boolean(contextId);

    const getFileUrl = (filePath: string): string | null => {
      if (!isReady || !filePath) return null;

      const baseUrl = config.apiUrl;
      const encodedPath = encodeURIComponent(filePath);

      if (contextType === 'session') {
        return `${baseUrl}/api/v1/sessions/${contextId}/files/download?file_path=${encodedPath}`;
      } else {
        return `${baseUrl}/api/v1/projects/${contextId}/files/download?file_path=${encodedPath}`;
      }
    };

    const downloadFile = async (filePath: string): Promise<Blob> => {
      if (!isReady) {
        throw new Error(`Cannot download file: ${contextType} ID is not set`);
      }

      if (contextType === 'session') {
        return await api.downloadSessionFile(contextId, filePath);
      } else {
        return await api.downloadProjectFile(contextId, filePath);
      }
    };

    const getFileContent = async (filePath: string) => {
      if (!isReady) {
        throw new Error(`Cannot get file content: ${contextType} ID is not set`);
      }

      if (contextType === 'session') {
        return await api.getSessionFileContent(contextId, filePath);
      } else {
        return await api.getProjectFileContent(contextId, filePath);
      }
    };

    return {
      contextType,
      contextId,
      isReady,
      getFileUrl,
      downloadFile,
      getFileContent,
    };
  }, [contextType, contextId]);

  return (
    <FileContext.Provider value={value}>
      {children}
    </FileContext.Provider>
  );
}

export function useFileContext(): FileContextValue {
  const context = useContext(FileContext);

  if (!context) {
    throw new Error('useFileContext must be used within a FileContextProvider');
  }

  return context;
}

// Optional hook that returns null instead of throwing
export function useOptionalFileContext(): FileContextValue | null {
  return useContext(FileContext);
}
