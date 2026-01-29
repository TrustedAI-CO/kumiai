import { useState } from 'react';
import { Sparkles, Send, Loader2, X, ChevronRight, Info, Edit, Lightbulb } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/primitives/button';
import { Textarea } from '@/components/ui/primitives/textarea';

interface PromptSidebarProps {
  title: string;
  placeholder: string;
  contextInfo?: {
    type: 'edit' | 'create';
    itemName?: string;
    itemId?: string;
  };
  onSubmit: (prompt: string) => Promise<{ agent_id: string; message: string }>;
  isOpen: boolean;
  onClose: () => void;
}

export function PromptSidebar({ title, placeholder, contextInfo, onSubmit, isOpen, onClose }: PromptSidebarProps) {
  const [prompt, setPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [agentId, setAgentId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!prompt.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const result = await onSubmit(prompt);
      setAgentId(result.agent_id);
      setMessage(result.message);
      setPrompt('');

      // Keep sidebar open to show result
    } catch (error: any) {
      alert('Failed to process request: ' + error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setPrompt('');
    setAgentId(null);
    setMessage(null);
    setIsSubmitting(false);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay for mobile */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
          />

          {/* Sidebar */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-full lg:w-96 bg-white border-l border-gray-200 shadow-2xl z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex-none border-b border-gray-200">
              <div className="h-16 px-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-br from-primary to-primary/90 rounded-lg">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="type-headline text-gray-900">{title}</h3>
                    <p className="type-body-sm text-gray-500">
                      Natural language editing
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<X className="w-5 h-5" />}
                  onClick={handleClose}
                  className="!p-2"
                />
              </div>

              {/* Context Info */}
              {contextInfo && (
                <div className={`border rounded-lg p-3 ${
                  contextInfo.type === 'edit'
                    ? 'bg-muted/50 border-border'
                    : 'bg-green-50 border-green-200'
                }`}>
                  <div className="flex items-start gap-2">
                    <Info className={`w-4 h-4 mt-0.5 ${
                      contextInfo.type === 'edit' ? 'text-primary' : 'text-green-600'
                    }`} />
                    <div className="flex-1">
                      <div className={`flex items-center gap-2 type-subtitle mb-1 ${
                        contextInfo.type === 'edit' ? 'text-foreground' : 'text-green-800'
                      }`}>
                        {contextInfo.type === 'edit' ? (
                          <>
                            <Edit className="w-4 h-4" />
                            <span>Editing Mode</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4" />
                            <span>Creation Mode</span>
                          </>
                        )}
                      </div>
                      <p className={`type-caption ${
                        contextInfo.type === 'edit' ? 'text-primary' : 'text-green-700'
                      }`}>
                        {contextInfo.type === 'edit' ? (
                          <>
                            Claude will modify <strong>"{contextInfo.itemName}"</strong>
                            <br />
                            <code className="type-caption bg-muted px-1 rounded">ID: {contextInfo.itemId}</code>
                          </>
                        ) : (
                          <>Claude will create a new skill from scratch</>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Help Text */}
              <div className="bg-muted/50 border border-border rounded-lg p-3 mt-3">
                <div className="flex items-center gap-2 type-subtitle text-foreground mb-1">
                  <Lightbulb className="w-4 h-4" />
                  <span>How it works</span>
                </div>
                <p className="type-caption text-primary">
                  Describe what you want in plain English. Claude Code will spawn an agent to make the changes for you.
                </p>
              </div>
            </div>

            {/* Result Message */}
            {message && agentId && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mx-6 mt-4 p-4 bg-green-50 border border-green-200 rounded-lg"
              >
                <div className="flex items-start gap-2">
                  <div className="flex-shrink-0 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center mt-0.5">
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="type-subtitle text-green-800">
                      Agent spawned successfully!
                    </p>
                    <p className="type-caption text-green-600 mt-1">
                      {message}
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <code className="type-caption bg-green-100 text-green-700 px-2 py-1 rounded font-mono">
                        {agentId}
                      </code>
                    </div>
                    <p className="type-caption text-green-600 mt-2">
                      Check the "Agents" tab to monitor progress. Changes will auto-refresh when complete.
                    </p>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Input Area */}
            <div className="flex-1 flex flex-col p-6 overflow-hidden">
              <label className="block type-label text-gray-700 mb-2">
                What would you like to do?
              </label>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    handleSubmit();
                  }
                }}
                placeholder={placeholder}
                disabled={isSubmitting}
                className="flex-1 px-4 py-3 disabled:bg-gray-50 disabled:text-gray-500 resize-none"
              />

              {/* Hint */}
              <div className="mt-3 flex items-center justify-between">
                <p className="type-caption text-gray-500">
                  <kbd className="px-2 py-1 bg-gray-100 rounded type-caption">⌘ Enter</kbd> to send
                </p>
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleSubmit}
                  disabled={!prompt.trim() || isSubmitting}
                  loading={isSubmitting}
                >
                  {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {isSubmitting ? 'Processing...' : 'Send Request'}
                </Button>
              </div>
            </div>

            {/* Examples */}
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <p className="type-label text-gray-700 mb-2">
                💬 Example prompts:
              </p>
              <div className="space-y-2">
                {[
                  "Add Python and Jupyter tools",
                  "Expand documentation with examples",
                  "Change focus to data visualization",
                  "Create Git workflow automation skill"
                ].map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => setPrompt(example)}
                    disabled={isSubmitting}
                    className="w-full text-left px-3 py-2 bg-white border border-gray-200 rounded-lg hover:border-border hover:bg-muted/50 transition-colors type-caption text-gray-600 hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="w-3 h-3 inline mr-1" />
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
