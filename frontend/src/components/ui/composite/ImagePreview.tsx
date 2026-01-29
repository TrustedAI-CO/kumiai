/**
 * ImagePreview Component
 *
 * Displays image preview with error handling and fallback
 */
import { useState } from 'react';
import { Image as ImageIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ImagePreviewProps {
  src: string;
  alt: string;
  className?: string;
  fallbackIcon?: React.ReactNode;
  onError?: () => void;
}

export function ImagePreview({
  src,
  alt,
  className,
  fallbackIcon,
  onError,
}: ImagePreviewProps) {
  const [hasError, setHasError] = useState(false);

  const handleError = () => {
    setHasError(true);
    onError?.();
  };

  if (hasError) {
    return (
      <div className={cn(
        'flex items-center justify-center bg-gray-100 rounded',
        className
      )}>
        {fallbackIcon || <ImageIcon className="w-12 h-12 text-gray-400" />}
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className={cn('object-contain', className)}
      onError={handleError}
      loading="lazy"
    />
  );
}
