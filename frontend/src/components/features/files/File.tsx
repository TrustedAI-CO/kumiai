import { useState, Suspense, lazy } from 'react';
import { File as FileIcon, Image, FileText, FileCode, Download, Eye, AlertCircle, Loader2 } from 'lucide-react';
import { useFileContext } from '@/contexts/FileContext';
import type { FileAttachment } from '@/types/chat';
import { detectFileType } from '@/lib/utils';

const FileViewerModal = lazy(() => import('./FileViewerModal').then(m => ({ default: m.FileViewerModal })));

interface FileProps {
  attachment: FileAttachment;
  mode?: 'compact' | 'expanded';
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
}

function getFileIconComponent(mimeType?: string, filePath?: string) {
  const fileInfo = filePath ? detectFileType(filePath) : null;
  const type = fileInfo?.type || (mimeType?.startsWith('image/') ? 'image' : 'text');

  const iconClass = "w-5 h-5 flex-shrink-0";

  switch (type) {
    case 'image':
      return <Image className={iconClass} />;
    case 'pdf':
      return <FileText className={iconClass} />;
    case 'code':
      return <FileCode className={iconClass} />;
    case 'markdown':
    case 'text':
      return <FileText className={iconClass} />;
    default:
      return <FileIcon className={iconClass} />;
  }
}

function FileThumbnail({ attachment, fileUrl }: { attachment: FileAttachment; fileUrl: string | null }) {
  const [imageError, setImageError] = useState(false);
  const fileInfo = detectFileType(attachment.path);
  const isImage = fileInfo.type === 'image' || attachment.mimeType?.startsWith('image/');

  if (!isImage || imageError || !fileUrl) {
    return (
      <div className="w-16 h-16 flex items-center justify-center bg-gray-100 rounded">
        {getFileIconComponent(attachment.mimeType, attachment.path)}
      </div>
    );
  }

  return (
    <img
      src={attachment.thumbnail || fileUrl}
      alt={attachment.name}
      className="w-16 h-16 object-cover rounded"
      onError={() => setImageError(true)}
    />
  );
}

function FileError({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm">
      <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
      <span className="text-red-800 flex-1">{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function File({ attachment, mode = 'compact' }: FileProps) {
  const fileContext = useFileContext();
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // Validate file context
  if (!fileContext.isReady) {
    return (
      <FileError
        message={`Cannot display file: ${fileContext.contextType} context not ready`}
      />
    );
  }

  const fileUrl = fileContext.getFileUrl(attachment.path);
  const fileInfo = detectFileType(attachment.path);

  const handleDownload = async () => {
    setDownloadError(null);
    try {
      const blob = await fileContext.downloadFile(attachment.path);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = attachment.name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download file:', err);
      setDownloadError(err instanceof Error ? err.message : 'Download failed');
    }
  };

  if (mode === 'compact') {
    return (
      <>
        <div
          className="inline-flex items-center gap-3 p-3 mt-2 mb-2 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors max-w-md group cursor-pointer"
          onClick={() => setIsViewerOpen(true)}
          title={`Click to view ${attachment.name}`}
        >
          {/* Thumbnail */}
          <FileThumbnail attachment={attachment} fileUrl={fileUrl} />

          {/* File Info */}
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm text-gray-900 truncate" title={attachment.name}>
              {attachment.name}
            </div>
            <div className="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
              <span>{formatSize(attachment.size)}</span>
              {fileInfo.type === 'code' && fileInfo.language && (
                <>
                  <span>•</span>
                  <span>{fileInfo.language}</span>
                </>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation(); // Prevent triggering card click
                handleDownload();
              }}
              className="p-1.5 text-gray-600 hover:bg-gray-200 rounded transition-colors"
              title="Download file"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {downloadError && (
          <FileError message={downloadError} onRetry={handleDownload} />
        )}

        {/* Lazy-load viewer modal */}
        {isViewerOpen && (
          <Suspense fallback={
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
              <Loader2 className="w-8 h-8 text-white animate-spin" />
            </div>
          }>
            <FileViewerModal
              mode={fileContext.contextType}
              projectId={fileContext.contextType === 'project' ? fileContext.contextId : undefined}
              sessionId={fileContext.contextType === 'session' ? fileContext.contextId : undefined}
              filePath={attachment.path}
              onClose={() => setIsViewerOpen(false)}
            />
          </Suspense>
        )}
      </>
    );
  }

  // Expanded mode - show more details
  return (
    <div className="p-4 border border-gray-200 rounded-lg bg-white">
      <div className="flex items-start gap-3">
        <FileThumbnail attachment={attachment} fileUrl={fileUrl} />
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900">{attachment.name}</h4>
          <p className="text-sm text-gray-500 mt-1">
            {formatSize(attachment.size)}
            {fileInfo.type === 'code' && fileInfo.language && ` • ${fileInfo.language}`}
          </p>
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => setIsViewerOpen(true)}
              className="px-3 py-1.5 text-sm bg-primary hover:bg-primary text-white rounded transition-colors flex items-center gap-1.5"
            >
              <Eye className="w-4 h-4" />
              View
            </button>
            <button
              onClick={handleDownload}
              className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors flex items-center gap-1.5"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
          </div>
        </div>
      </div>

      {downloadError && (
        <div className="mt-3">
          <FileError message={downloadError} onRetry={handleDownload} />
        </div>
      )}
    </div>
  );
}
