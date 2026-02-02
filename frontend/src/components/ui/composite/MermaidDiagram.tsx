import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { Eye, Download } from 'lucide-react';
import { MermaidViewerModal } from './MermaidViewerModal';

interface MermaidDiagramProps {
  chart: string;
  className?: string;
  title?: string;
}

let mermaidInitialized = false;

export function MermaidDiagram({ chart, className = '', title = 'Diagram' }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [id] = useState(() => `mermaid-${Math.random().toString(36).substr(2, 9)}`);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    if (!mermaidInitialized) {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'strict',
        fontFamily: 'Noto Sans Display, ui-sans-serif, system-ui, sans-serif',
      });
      mermaidInitialized = true;
    }
  }, []);

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
        }
      } catch (err) {
        console.error('Mermaid render error:', err);
        setError(err instanceof Error ? err.message : 'Failed to render diagram');
      }
    };

    renderDiagram();
  }, [chart, id]);

  const handleDownloadPNG = async (e: React.MouseEvent) => {
    e.stopPropagation();

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

  const handleOpenModal = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowModal(true);
  };

  if (error) {
    return (
      <div className={`border border-destructive/50 bg-destructive/10 rounded-md p-4 ${className}`}>
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
    );
  }

  return (
    <>
      <div className={`relative group ${className}`}>
        {/* Action Buttons - shown on hover at right side */}
        <div className="absolute top-2 right-2 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleOpenModal}
            className="p-1.5 bg-white/90 hover:bg-white text-gray-700 rounded-md shadow-sm border border-gray-200 transition-colors"
            title="View fullscreen"
          >
            <Eye className="w-4 h-4" />
          </button>
          <button
            onClick={handleDownloadPNG}
            className="p-1.5 bg-white/90 hover:bg-white text-gray-700 rounded-md shadow-sm border border-gray-200 transition-colors"
            title="Download as PNG"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>

        {/* Diagram - clickable to open modal */}
        <div
          ref={containerRef}
          onClick={handleOpenModal}
          className="mermaid-diagram flex justify-center items-center p-4 bg-muted/30 rounded-md overflow-auto cursor-pointer hover:bg-muted/40 transition-colors"
        />
      </div>

      {/* Viewer Modal */}
      {showModal && (
        <MermaidViewerModal
          chart={chart}
          title={title}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  );
}
