/**
 * ChatInput Component
 *
 * Handles user input, file uploads, and message sending.
 */

import React, { useState, useRef, useImperativeHandle, forwardRef } from 'react';
import { Send, Loader2, StopCircle, Paperclip } from 'lucide-react';
import { Textarea } from '@/components/ui/primitives/textarea';
import { Button } from '@/components/ui/primitives/button';
import { cn } from '@/lib/utils';
import { useFileUpload } from '@/hooks/utils/useFileUpload';
import { FileAttachmentPreview } from '@/components/features/chat/FileAttachmentPreview';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (fileMetadata?: string) => Promise<void> | void;
  disabled?: boolean;
  isSending?: boolean;
  error?: string | null;
  placeholder?: string;
  onInterrupt?: () => void;
  sessionId: string;
}

export interface ChatInputHandle {
  addFiles: (files: File[]) => Promise<void>;
}

export const ChatInput = forwardRef<ChatInputHandle, ChatInputProps>(({
  value,
  onChange,
  onSend,
  disabled = false,
  isSending = false,
  error,
  placeholder = 'Type a message...',
  onInterrupt,
  sessionId,
}, ref) => {
  const [isComposing, setIsComposing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // File upload functionality
  const {
    attachedFiles,
    addFiles,
    removeFile,
    commitFiles,
    hasFiles,
  } = useFileUpload(sessionId);

  // Expose addFiles method to parent components
  useImperativeHandle(ref, () => ({
    addFiles,
  }));

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      // Allow sending even when session is processing (queue-based architecture)
      if (!disabled && (value.trim() || hasFiles)) {
        handleSendWithFiles();
      }
    }
  };

  const handleSendClick = () => {
    // Allow sending even when session is processing (queue-based architecture)
    if (!disabled && (value.trim() || hasFiles)) {
      handleSendWithFiles();
    }
  };

  const handleSendWithFiles = async () => {
    try {
      let fileMetadata = '';

      // Commit files first if any are attached
      if (hasFiles) {
        const result = await commitFiles();
        fileMetadata = result.messageText;
      }

      // Send message with file metadata
      await onSend(fileMetadata);
    } catch (err) {
      console.error('Failed to send message with files:', err);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  // File input handlers
  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      addFiles(files);
    }
    // Reset input so same file can be selected again
    e.target.value = '';
  };

  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.types.includes('Files')) {
      setIsDragging(true);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set to false if leaving the container itself
    if (e.currentTarget === e.target) {
      setIsDragging(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      addFiles(files);
    }
  };

  const handleContainerClick = (e: React.MouseEvent) => {
    // Focus textarea when clicking anywhere in the input container
    // Exclude clicks on buttons and other interactive elements
    if (
      textareaRef.current &&
      !disabled &&
      e.target !== textareaRef.current &&
      !(e.target as HTMLElement).closest('button') &&
      !(e.target as HTMLElement).closest('input[type="file"]')
    ) {
      textareaRef.current.focus();
    }
  };

  return (
    <div className="space-y-2">
      {/* Error message */}
      {error && (
        <div className="mx-4 p-3 bg-destructive/10 border border-destructive/20 text-destructive type-body-sm rounded-lg flex items-start gap-2 animate-in fade-in slide-in-from-top-1">
          <span className="flex-1">{error}</span>
        </div>
      )}

      {/* File previews */}
      {attachedFiles.length > 0 && (
        <div className="mx-4 px-4 py-3 bg-muted/30 rounded-lg border border-input">
          <div className="flex flex-wrap gap-3">
            {attachedFiles.map((file) => (
              <FileAttachmentPreview
                key={file.id || file.name}
                attachedFile={file}
                onRemove={() => removeFile(file.id || file.name)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="relative px-4 pb-4 pt-2">
        <div
          className={cn(
            "relative rounded-lg border bg-background shadow-sm transition-all cursor-text",
            isDragging
              ? "border-primary bg-primary/5 ring-2 ring-primary/20"
              : "border-input focus-within:ring-1 focus-within:ring-ring/30 focus-within:border-input"
          )}
          onClick={handleContainerClick}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {/* Drag overlay */}
          {isDragging && (
            <div className="absolute inset-0 flex items-center justify-center bg-primary/5 rounded-lg pointer-events-none z-10">
              <div className="text-sm font-medium text-primary">Drop files here</div>
            </div>
          )}

          {/* Top options bar */}
          <div className="flex items-center gap-1 px-3 pt-2 pb-0">
            {/* File attach button */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={handleFileSelect}
              aria-label="Attach files"
            />
            <Button
              onClick={handleFileButtonClick}
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-foreground hover:bg-accent"
              aria-label="Attach files"
              title="Attach files"
              disabled={disabled}
            >
              <Paperclip className="w-3.5 h-3.5" />
            </Button>

            {/* Spacer */}
            <div className="flex-1" />

            {/* Processing spinner */}
            {isSending && (
              <div className="flex items-center justify-center w-7 h-7">
                <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
              </div>
            )}

            {/* Interrupt button (only shown when processing) */}
            {isSending && onInterrupt && (
              <Button
                onClick={onInterrupt}
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10"
                aria-label="Interrupt"
                title="Stop current operation"
              >
                <StopCircle className="w-4 h-4" />
              </Button>
            )}
          </div>

          {/* Main input area */}
          <div className="flex items-center gap-2">
            <Textarea
              ref={textareaRef}
              value={value}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              onCompositionStart={() => setIsComposing(true)}
              onCompositionEnd={() => setIsComposing(false)}
              placeholder={placeholder}
              disabled={disabled}
              rows={1}
              className={cn(
                "min-h-[52px] max-h-[120px] resize-none border-0 shadow-none focus-visible:ring-0 px-4 py-3 overflow-y-auto",
                "placeholder:text-muted-foreground/60"
              )}
              aria-label="Chat message input"
            />

            {/* Send button */}
            <div className="flex items-center pr-1 flex-shrink-0">
              <Button
                onClick={handleSendClick}
                disabled={disabled || (!value.trim() && !hasFiles)}
                size="icon"
                variant="ghost"
                className={cn(
                  "h-9 w-8 shrink-0 transition-colors",
                  (value.trim() || hasFiles) && !disabled
                    ? "text-primary hover:text-primary hover:bg-primary/10"
                    : "text-muted-foreground"
                )}
                aria-label="Send message"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

ChatInput.displayName = 'ChatInput';
