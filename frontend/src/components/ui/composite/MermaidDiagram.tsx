import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import DOMPurify from 'dompurify';
import { Eye, Download } from 'lucide-react';
import { MermaidViewerModal } from './MermaidViewerModal';
import { exportMermaidToPNG } from '@/lib/utils/mermaidExport';

interface MermaidDiagramProps {
  chart: string;
  className?: string;
  title?: string;
}

let mermaidInitialized = false;

export function MermaidDiagram({ chart, className = '', title = 'Diagram' }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [id] = useState(() => `mermaid-${Math.random().toString(36).substring(2, 11)}`);
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

        // Render the diagram with Mermaid (securityLevel: 'strict' configured at init)
        const { svg } = await mermaid.render(id, chart);

        if (containerRef.current) {
          // Sanitize SVG before injection to prevent XSS attacks
          // Even though Mermaid has securityLevel: 'strict', defense in depth is important
          const cleanSvg = DOMPurify.sanitize(svg, {
            USE_PROFILES: { svg: true, svgFilters: true }
          });
          containerRef.current.innerHTML = cleanSvg;
        }
      } catch (err) {
        console.error('Mermaid render error:', err);
        setError(err instanceof Error ? err.message : 'Failed to render diagram');
      }
    };

    renderDiagram();

    // Cleanup: Remove Mermaid's internal state for this diagram when unmounting
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

  const handleDownloadPNG = async (e: React.MouseEvent) => {
    e.stopPropagation();

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
            aria-label="View diagram in fullscreen"
            title="View fullscreen"
          >
            <Eye className="w-4 h-4" aria-hidden="true" />
          </button>
          <button
            onClick={handleDownloadPNG}
            className="p-1.5 bg-white/90 hover:bg-white text-gray-700 rounded-md shadow-sm border border-gray-200 transition-colors"
            aria-label="Download diagram as PNG"
            title="Download as PNG"
          >
            <Download className="w-4 h-4" aria-hidden="true" />
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
