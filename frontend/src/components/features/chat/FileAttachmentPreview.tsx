import React, { useEffect, useState } from 'react';
import { X, File, Image, FileText, FileCode, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/primitives/button';
import { AttachedFile } from '@/hooks/utils/useFileUpload';

interface FileAttachmentPreviewProps {
  attachedFile: AttachedFile;
  onRemove: () => void;
}

export const FileAttachmentPreview: React.FC<FileAttachmentPreviewProps> = ({
  attachedFile,
  onRemove,
}) => {
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
  };

  const getFileIcon = () => {
    const type = attachedFile.type;
    if (type.startsWith('image/')) return <Image className="w-5 h-5" />;
    if (type.startsWith('text/')) return <FileText className="w-5 h-5" />;
    if (type.includes('json') || type.includes('javascript') || type.includes('typescript')) {
      return <FileCode className="w-5 h-5" />;
    }
    return <File className="w-5 h-5" />;
  };

  // Show image thumbnail for image files
  const [thumbnail, setThumbnail] = useState<string | null>(null);
  useEffect(() => {
    if (attachedFile.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => setThumbnail(e.target?.result as string);
      reader.readAsDataURL(attachedFile.file);
    }
  }, [attachedFile.file, attachedFile.type]);

  return (
    <div className="relative group">
      {/* File preview box */}
      <div className="relative">
        {/* Circular progress indicator (uploading) */}
        {attachedFile.status === 'uploading' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <svg className="w-full h-full" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                className="text-gray-200"
              />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                className="text-blue-500"
                strokeDasharray={`${attachedFile.progress * 2.827} 282.7`}
                strokeDashoffset="0"
                transform="rotate(-90 50 50)"
              />
            </svg>
          </div>
        )}

        <div className="w-14 h-14 rounded-lg border-2 bg-white p-1.5 flex items-center justify-center relative overflow-hidden">
          {thumbnail ? (
            <img
              src={thumbnail}
              alt={attachedFile.name}
              className="w-full h-full object-cover rounded"
            />
          ) : (
            <div className="text-gray-400">
              {getFileIcon()}
            </div>
          )}

          {/* Status overlay */}
          {attachedFile.status === 'prepared' && (
            <div className="absolute inset-0 bg-green-500/10 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
          )}

          {attachedFile.status === 'uploading' && (
            <div className="absolute inset-0 bg-blue-500/10 flex items-center justify-center">
              <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
            </div>
          )}

          {attachedFile.status === 'error' && (
            <div className="absolute inset-0 bg-red-500/10 flex items-center justify-center">
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
          )}
        </div>
      </div>

      {/* File info */}
      <div className="mt-1 text-xs text-center max-w-[64px]">
        <p className="truncate font-medium text-gray-700" title={attachedFile.name}>
          {attachedFile.name}
        </p>
        <p className="text-gray-500">{formatSize(attachedFile.size)}</p>
        {attachedFile.status === 'uploading' && (
          <p className="text-blue-600 mt-0.5">{attachedFile.progress}%</p>
        )}
        {attachedFile.status === 'error' && (
          <p className="text-red-600 mt-0.5 truncate" title={attachedFile.error}>
            Error
          </p>
        )}
      </div>

      {/* Remove button */}
      <Button
        variant="destructive"
        size="icon"
        className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
        onClick={onRemove}
      >
        <X className="w-3 h-3" />
      </Button>
    </div>
  );
};
