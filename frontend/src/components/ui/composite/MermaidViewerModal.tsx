import { useEffect, useState, useRef } from 'react';
import { X, Download, Maximize2, Minimize2, Network } from 'lucide-react';
import mermaid from 'mermaid';
import DOMPurify from 'dompurify';
import { exportMermaidToPNG } from '@/lib/utils/mermaidExport';

interface MermaidViewerModalProps {
  chart: string;
  title?: string;
  onClose: () => void;
}

export function MermaidViewerModal({ chart, title = 'Mermaid Diagram', onClose }: MermaidViewerModalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [id] = useState(() => `mermaid-modal-${Math.random().toString(36).substring(2, 11)}`);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown, { capture: true });
    return () => window.removeEventListener('keydown', handleKeyDown, { capture: true });
  }, [onClose]);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current || !chart.trim()) {
        return;
      }

      try {
        setError(null);

        // Clear previous content
        containerRef.current.innerHTML = '';

        // Render the diagram with Mermaid (securityLevel: 'strict' configured at init)
        const { svg } = await mermaid.render(id, chart);

        if (containerRef.current) {
          // Sanitize SVG before injection to prevent XSS attacks
          const cleanSvg = DOMPurify.sanitize(svg, {
            USE_PROFILES: { svg: true, svgFilters: true },
            ADD_TAGS: ['foreignObject'], // Allow foreignObject for text wrapping
            ADD_ATTR: ['target', 'xlink:href', 'xmlns:xlink'], // Allow links and namespaces
            KEEP_CONTENT: true // Preserve text content
          });
          containerRef.current.innerHTML = cleanSvg;

          // Make SVG responsive - use viewBox for proper scaling
          const svgElement = containerRef.current.querySelector('svg');
          if (svgElement) {
            // Remove fixed dimensions to allow responsive scaling
            svgElement.removeAttribute('width');
            svgElement.removeAttribute('height');
            svgElement.style.width = '100%';
            svgElement.style.height = '100%';
            svgElement.style.maxWidth = '100%';
            svgElement.style.maxHeight = '100%';
          }
        }
      } catch (err) {
        console.error('Mermaid render error:', err);
        setError(err instanceof Error ? err.message : 'Failed to render diagram');
      }
    };

    renderDiagram();

    // Cleanup: Remove Mermaid's internal state when unmounting
    return () => {
      try {
        const element = document.getElementById(id);
        if (element) {
          element.remove();
        }
      } catch (e) {
        // Ignore cleanup errors
      }
    };
  }, [chart, id]);

  const handleDownloadPNG = async () => {
    if (!containerRef.current) return;

    const svgElement = containerRef.current.querySelector('svg');
    if (!svgElement) return;

    try {
      const filename = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.png`;
      await exportMermaidToPNG(svgElement, filename);
    } catch (err) {
      console.error('Failed to export PNG:', err);
      // TODO: Replace with toast notification for better UX
      alert('Failed to export diagram as PNG. Please try again.');
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.2, 0.2));
  };

  const handleResetZoom = () => {
    setScale(1);
  };

  return (
    <div
      className="fixed inset-0 z-[101] flex items-center justify-center bg-black/50 backdrop-blur-sm p-0 lg:p-4"
      onClick={onClose}
    >
      <div
        className={`bg-white rounded-none lg:rounded-lg w-full h-full flex flex-col ${
          isFullscreen ? 'lg:max-w-full lg:h-full' : 'lg:max-w-6xl lg:h-[85vh]'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 lg:px-6 py-3 lg:py-4 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-center gap-3">
            <Network className="w-5 h-5 flex-shrink-0 text-primary" />
            <div>
              <h2 className="type-title text-gray-900">{title}</h2>
              <p className="type-caption text-gray-500">Mermaid Diagram</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleZoomOut}
              className="px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
              aria-label="Zoom out"
              title="Zoom out"
            >
              −
            </button>
            <button
              onClick={handleResetZoom}
              className="px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
              aria-label="Reset zoom to 100%"
              title="Reset zoom"
            >
              {Math.round(scale * 100)}%
            </button>
            <button
              onClick={handleZoomIn}
              className="px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
              aria-label="Zoom in"
              title="Zoom in"
            >
              +
            </button>
            <div className="w-px h-6 bg-gray-200" aria-hidden="true" />
            <button
              onClick={toggleFullscreen}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label={isFullscreen ? 'Exit fullscreen mode' : 'Enter fullscreen mode'}
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-5 h-5" aria-hidden="true" /> : <Maximize2 className="w-5 h-5" aria-hidden="true" />}
            </button>
            <button
              onClick={handleDownloadPNG}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Download diagram as PNG image"
              title="Download PNG"
            >
              <Download className="w-5 h-5" aria-hidden="true" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Close modal"
              title="Close"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto bg-white flex items-center justify-center p-6">
          {error ? (
            <div className="max-w-4xl w-full">
              {/* Show original code block */}
              <pre className="mb-4 bg-muted text-foreground px-4 py-3 text-sm font-mono overflow-x-auto leading-normal border border-border rounded">
                <code>{chart}</code>
              </pre>

              {/* Error message below */}
              <div className="border border-destructive/50 bg-destructive/10 rounded-md p-3">
                <div className="flex items-start gap-2">
                  <svg
                    className="w-5 h-5 text-destructive mt-0.5 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-destructive">Invalid Mermaid Syntax</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div
              ref={containerRef}
              className="mermaid-diagram w-full h-full max-w-full max-h-full transition-transform"
              style={{ transform: `scale(${scale})`, transformOrigin: 'center' }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
