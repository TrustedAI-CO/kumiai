import { useEffect, useState, useRef } from 'react';
import { X, Download, Maximize2, Minimize2, Network } from 'lucide-react';
import mermaid from 'mermaid';

interface MermaidViewerModalProps {
  chart: string;
  title?: string;
  onClose: () => void;
}

export function MermaidViewerModal({ chart, title = 'Mermaid Diagram', onClose }: MermaidViewerModalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [id] = useState(() => `mermaid-modal-${Math.random().toString(36).substr(2, 9)}`);
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

        // Render the diagram
        const { svg } = await mermaid.render(id, chart);

        if (containerRef.current) {
          containerRef.current.innerHTML = svg;

          // Make SVG responsive and larger
          const svgElement = containerRef.current.querySelector('svg');
          if (svgElement) {
            svgElement.style.maxWidth = '100%';
            svgElement.style.height = 'auto';
            svgElement.style.width = '100%';
          }
        }
      } catch (err) {
        console.error('Mermaid render error:', err);
        setError(err instanceof Error ? err.message : 'Failed to render diagram');
      }
    };

    renderDiagram();
  }, [chart, id]);

  const handleDownloadPNG = async () => {
    if (!containerRef.current) return;

    const svgElement = containerRef.current.querySelector('svg');
    if (!svgElement) return;

    try {
      // Clone the SVG to avoid modifying the original
      const clonedSvg = svgElement.cloneNode(true) as SVGSVGElement;

      // Ensure proper namespace
      clonedSvg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

      // Get SVG dimensions
      const viewBox = clonedSvg.getAttribute('viewBox');
      let width: number, height: number;

      if (viewBox) {
        const parts = viewBox.split(' ');
        width = parseFloat(parts[2]);
        height = parseFloat(parts[3]);
      } else {
        width = parseFloat(clonedSvg.getAttribute('width') || '800');
        height = parseFloat(clonedSvg.getAttribute('height') || '600');
      }

      // Set explicit dimensions
      clonedSvg.setAttribute('width', width.toString());
      clonedSvg.setAttribute('height', height.toString());

      // Create a canvas
      const canvas = document.createElement('canvas');
      const scaleFactor = 2; // Higher quality
      canvas.width = width * scaleFactor;
      canvas.height = height * scaleFactor;
      const ctx = canvas.getContext('2d');

      if (!ctx) return;

      // Serialize the SVG to data URL
      const svgData = new XMLSerializer().serializeToString(clonedSvg);
      const svgDataUrl = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));

      const img = new Image();
      img.onload = () => {
        try {
          // Fill white background
          ctx.fillStyle = 'white';
          ctx.fillRect(0, 0, canvas.width, canvas.height);

          // Scale and draw the image
          ctx.scale(scaleFactor, scaleFactor);
          ctx.drawImage(img, 0, 0, width, height);

          // Convert to PNG and download
          canvas.toBlob((blob) => {
            if (blob) {
              const downloadUrl = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = downloadUrl;
              a.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.png`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(downloadUrl);
            }
          }, 'image/png');
        } catch (err) {
          console.error('Failed to convert to PNG:', err);
          alert('Failed to export diagram as PNG. Please try again.');
        }
      };

      img.onerror = (err) => {
        console.error('Failed to load SVG as image:', err);
        alert('Failed to export diagram as PNG. Please try again.');
      };

      img.src = svgDataUrl;
    } catch (err) {
      console.error('Failed to export PNG:', err);
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
              title="Zoom out"
            >
              −
            </button>
            <button
              onClick={handleResetZoom}
              className="px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
              title="Reset zoom"
            >
              {Math.round(scale * 100)}%
            </button>
            <button
              onClick={handleZoomIn}
              className="px-2 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
              title="Zoom in"
            >
              +
            </button>
            <div className="w-px h-6 bg-gray-200" />
            <button
              onClick={toggleFullscreen}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
            </button>
            <button
              onClick={handleDownloadPNG}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Download PNG"
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
        <div className="flex-1 overflow-auto bg-white flex items-center justify-center p-6">
          {error ? (
            <div className="border border-destructive/50 bg-destructive/10 rounded-md p-4 max-w-2xl">
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
                  <p className="text-xs text-destructive/80 mt-1">{error}</p>
                </div>
              </div>
            </div>
          ) : (
            <div
              ref={containerRef}
              className="mermaid-diagram w-full max-w-full transition-transform"
              style={{ transform: `scale(${scale})`, transformOrigin: 'center' }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
