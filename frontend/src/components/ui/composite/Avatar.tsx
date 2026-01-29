import { useMemo } from 'react';
import { createAvatar } from '@dicebear/core';
import { notionists } from '@dicebear/collection';

interface AvatarProps {
  seed: string | null | undefined;
  size?: number;
  className?: string;
  color?: string;
}

export function Avatar({ seed, size = 48, className = '', color }: AvatarProps) {
  // Check if seed is an uploaded image (base64 or URL)
  const isUploadedImage = seed && (seed.startsWith('data:image/') || seed.startsWith('http://') || seed.startsWith('https://'));

  const avatarSvg = useMemo(() => {
    if (isUploadedImage) return null;

    // Use a default seed if none provided
    const actualSeed = seed || 'default-avatar';
    const avatar = createAvatar(notionists, {
      seed: actualSeed,
      size,
    });
    return avatar.toString();
  }, [seed, size, isUploadedImage]);

  // If it's an uploaded image, render as img tag
  if (isUploadedImage) {
    return (
      <div
        className={`rounded-full overflow-hidden flex items-center justify-center ${color ? '' : 'bg-muted/50'} ${className}`}
        style={{
          width: size,
          height: size,
          ...(color ? { backgroundColor: color } : {})
        }}
      >
        <img
          src={seed}
          alt="Avatar"
          className="w-full h-full object-cover"
        />
      </div>
    );
  }

  // Otherwise render generated avatar
  return (
    <div
      className={`rounded-full overflow-hidden flex items-center justify-center ${color ? '' : 'bg-muted/50'} ${className}`}
      style={{
        width: size,
        height: size,
        ...(color ? { backgroundColor: color } : {})
      }}
      dangerouslySetInnerHTML={{ __html: avatarSvg || '' }}
    />
  );
}
