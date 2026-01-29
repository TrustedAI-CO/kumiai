import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { XCircle } from 'lucide-react';
import { api, type AgentInstance } from '@/lib/api';

interface OutputPanelProps {
  agent: AgentInstance;
  onClose?: () => void;
  showHeader?: boolean;
}

interface OutputMessage {
  type: string;
  data: any;
  timestamp: string;
}

export function OutputPanel({ agent, onClose, showHeader = true }: OutputPanelProps) {
  const [messages, setMessages] = useState<OutputMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Get agent name, avatar, and color from agent_id (no legacy character fallback)
  const agentName = agent.agent_id || 'Unknown Agent';
  const agentAvatar = '🤖'; // Default robot avatar (TODO: look up from agents list)
  const agentColor = '#4A90E2'; // Default blue color (TODO: look up from agents list)

  useEffect(() => {
    // Reset messages when agent changes
    setMessages([]);
    setIsStreaming(agent.status !== 'completed' && agent.status !== 'error');

    const unsubscribe = api.streamSessionOutput(agent.instance_id, (event) => {
      setMessages((prev) => [...prev, event]);

      if (event.type === 'complete' || event.type === 'error') {
        setIsStreaming(false);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [agent.instance_id]);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleCancel = async () => {
    await api.cancelSession(agent.instance_id);
    setIsStreaming(false);
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      {showHeader && (
        <div
          className="h-16 px-5 border-b border-gray-200 flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <span className="text-3xl">{agentAvatar}</span>
            <div>
              <h2 className="font-bold text-lg text-gray-900">
                {agentName}
              </h2>
              <p className="text-sm text-gray-600">
                {agent.current_session_description || 'No session description'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isStreaming && (
              <button
                onClick={handleCancel}
                className="px-3 py-1.5 text-sm rounded-lg bg-red-50 text-red-600 hover:bg-red-100 border border-red-200"
              >
                Cancel
              </button>
            )}
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-600"
              >
                <XCircle className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Output */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-2 bg-gray-50">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-sm">No output yet</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} color={agentColor} />
        ))}

        {isStreaming && (
          <motion.div
            className="flex items-center gap-2 text-gray-400"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
          >
            <div className="w-2 h-2 rounded-full bg-current" />
            <div className="w-2 h-2 rounded-full bg-current" />
            <div className="w-2 h-2 rounded-full bg-current" />
          </motion.div>
        )}
      </div>
    </div>
  );
}

function MessageBubble({
  message,
  color,
}: {
  message: OutputMessage;
  color: string;
}) {
  const renderContent = () => {
    if (message.type === 'output') {
      // Parse Claude output
      const data = message.data.data;

      if (data.type === 'assistant') {
        return (
          <div className="prose prose-sm max-w-none">
            <div className="text-gray-900 whitespace-pre-wrap">
              {data.content}
            </div>
          </div>
        );
      }

      if (data.type === 'tool_use') {
        return (
          <div className="text-sm">
            <span
              className="font-medium px-2 py-0.5 rounded"
              style={{ backgroundColor: color + '20', color }}
            >
              {data.tool}
            </span>
            <pre className="mt-2 text-xs text-gray-600 overflow-x-auto bg-gray-100 p-2 rounded">
              {JSON.stringify(data.arguments, null, 2)}
            </pre>
          </div>
        );
      }

      if (data.raw) {
        return (
          <div className="text-sm font-mono text-gray-600">{data.raw}</div>
        );
      }

      // Fallback for other output types
      return (
        <pre className="text-xs text-gray-600 overflow-x-auto bg-gray-100 p-2 rounded">
          {JSON.stringify(data, null, 2)}
        </pre>
      );
    }

    if (message.type === 'status') {
      return (
        <div className="text-sm text-gray-600">
          Status: {message.data.data?.status || message.data.status || 'Unknown'}
        </div>
      );
    }

    if (message.type === 'complete') {
      return (
        <div className="text-sm font-medium text-green-600">
          ✅ Task completed
        </div>
      );
    }

    if (message.type === 'error') {
      const errorText =
        message.data.data?.error ||
        message.data.error ||
        (message.data.subtype ? `Task ${message.data.subtype}` : 'Unknown error');

      return (
        <div className="text-sm font-medium text-red-600">
          ❌ Error: {errorText}
        </div>
      );
    }

    // Default fallback - always show something
    return (
      <pre className="text-xs text-gray-600 overflow-x-auto bg-gray-100 p-2 rounded">
        {JSON.stringify(message, null, 2)}
      </pre>
    );
  };

  const content = renderContent();

  // Don't render empty bubbles
  if (!content) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-3 rounded-lg bg-white border border-gray-200 shadow-sm"
    >
      {content}
    </motion.div>
  );
}
