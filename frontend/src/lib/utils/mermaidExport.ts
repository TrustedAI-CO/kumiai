/**
 * Utility for exporting Mermaid diagrams as PNG images
 */

export async function exportMermaidToPNG(
  svgElement: SVGSVGElement,
  filename: string
): Promise<void> {
  return new Promise((resolve, reject) => {
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

      if (!ctx) {
        reject(new Error('Could not get canvas context'));
        return;
      }

      // Serialize the SVG to data URL (using modern approach without deprecated btoa/unescape)
      const svgData = new XMLSerializer().serializeToString(clonedSvg);
      const svgDataUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgData);

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
              a.download = filename;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(downloadUrl);
              resolve();
            } else {
              reject(new Error('Failed to create blob'));
            }
          }, 'image/png');
        } catch (err) {
          reject(err);
        }
      };

      img.onerror = (err) => {
        reject(new Error('Failed to load SVG as image'));
      };

      img.src = svgDataUrl;
    } catch (err) {
      reject(err);
    }
  });
}
