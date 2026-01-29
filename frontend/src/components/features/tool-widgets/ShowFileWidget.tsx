import React, { useState, Suspense } from 'react';
import { Eye, Download, Image, FileCode, FileText, File as FileIcon, Loader2 } from 'lucide-react';
import { useOptionalFileContext } from '@/contexts/FileContext';
import { detectFileType } from '@/lib/utils/fileTypeDetector';
import { FileViewerModal } from '@/components/features/files/FileViewerModal';
import { CollapsibleWidget } from './CollapsibleWidget';
import type { ToolWidgetProps } from './types';

const WIDGET_HEADER_TEXT_SIZE = 'type-body-sm';

function parseResultContent(result: any): { content: string; isError: boolean } {
  if (!result) return { content: '', isError: false };

  let content = '';
  let isError = false;

  if (typeof result === 'string') {
    content = result;
  } else if (result.content) {
    if (Array.isArray(result.content)) {
      content = result.content
        .map((c: any) => (typeof c === 'string' ? c : c.text || ''))
        .join('');
    } else if (typeof result.content === 'string') {
      content = result.content;
    } else if (result.content.text) {
      content = result.content.text;
    }
  }

  if (result.isError || content.toLowerCase().includes('error')) {
    isError = true;
  }

  return { content, isError };
}

export const ShowFileWidget: React.FC<ToolWidgetProps> = ({ toolArgs, result }) => {
  const filePath = (toolArgs.file_path || toolArgs.path) as string | undefined;
  const fileContext = useOptionalFileContext();
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // Handle missing file path
  if (!filePath) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <div className="flex items-center gap-2 type-body-sm text-red-800">
          <Eye className="h-4 w-4 flex-shrink-0" />
          <span>Error: No file path provided</span>
        </div>
      </div>
    );
  }

  const fileInfo = detectFileType(filePath);
  const fileName = filePath.split('/').pop() || filePath;
  const isImage = fileInfo.type === 'image';
  const { content: resultContent, isError } = parseResultContent(result);

  // Get file URL if context is available
  const fileUrl = fileContext?.isReady ? fileContext.getFileUrl(filePath) : null;

  // Handle download
  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setDownloadError(null);
    if (!fileContext?.isReady) return;

    try {
      const blob = await fileContext.downloadFile(filePath);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download file:', err);
      setDownloadError(err instanceof Error ? err.message : 'Download failed');
    }
  };

  // Format file size
  const formatSize = (path: string): string => {
    if (fileInfo.language) return fileInfo.language;
    return fileInfo.type;
  };

  // Get file icon based on type
  const getFileIcon = () => {
    const iconClass = 'w-5 h-5 text-gray-400';

    switch (fileInfo.type) {
      case 'image':
        return <Image className={iconClass} />;
      case 'code':
        return <FileCode className={iconClass} />;
      case 'markdown':
      case 'text':
        return <FileText className={iconClass} />;
      default:
        return <FileIcon className={iconClass} />;
    }
  };

  const header = (
    <>
      <Eye className="h-3.5 w-3.5 text-primary flex-shrink-0" />
      <span className={`${WIDGET_HEADER_TEXT_SIZE} text-gray-600 flex-shrink-0`}>Show:</span>
      <code className={`${WIDGET_HEADER_TEXT_SIZE} font-mono text-gray-600 truncate`} title={filePath}>
        {filePath}
      </code>
    </>
  );

  return (
    <CollapsibleWidget header={header} defaultExpanded={true} toolArgs={toolArgs} result={result}>
      <div className="p-4">
        {/* File card - horizontal layout matching sent attachment card */}
        <div
          className="inline-flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors max-w-md group cursor-pointer"
          onClick={() => {
            if (fileContext?.isReady) {
              setIsViewerOpen(true);
            }
          }}
          title={fileContext?.isReady ? `Click to view ${fileName}` : 'File context not available'}
        >
          {/* Thumbnail */}
          <div className="w-16 h-16 flex-shrink-0">
            {isImage && fileUrl && !imageError ? (
              <img
                src={fileUrl}
                alt={fileName}
                className="w-full h-full object-cover rounded"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gray-100 rounded">
                {getFileIcon()}
              </div>
            )}
          </div>

          {/* File Info */}
          <div className="flex-1 min-w-0">
            <div className="font-medium type-body-sm text-gray-900 truncate" title={fileName}>
              {fileName}
            </div>
            <div className="type-caption text-gray-500 mt-0.5 flex items-center gap-2">
              <span>{formatSize(filePath)}</span>
            </div>
          </div>

          {/* Actions */}
          {fileContext?.isReady && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={handleDownload}
                className="p-1.5 text-gray-600 hover:bg-gray-200 rounded transition-colors"
                title="Download file"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Warning if no file context */}
        {!fileContext?.isReady && (
          <div className="mt-2 type-caption text-amber-600 bg-amber-50 border border-amber-200 rounded p-2">
            ⚠️ Cannot preview file: File context not available
          </div>
        )}

        {/* Download error */}
        {downloadError && (
          <div className="mt-2 type-caption text-red-600 bg-red-50 border border-red-200 rounded p-2">
            {downloadError}
          </div>
        )}

        {/* Result */}
        {result && resultContent && (
          <div
            className={`p-2 rounded border type-caption ${
              isError
                ? 'bg-red-50 border-red-200 text-red-700'
                : 'bg-green-50 border-green-200 text-green-700'
            }`}
          >
            {resultContent}
          </div>
        )}

        {/* File viewer modal */}
        {isViewerOpen && fileContext?.isReady && (
          <Suspense
            fallback={
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                <Loader2 className="w-8 h-8 text-white animate-spin" />
              </div>
            }
          >
            <FileViewerModal
              mode={fileContext.contextType}
              projectId={fileContext.contextType === 'project' ? fileContext.contextId : undefined}
              sessionId={fileContext.contextType === 'session' ? fileContext.contextId : undefined}
              filePath={filePath}
              onClose={() => setIsViewerOpen(false)}
            />
          </Suspense>
        )}
      </div>
    </CollapsibleWidget>
  );
};
