import { useEffect, useState } from 'react';
import { X, Download, FileText, Image as ImageIcon, FileCode, File } from 'lucide-react';
import { LoadingState, EmptyState } from '@/components/ui';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import type { Components } from 'react-markdown';
import { Document, Page, pdfjs } from 'react-pdf';
import { detectFileType } from '@/lib/utils';
import { api } from '@/lib/api';
import { config } from '@/lib/utils/config';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface FileViewerModalProps {
  mode: 'project' | 'session';
  projectId?: string;
  sessionId?: string;
  filePath: string | null;
  onClose: () => void;
}

// Custom markdown components matching MessageBubble style
const markdownComponents: Components = {
  p: ({ children }) => <p className="mb-2.5 leading-normal text-gray-900">{children}</p>,
  ul: ({ children }) => <ul className="list-none ml-5 mb-2.5 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-none ml-5 mb-2.5 space-y-1 counter-reset-[item]">{children}</ol>,
  li: ({ children }) => (
    <li className="leading-normal before:content-['–'] before:absolute before:-ml-4 before:text-gray-600 relative">
      {children}
    </li>
  ),
  h1: ({ children }) => <h1 className="text-3xl font-semibold mt-6 mb-2.5 text-gray-900 tracking-tight">{children}</h1>,
  h2: ({ children }) => <h2 className="text-2xl font-semibold mt-5 mb-2 text-gray-900">{children}</h2>,
  h3: ({ children }) => <h3 className="text-xl font-semibold mt-4 mb-2 text-gray-900">{children}</h3>,
  h4: ({ children }) => <h4 className="text-lg font-medium mt-3 mb-1 text-gray-600">{children}</h4>,
  h5: ({ children }) => <h5 className="text-base font-medium mt-2 mb-1 text-gray-600">{children}</h5>,
  h6: ({ children }) => <h6 className="text-sm font-medium mt-2 mb-1 text-gray-600 uppercase tracking-wide">{children}</h6>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-border pl-4 pr-3 pt-2 pb-1 my-3 bg-muted/50 text-foreground italic leading-normal rounded-r">
      {children}
    </blockquote>
  ),
  code: ({ inline, className, children, ...props }: any) => {
    const isInline = inline ?? !className?.includes('language-');

    if (isInline) {
      return (
        <code className="inline-block bg-muted text-foreground mx-1 px-1 py-0.5 font-mono text-[90%] rounded-sm border border-border">
          {children}
        </code>
      );
    }
    return (
      <code className="block bg-muted text-foreground px-3 py-2 my-3 text-sm font-mono overflow-x-auto leading-normal border border-border rounded">
        {children}
      </code>
    );
  },
  pre: ({ children }) => <pre className="my-3">{children}</pre>,
  a: ({ href, children }) => (
    <a href={href} className="text-primary underline decoration-1 underline-offset-2 hover:text-primary/90 transition-colors" target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
  hr: () => <hr className="my-6 border-t border-border" />,
  table: ({ children }) => (
    <div className="overflow-x-auto my-5">
      <table className="w-full border-collapse text-sm">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => <thead>{children}</thead>,
  tbody: ({ children }) => <tbody>{children}</tbody>,
  tr: ({ children }) => <tr className="border-b border-border">{children}</tr>,
  th: ({ children }) => <th className="px-3 py-2 text-left font-normal text-gray-900 border-b-2 border-gray-900">{children}</th>,
  td: ({ children }) => <td className="px-3 py-2 text-gray-900">{children}</td>,
  strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  del: ({ children }) => <del className="line-through text-gray-600">{children}</del>,
  br: () => <br />,
};

export function FileViewerModal({ mode, projectId, sessionId, filePath, onClose }: FileViewerModalProps) {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);

  const fileInfo = filePath ? detectFileType(filePath) : null;
  const fileName = filePath?.split('/').pop() || 'file';

  useEffect(() => {
    if (!filePath) return;

    const loadFile = async () => {
      setLoading(true);
      setError(null);

      try {
        if (fileInfo?.type === 'image' || fileInfo?.type === 'pdf') {
          // For binary files, we'll use the download endpoint
          setContent(''); // Will use different rendering
        } else {
          // For text files, fetch content
          const response = mode === 'project'
            ? await api.getProjectFileContent(projectId!, filePath)
            : await api.getSessionFileContent(sessionId!, filePath);
          setContent(response.content);
        }
      } catch (err) {
        console.error('Failed to load file:', err);
        setError(err instanceof Error ? err.message : 'Failed to load file');
      } finally {
        setLoading(false);
      }
    };

    loadFile();
  }, [filePath, mode, projectId, sessionId, fileInfo?.type]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleDownload = async () => {
    if (!filePath) return;

    try {
      const blob = mode === 'project'
        ? await api.downloadProjectFile(projectId!, filePath)
        : await api.downloadSessionFile(sessionId!, filePath);

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
      alert(err instanceof Error ? err.message : 'Failed to download file');
    }
  };

  const getFileUrl = () => {
    if (!filePath) return '';
    const encodedPath = encodeURIComponent(filePath);
    return mode === 'project'
      ? `${config.apiUrl}/api/v1/projects/${projectId}/files/download?file_path=${encodedPath}`
      : `${config.apiUrl}/api/v1/sessions/${sessionId}/files/download?file_path=${encodedPath}`;
  };

  const getFileIcon = () => {
    switch (fileInfo?.type) {
      case 'image': return <ImageIcon className="w-5 h-5 flex-shrink-0" />;
      case 'code': return <FileCode className="w-5 h-5 flex-shrink-0" />;
      case 'markdown': return <FileText className="w-5 h-5 flex-shrink-0" />;
      case 'pdf': return <FileText className="w-5 h-5 flex-shrink-0" />;
      case 'text': return <File className="w-5 h-5 flex-shrink-0" />;
      default: return <File className="w-5 h-5 flex-shrink-0" />;
    }
  };

  if (!filePath) return null;

  return (
    <div
      className="fixed inset-0 z-[101] flex items-center justify-center bg-black/50 backdrop-blur-sm p-0 lg:p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-none lg:rounded-lg w-full h-full lg:max-w-6xl lg:h-[70vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 lg:px-6 py-3 lg:py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            {getFileIcon()}
            <div>
              <h2 className="type-title text-gray-900">{fileName}</h2>
              <p className="type-caption text-gray-500">{filePath}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Download file"
            >
              <Download className="w-5 h-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 bg-white">
          {loading && (
            <LoadingState message="Loading..." />
          )}

          {error && (
            <div className="text-center text-red-500 py-12 type-body">
              {error}
            </div>
          )}

          {!loading && !error && (
            <>
              {/* Markdown Viewer */}
              {fileInfo?.type === 'markdown' && (
                <div className="type-body leading-relaxed break-words">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw]}
                    components={markdownComponents}
                  >
                    {content}
                  </ReactMarkdown>
                </div>
              )}

              {/* Code Viewer */}
              {fileInfo?.type === 'code' && (
                <div className="bg-muted rounded-lg border border-border overflow-hidden">
                  <pre className="font-mono type-body-sm text-foreground overflow-x-auto">
                    {content.split('\n').map((line, i) => (
                      <div key={i} className="flex hover:bg-muted/80">
                        <span className="inline-block w-12 text-right pr-3 text-muted-foreground select-none flex-shrink-0 border-r border-border bg-background type-caption">
                          {i + 1}
                        </span>
                        <span className="px-3 flex-1">{line || ' '}</span>
                      </div>
                    ))}
                  </pre>
                </div>
              )}

              {/* Text Viewer */}
              {fileInfo?.type === 'text' && (
                <pre className="font-mono type-body-sm text-foreground whitespace-pre-wrap bg-muted p-4 rounded-lg border border-border">
                  {content}
                </pre>
              )}

              {/* Image Viewer */}
              {fileInfo?.type === 'image' && (
                <div className="flex items-center justify-center min-h-[400px]">
                  <img
                    src={getFileUrl()}
                    alt={fileName}
                    className="max-w-full max-h-[70vh] object-contain rounded-lg"
                  />
                </div>
              )}

              {/* PDF Viewer */}
              {fileInfo?.type === 'pdf' && (
                <div className="flex flex-col items-center">
                  <Document
                    file={getFileUrl()}
                    onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                    className="max-w-full"
                  >
                    <Page
                      pageNumber={pageNumber}
                      className=""
                      renderTextLayer={false}
                      renderAnnotationLayer={false}
                    />
                  </Document>
                  {numPages > 1 && (
                    <div className="flex items-center gap-4 mt-4">
                      <button
                        onClick={() => setPageNumber(p => Math.max(1, p - 1))}
                        disabled={pageNumber <= 1}
                        className="px-3 py-1 bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed rounded type-body-sm"
                      >
                        Previous
                      </button>
                      <span className="type-body-sm text-gray-700">
                        Page {pageNumber} of {numPages}
                      </span>
                      <button
                        onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}
                        disabled={pageNumber >= numPages}
                        className="px-3 py-1 bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed rounded type-body-sm"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Binary/Unknown */}
              {fileInfo?.type === 'binary' && (
                <EmptyState
                  icon={File}
                  title="Cannot preview this file type"
                  description="Click the download button to view it locally"
                  centered
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
