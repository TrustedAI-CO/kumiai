import type { Components } from 'react-markdown';
import React from 'react';

/**
 * Shared markdown components for consistent rendering across the application.
 * Used by MessageBubble and MessageGroup components.
 */
export const markdownComponents: Components = {
  p: ({ children }) => <p className="mb-2.5 leading-normal text-gray-900">{children}</p>,
  ul: ({ children }) => <ul className="list-none ml-5 mb-2.5 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-none ml-5 mb-2.5 space-y-1 counter-reset-[item]">{children}</ol>,
  li: ({ children }) => (
    <li className="leading-normal before:content-['–'] before:absolute before:-ml-4 before:text-gray-600 relative">
      {children}
    </li>
  ),
  h1: ({ children }) => <h1 className="type-display mt-6 mb-2.5 text-gray-900 tracking-tight">{children}</h1>,
  h2: ({ children }) => <h2 className="type-display mt-5 mb-2 text-gray-900">{children}</h2>,
  h3: ({ children }) => <h3 className="type-headline mt-4 mb-2 text-gray-900">{children}</h3>,
  h4: ({ children }) => <h4 className="type-title mt-3 mb-1 text-gray-600">{children}</h4>,
  h5: ({ children }) => <h5 className="type-body font-medium mt-2 mb-1 text-gray-600">{children}</h5>,
  h6: ({ children }) => <h6 className="type-subtitle mt-2 mb-1 text-gray-600 uppercase tracking-wide">{children}</h6>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-border pl-4 pr-3 pt-2 pb-1 my-3 bg-muted/50/30 text-gray-900 italic leading-normal rounded-r">
      {children}
    </blockquote>
  ),
  code: ({ className, children, ...props }: any) => {
    const isInline = !className?.includes('language-');

    if (isInline) {
      return (
        <code className="inline-block bg-muted/50 text-foreground mx-1 px-1 py-0.5 font-mono text-[90%] rounded-sm border border-border">
          {children}
        </code>
      );
    }
    return (
      <code className="block bg-muted/50 text-foreground px-3 py-2 my-3 type-body-sm font-mono overflow-x-auto leading-normal border border-border rounded">
        {children}
      </code>
    );
  },
  pre: ({ children }) => <pre className="my-3">{children}</pre>,
  a: ({ href, children }) => (
    <a href={href} className="text-primary underline decoration-1 underline-offset-2 hover:text-foreground transition-colors" target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
  hr: () => <hr className="my-6 border-t border-border" />,
  table: ({ children }) => (
    <div className="overflow-x-auto my-5">
      <table className="w-full border-collapse type-body-sm">
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
