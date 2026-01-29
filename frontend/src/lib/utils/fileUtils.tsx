/**
 * File Utilities
 *
 * Shared utilities for file handling across the application
 */
import { File, FileCode, FileText, Image as ImageIcon } from 'lucide-react';

export type SimpleFileType = 'image' | 'code' | 'markdown' | 'pdf' | 'text' | 'unknown';

/**
 * Get the appropriate icon for a file type
 */
export function getFileIcon(fileType?: SimpleFileType, className: string = 'w-5 h-5') {
  switch (fileType) {
    case 'image':
      return <ImageIcon className={className} />;
    case 'code':
      return <FileCode className={className} />;
    case 'markdown':
      return <FileText className={className} />;
    case 'pdf':
      return <FileText className={className} />;
    case 'text':
      return <File className={className} />;
    default:
      return <File className={className} />;
  }
}

/**
 * Format file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

/**
 * Download a file from a Blob
 */
export function downloadFile(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Download a file from a URL
 */
export async function downloadFileFromUrl(url: string, filename: string): Promise<void> {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Download failed');
    const blob = await response.blob();
    downloadFile(blob, filename);
  } catch (error) {
    console.error('Error downloading file:', error);
    throw error;
  }
}

/**
 * Get file extension from filename
 */
export function getFileExtension(filename: string): string {
  const parts = filename.split('.');
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
}

/**
 * Detect file type from filename or MIME type
 */
export function detectSimpleFileType(filename: string, mimeType?: string): SimpleFileType {
  const ext = getFileExtension(filename);

  // Check by extension first
  const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'];
  const codeExts = ['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'c', 'cpp', 'h', 'css', 'html', 'json', 'xml', 'yml', 'yaml'];
  const markdownExts = ['md', 'markdown'];

  if (imageExts.includes(ext)) return 'image';
  if (codeExts.includes(ext)) return 'code';
  if (markdownExts.includes(ext)) return 'markdown';
  if (ext === 'pdf') return 'pdf';
  if (ext === 'txt') return 'text';

  // Check by MIME type
  if (mimeType) {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('text/')) return 'text';
    if (mimeType === 'application/pdf') return 'pdf';
  }

  return 'unknown';
}

/**
 * File tree node structure
 */
export interface FileTreeNode {
  path: string;
  name: string;
  type: 'file' | 'directory';
  size?: number;
  modified_at?: string;
  children?: FileTreeNode[];
}

/**
 * Convert flat file list from API to tree structure
 */
export function buildFileTree(files: Array<{
  path: string;
  name: string;
  size: number;
  is_directory: boolean;
  modified_at: string;
}>): FileTreeNode[] {
  // Create a map to hold all nodes by their path
  const nodeMap = new Map<string, FileTreeNode>();
  const rootNodes: FileTreeNode[] = [];

  // First pass: Create all nodes
  files.forEach(file => {
    const node: FileTreeNode = {
      path: file.path,
      name: file.name,
      type: file.is_directory ? 'directory' : 'file',
      size: file.size,
      modified_at: file.modified_at,
      children: file.is_directory ? [] : undefined,
    };
    nodeMap.set(file.path, node);
  });

  // Second pass: Build tree structure
  files.forEach(file => {
    const node = nodeMap.get(file.path)!;

    // Find parent directory
    const pathParts = file.path.split('/');
    if (pathParts.length > 1) {
      // Has a parent directory
      const parentPath = pathParts.slice(0, -1).join('/');
      const parent = nodeMap.get(parentPath);

      if (parent && parent.children) {
        parent.children.push(node);
      } else {
        // Parent not found (shouldn't happen with proper API response)
        rootNodes.push(node);
      }
    } else {
      // Root level file/directory
      rootNodes.push(node);
    }
  });

  // Sort: directories first, then files, alphabetically within each group
  const sortNodes = (nodes: FileTreeNode[]) => {
    nodes.sort((a, b) => {
      // Directories come before files
      if (a.type === 'directory' && b.type === 'file') return -1;
      if (a.type === 'file' && b.type === 'directory') return 1;
      // Alphabetical within same type
      return a.name.localeCompare(b.name);
    });

    // Recursively sort children
    nodes.forEach(node => {
      if (node.children) {
        sortNodes(node.children);
      }
    });
  };

  sortNodes(rootNodes);
  return rootNodes;
}
