/**
 * FileContentView - File editor modal with syntax highlighting
 *
 * Displays and edits file content in a modal overlay.
 * Supports auto-save and read-only mode for protected files.
 */
import { useState, useEffect, useRef } from 'react';
import { X, Download, Lock, Save } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';
import { LoadingState } from '@/ui';

interface FileContentViewProps {
  mode: 'project' | 'session';
  projectId?: string;
  sessionId?: string;
  filePath: string | null;
  onClose: () => void;
}

export function FileContentView({
  mode,
  projectId,
  sessionId,
  filePath,
  onClose,
}: FileContentViewProps) {
  // Don't render if no file selected
  if (!filePath) return null;
  const [content, setContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [readonly, setReadonly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const saveTimeoutRef = useRef<NodeJS.Timeout>();

  // Load file content when component mounts or file changes
  useEffect(() => {
    loadFileContent();

    return () => {
      // Clear auto-save timeout on unmount
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [filePath, mode, projectId, sessionId]);

  // Auto-save when content changes
  useEffect(() => {
    // Don't auto-save if readonly or content hasn't changed
    if (readonly || content === originalContent) {
      return;
    }

    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Set new timeout for auto-save (1 second debounce)
    saveTimeoutRef.current = setTimeout(() => {
      saveFileContent();
    }, 1000);

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [content, readonly, originalContent]);

  const loadFileContent = async () => {
    setLoading(true);
    setError(null);

    try {
      let fileData: { content: string; path: string; readonly: boolean };

      if (mode === 'project' && projectId) {
        fileData = await api.getProjectFileContent(projectId, filePath);
      } else if (mode === 'session' && sessionId) {
        fileData = await api.getSessionFileContent(sessionId, filePath);
      } else {
        setError('Invalid context: missing project or session ID');
        return;
      }

      setContent(fileData.content);
      setOriginalContent(fileData.content);
      setReadonly(fileData.readonly);
    } catch (err) {
      console.error('Failed to load file content:', err);
      setError(err instanceof Error ? err.message : 'Failed to load file');
    } finally {
      setLoading(false);
    }
  };

  const saveFileContent = async () => {
    if (readonly) return;

    setSaving(true);
    setError(null);

    try {
      if (mode === 'project' && projectId) {
        await api.updateProjectFileContent(projectId, filePath, content);
      } else if (mode === 'session' && sessionId) {
        await api.updateSessionFileContent(sessionId, filePath, content);
      }

      setOriginalContent(content);
      setLastSaved(new Date());
    } catch (err) {
      console.error('Failed to save file:', err);
      setError(err instanceof Error ? err.message : 'Failed to save file');
    } finally {
      setSaving(false);
    }
  };

  const handleDownload = async () => {
    try {
      let blob: Blob;

      if (mode === 'project' && projectId) {
        blob = await api.downloadProjectFile(projectId, filePath);
      } else if (mode === 'session' && sessionId) {
        blob = await api.downloadSessionFile(sessionId, filePath);
      } else {
        return;
      }

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filePath.split('/').pop() || 'file';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download file:', err);
      setError('Failed to download file');
    }
  };

  const handleManualSave = async () => {
    await saveFileContent();
  };

  const formatTime = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 5) return 'just now';
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    return date.toLocaleTimeString();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="flex flex-col h-[90vh] w-[90vw] max-w-6xl bg-white rounded-lg shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
      {/* Header */}
      <div className="flex-none h-16 px-5 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-gray-700">
            {filePath}
          </h2>
          {readonly && (
            <div className="flex items-center gap-1 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
              <Lock className="w-3 h-3" />
              <span>Read-only</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Save status */}
          {!readonly && (
            <div className="text-xs text-gray-500">
              {saving && 'Saving...'}
              {!saving && lastSaved && `Auto-saved ${formatTime(lastSaved)}`}
              {!saving && !lastSaved && content !== originalContent && 'Unsaved changes'}
            </div>
          )}

          {/* Manual save button */}
          {!readonly && content !== originalContent && (
            <button
              onClick={handleManualSave}
              disabled={saving}
              className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
              title="Save now"
            >
              <Save className="w-4 h-4" />
            </button>
          )}

          {/* Download button */}
          <button
            onClick={handleDownload}
            className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors"
            title="Download file"
          >
            <Download className="w-4 h-4" />
          </button>

          {/* Close button */}
          <button
            onClick={onClose}
            className="p-1.5 text-gray-600 hover:bg-gray-100 rounded transition-colors"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden">
        {loading && (
          <LoadingState message="Loading file..." />
        )}

        {error && (
          <div className="flex items-center justify-center h-full">
            <div className="text-sm text-red-500">{error}</div>
          </div>
        )}

        {!loading && !error && (
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            disabled={readonly}
            className={cn(
              "w-full h-full p-4 font-mono text-sm resize-none focus:outline-none",
              readonly && "bg-gray-50 text-gray-700 cursor-not-allowed"
            )}
            spellCheck={false}
          />
        )}
      </div>
      </div>
    </div>
  );
}
