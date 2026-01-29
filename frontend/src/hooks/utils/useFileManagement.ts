import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { FileNode } from '@/types';

interface UseFileManagementProps {
  entityId: string | null;
  entityType: 'agent' | 'skill';
  onMetadataUpdate?: () => Promise<void>;
  protectedFiles?: string[];
}

interface UseFileManagementReturn {
  // State
  files: FileNode[];
  selectedFile: string | null;
  fileContent: string;
  expandedDirs: Set<string>;
  isCreatingFile: boolean;
  newFilePath: string;
  isRenamingFile: boolean;
  renameNewPath: string;

  // Actions
  setFileContent: (content: string) => void;
  setNewFilePath: (path: string) => void;
  setRenameNewPath: (path: string) => void;
  setIsCreatingFile: (value: boolean) => void;
  setIsRenamingFile: (value: boolean) => void;
  handleFileSelect: (filePath: string) => Promise<void>;
  handleFileSave: () => Promise<void>;
  handleCreateFile: () => Promise<void>;
  handleDeleteFile: () => Promise<void>;
  handleRenameFile: () => Promise<void>;
  toggleDirectory: (path: string) => void;
  loadFiles: () => Promise<void>;
  clearSelection: () => void;
}

/**
 * Custom hook for managing files in agents and skills
 * Provides unified file operations: select, create, delete, rename, save
 */
export function useFileManagement({
  entityId,
  entityType,
  onMetadataUpdate,
  protectedFiles = ['CLAUDE.md'],
}: UseFileManagementProps): UseFileManagementReturn {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const [isCreatingFile, setIsCreatingFile] = useState(false);
  const [newFilePath, setNewFilePath] = useState('');
  const [isRenamingFile, setIsRenamingFile] = useState(false);
  const [renameNewPath, setRenameNewPath] = useState('');

  // Load files when entity changes
  useEffect(() => {
    if (entityId) {
      loadFiles();
    }
  }, [entityId]);

  // Auto-save with debounce
  useEffect(() => {
    if (!entityId || !selectedFile || !fileContent) return;

    const timeoutId = setTimeout(() => {
      handleFileSave();
    }, 1000); // Save after 1 second of inactivity

    return () => clearTimeout(timeoutId);
  }, [fileContent]);

  const loadFiles = async () => {
    if (!entityId) return;

    try {
      const data = entityType === 'agent'
        ? await api.getAgentFiles(entityId)
        : await api.getSkillFiles(entityId);
      setFiles(data);
    } catch (error) {
      console.error(`Failed to load ${entityType} files:`, error);
    }
  };

  const handleFileSelect = async (filePath: string) => {
    if (!entityId) return;

    try {
      setSelectedFile(filePath);
      const result = entityType === 'agent'
        ? await api.getAgentFileContent(entityId, filePath)
        : await api.getSkillFileContent(entityId, filePath);
      setFileContent(result.content);
    } catch (error) {
      console.error('Failed to load file:', error);
    }
  };

  const handleFileSave = async () => {
    if (!entityId || !selectedFile) return;

    try {
      if (entityType === 'agent') {
        await api.updateAgentFileContent(entityId, selectedFile, fileContent);
      } else {
        await api.updateSkillFileContent(entityId, selectedFile, fileContent);
      }

      // Reload metadata if main file was edited
      if (selectedFile === 'CLAUDE.md' && onMetadataUpdate) {
        await onMetadataUpdate();
      }
    } catch (error) {
      console.error('Failed to save file:', error);
    }
  };

  const handleCreateFile = async () => {
    if (!entityId || !newFilePath.trim()) return;

    try {
      // Create the file with empty content
      if (entityType === 'agent') {
        await api.updateAgentFileContent(entityId, newFilePath, '');
      } else {
        await api.updateSkillFileContent(entityId, newFilePath, '');
      }

      // Reload file tree
      await loadFiles();

      // Select the newly created file
      setSelectedFile(newFilePath);
      setFileContent('');

      // Reset new file state
      setIsCreatingFile(false);
      setNewFilePath('');
    } catch (error) {
      console.error('Failed to create file:', error);
      alert('Failed to create file');
    }
  };

  const handleDeleteFile = async () => {
    if (!entityId || !selectedFile) return;

    // Check if file is protected
    if (protectedFiles.includes(selectedFile)) {
      alert(`Cannot delete ${selectedFile} - this file is protected`);
      return;
    }

    if (!confirm(`Are you sure you want to delete "${selectedFile}"?`)) return;

    try {
      if (entityType === 'agent') {
        await api.deleteAgentFile(entityId, selectedFile);
      } else {
        await api.deleteSkillFile(entityId, selectedFile);
      }

      // Reload file tree
      await loadFiles();

      // Clear selection
      clearSelection();
    } catch (error) {
      console.error('Failed to delete file:', error);
      alert('Failed to delete file');
    }
  };

  const handleRenameFile = async () => {
    if (!entityId || !selectedFile || !renameNewPath.trim()) return;

    // TODO: Implement rename API endpoint
    alert('Rename functionality coming soon');
    setIsRenamingFile(false);
    setRenameNewPath('');
  };

  const toggleDirectory = (path: string) => {
    setExpandedDirs(prev => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setFileContent('');
  };

  return {
    files,
    selectedFile,
    fileContent,
    expandedDirs,
    isCreatingFile,
    newFilePath,
    isRenamingFile,
    renameNewPath,
    setFileContent,
    setNewFilePath,
    setRenameNewPath,
    setIsCreatingFile,
    setIsRenamingFile,
    handleFileSelect,
    handleFileSave,
    handleCreateFile,
    handleDeleteFile,
    handleRenameFile,
    toggleDirectory,
    loadFiles,
    clearSelection,
  };
}
