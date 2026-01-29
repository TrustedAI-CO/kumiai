import React from 'react';
import { File, FileText, FileCode, Image } from 'lucide-react';
import { detectFileType, FileType } from '@/lib/utils';
import { config } from '@/lib/utils/config';

interface FilePreviewCardProps {
  sessionId: string;
  filePath: string;
  onView: () => void;
}

export function FilePreviewCard({ sessionId, filePath, onView }: FilePreviewCardProps) {
  const fileInfo = detectFileType(filePath);
  const fileName = filePath.split('/').pop() || filePath;

  // Construct download URL for the file
  // Backend now supports both relative and absolute paths
  const fileUrl = `${config.apiUrl}/sessions/${sessionId}/files/download?file_path=${encodeURIComponent(filePath)}`;

  // Get icon based on file type
  const getFileIcon = (type: FileType) => {
    const iconClass = "w-5 h-5";
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
        return <File className={iconClass} />;
    }
  };

  return (
    <div
      onClick={onView}
      className="inline-flex items-center gap-3 p-3 mt-2 mb-2 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 hover:border-gray-300 transition-colors max-w-md"
    >
      {/* Thumbnail or Icon */}
      <div className="flex-shrink-0">
        {fileInfo.type === 'image' ? (
          <img
            src={fileUrl}
            alt={fileName}
            className="w-16 h-16 object-cover rounded"
            onError={(e) => {
              // Fallback to icon if image fails to load
              e.currentTarget.style.display = 'none';
              e.currentTarget.parentElement!.innerHTML = getFileIcon('image').props.children;
            }}
          />
        ) : (
          <div className="w-16 h-16 flex items-center justify-center bg-gray-100 rounded">
            {getFileIcon(fileInfo.type)}
          </div>
        )}
      </div>

      {/* File Info */}
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm text-gray-900 truncate">
          {fileName}
        </div>
        <div className="text-xs text-gray-500 mt-0.5">
          {fileInfo.type === 'code' && fileInfo.language
            ? `${fileInfo.language} • Click to view`
            : 'Click to view'}
        </div>
      </div>
    </div>
  );
}
