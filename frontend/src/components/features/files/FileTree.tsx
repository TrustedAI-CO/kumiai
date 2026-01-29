/**
 * FileTree Component
 *
 * Recursive file tree viewer with folder expansion and file selection
 * Consolidates duplicate FileTree from Skills.tsx and Agents.tsx
 */
import { useState } from 'react';
import { ChevronDown, ChevronRight, Folder, File } from 'lucide-react';
import { formatFileSize } from '@/lib/utils';

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  children?: FileNode[];
}

interface FileTreeProps {
  node: FileNode;
  selectedPath: string | null;
  onSelect: (path: string) => void;
  level?: number;
}

export function FileTree({
  node,
  selectedPath,
  onSelect,
  level = 0
}: FileTreeProps) {
  const [isExpanded, setIsExpanded] = useState(level === 0);

  const isSelected = selectedPath === node.path;
  const paddingLeft = `${level * 1.5}rem`;

  if (node.type === 'directory') {
    return (
      <div>
        {/* Folder */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-gray-100 transition-colors text-left"
          style={{ paddingLeft }}
        >
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
          <Folder className="w-4 h-4 text-gray-500" />
          <span className="type-subtitle text-gray-700">{node.name}</span>
        </button>

        {/* Children */}
        {isExpanded && node.children && (
          <div>
            {node.children.map((child) => (
              <FileTree
                key={child.path}
                node={child}
                selectedPath={selectedPath}
                onSelect={onSelect}
                level={level + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // File
  return (
    <button
      onClick={() => onSelect(node.path)}
      className={`w-full flex items-center justify-between gap-2 px-3 py-1.5 hover:bg-gray-100 transition-colors text-left ${
        isSelected ? 'bg-muted/50' : ''
      }`}
      style={{ paddingLeft }}
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <File className="w-4 h-4 text-gray-400 flex-shrink-0" />
        <span className="type-body-sm text-gray-900 truncate">{node.name}</span>
      </div>
      {node.size !== undefined && (
        <span className="type-caption text-gray-400 flex-shrink-0">
          {formatFileSize(node.size)}
        </span>
      )}
    </button>
  );
}
