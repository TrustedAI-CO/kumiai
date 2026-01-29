/**
 * File type detection utilities for rich file viewing
 */

export type FileType = 'image' | 'pdf' | 'markdown' | 'code' | 'text' | 'binary';

interface FileTypeInfo {
  type: FileType;
  language?: string; // For code files
  mimeType?: string; // For images
}

const IMAGE_EXTENSIONS = new Set([
  'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico', 'avif'
]);

const PDF_EXTENSIONS = new Set(['pdf']);

const MARKDOWN_EXTENSIONS = new Set(['md', 'markdown', 'mdx']);

const CODE_LANGUAGE_MAP: Record<string, string> = {
  // JavaScript/TypeScript
  'js': 'javascript',
  'jsx': 'jsx',
  'ts': 'typescript',
  'tsx': 'tsx',
  'mjs': 'javascript',
  'cjs': 'javascript',

  // Web
  'html': 'html',
  'htm': 'html',
  'css': 'css',
  'scss': 'scss',
  'sass': 'sass',
  'less': 'less',

  // Python
  'py': 'python',
  'pyw': 'python',
  'pyx': 'python',

  // Rust
  'rs': 'rust',

  // Go
  'go': 'go',

  // C/C++
  'c': 'c',
  'cpp': 'cpp',
  'cc': 'cpp',
  'cxx': 'cpp',
  'h': 'c',
  'hpp': 'cpp',
  'hh': 'cpp',
  'hxx': 'cpp',

  // Java/Kotlin
  'java': 'java',
  'kt': 'kotlin',
  'kts': 'kotlin',

  // C#
  'cs': 'csharp',

  // Ruby
  'rb': 'ruby',

  // PHP
  'php': 'php',

  // Shell
  'sh': 'bash',
  'bash': 'bash',
  'zsh': 'bash',
  'fish': 'bash',

  // Config/Data
  'json': 'json',
  'yaml': 'yaml',
  'yml': 'yaml',
  'toml': 'toml',
  'xml': 'xml',
  'ini': 'ini',
  'conf': 'ini',
  'cfg': 'ini',

  // SQL
  'sql': 'sql',

  // Docker/Terraform
  'dockerfile': 'dockerfile',
  'tf': 'hcl',

  // Other
  'graphql': 'graphql',
  'gql': 'graphql',
  'proto': 'protobuf',
  'lua': 'lua',
  'vim': 'vim',
  'r': 'r',
  'swift': 'swift',
  'dart': 'dart',
};

const TEXT_EXTENSIONS = new Set([
  'txt', 'log', 'csv', 'tsv', 'env', 'gitignore', 'gitattributes',
  'editorconfig', 'prettierrc', 'eslintrc', 'LICENSE', 'README'
]);

const IMAGE_MIME_TYPES: Record<string, string> = {
  'jpg': 'image/jpeg',
  'jpeg': 'image/jpeg',
  'png': 'image/png',
  'gif': 'image/gif',
  'webp': 'image/webp',
  'svg': 'image/svg+xml',
  'bmp': 'image/bmp',
  'ico': 'image/x-icon',
  'avif': 'image/avif',
};

/**
 * Get file extension from filename or path
 */
function getExtension(filePath: string): string {
  const parts = filePath.split('/').pop()?.split('.');
  if (!parts || parts.length < 2) return '';
  return parts.pop()?.toLowerCase() || '';
}

/**
 * Get filename without extension
 */
function getBasename(filePath: string): string {
  const filename = filePath.split('/').pop() || '';
  const parts = filename.split('.');
  if (parts.length === 1) return filename;
  parts.pop();
  return parts.join('.');
}

/**
 * Detect file type from filename or path
 */
export function detectFileType(filePath: string): FileTypeInfo {
  const ext = getExtension(filePath);
  const basename = getBasename(filePath).toLowerCase();

  // Check for special files without extensions
  if (basename === 'dockerfile') {
    return { type: 'code', language: 'dockerfile' };
  }

  if (basename === 'makefile') {
    return { type: 'code', language: 'makefile' };
  }

  // Images
  if (IMAGE_EXTENSIONS.has(ext)) {
    return {
      type: 'image',
      mimeType: IMAGE_MIME_TYPES[ext] || 'image/*'
    };
  }

  // PDFs
  if (PDF_EXTENSIONS.has(ext)) {
    return { type: 'pdf' };
  }

  // Markdown
  if (MARKDOWN_EXTENSIONS.has(ext)) {
    return { type: 'markdown' };
  }

  // Code
  if (ext in CODE_LANGUAGE_MAP) {
    return {
      type: 'code',
      language: CODE_LANGUAGE_MAP[ext]
    };
  }

  // Plain text
  if (TEXT_EXTENSIONS.has(ext) || !ext) {
    return { type: 'text' };
  }

  // Default to binary for unknown extensions
  return { type: 'binary' };
}

/**
 * Check if file can be viewed in the app
 */
export function isViewableFile(filePath: string): boolean {
  const info = detectFileType(filePath);
  return info.type !== 'binary';
}

/**
 * Get appropriate viewer component name for file
 */
export function getViewerType(filePath: string): FileType {
  return detectFileType(filePath).type;
}

/**
 * Get syntax highlighting language for code file
 */
export function getCodeLanguage(filePath: string): string | undefined {
  const info = detectFileType(filePath);
  return info.type === 'code' ? info.language : undefined;
}

/**
 * Get MIME type for image file
 */
export function getImageMimeType(filePath: string): string | undefined {
  const info = detectFileType(filePath);
  return info.type === 'image' ? info.mimeType : undefined;
}
