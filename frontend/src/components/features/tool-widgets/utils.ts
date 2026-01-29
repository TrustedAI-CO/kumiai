/**
 * Shared utilities for tool widgets
 */

import type { ParsedResult } from './types';

export const WIDGET_HEADER_TEXT_SIZE = "type-body-sm";

/**
 * Parse tool result content from various formats
 */
export function parseResultContent(result: any): ParsedResult {
  if (!result) {
    return { content: '', isError: false };
  }

  let content = '';
  const isError = result.is_error || false;

  if (typeof result.content === 'string') {
    content = result.content;
  } else if (result.content && typeof result.content === 'object') {
    if (result.content.text) {
      content = result.content.text;
    } else if (Array.isArray(result.content)) {
      content = result.content
        .map((c: any) => (typeof c === 'string' ? c : c.text || JSON.stringify(c)))
        .join('\n');
    } else {
      content = JSON.stringify(result.content, null, 2);
    }
  }

  return { content, isError };
}
