/**
 * useAgentStream — React hook for consuming chatforge SSE streams.
 *
 * Connects to a chatforge SSE endpoint, parses typed chunks,
 * and provides reactive state for chat UI, debug panel, and
 * progress bar.
 *
 * Works with any chatforge backend that uses the standard chunk
 * types: text, tool_call, tool_result, progress, done, error.
 *
 * Usage:
 *   import { useAgentStream } from '@chatforge/react';
 *
 *   function ChatPage({ sessionId }) {
 *     const {
 *       messages, debugEntries, progress,
 *       isStreaming, error,
 *       addUserMessage, reconnect,
 *     } = useAgentStream(sessionId);
 *
 *     // messages → render chat bubbles
 *     // debugEntries → render collapsible debug panel
 *     // progress → render progress bar
 *     // isStreaming → disable send button
 *   }
 */

import { useState, useEffect, useRef, useCallback } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface DebugEntry {
  type: 'tool_call' | 'tool_result';
  toolName: string;
  content: string;
  timestamp: number;
}

export interface Progress {
  total: number;
  completed: number;
  failed: number;
  activeTask: string | null;
  activeDescription: string;
  percent: number;
}

export interface UseAgentStreamResult {
  messages: ChatMessage[];
  debugEntries: DebugEntry[];
  progress: Progress | null;
  isStreaming: boolean;
  error: string | null;
  addUserMessage: (content: string) => void;
  reconnect: () => void;
}

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const DEFAULT_BASE_URL = '/api';

interface UseAgentStreamOptions {
  /** Base URL for the API (default: "/api") */
  baseUrl?: string;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAgentStream(
  sessionId: string | null,
  options: UseAgentStreamOptions = {},
): UseAgentStreamResult {
  const baseUrl = options.baseUrl ?? DEFAULT_BASE_URL;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [debugEntries, setDebugEntries] = useState<DebugEntry[]>([]);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Counter to force EventSource re-creation on reconnect
  const [streamTrigger, setStreamTrigger] = useState(0);

  // Track previous sessionId to detect changes
  const prevSessionIdRef = useRef<string | null>(null);

  // -----------------------------------------------------------------------
  // Reconnect — call after sending a message
  // -----------------------------------------------------------------------

  const reconnect = useCallback(() => {
    setStreamTrigger((n) => n + 1);
  }, []);

  // -----------------------------------------------------------------------
  // Optimistic message insertion
  // -----------------------------------------------------------------------

  const addUserMessage = useCallback((content: string) => {
    setMessages((prev) => [...prev, { role: 'user', content }]);
    setError(null);
  }, []);

  // -----------------------------------------------------------------------
  // Load history on session change
  // -----------------------------------------------------------------------

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      setDebugEntries([]);
      setProgress(null);
      return;
    }

    if (prevSessionIdRef.current !== sessionId) {
      prevSessionIdRef.current = sessionId;
      setDebugEntries([]);
      setProgress(null);
      setError(null);

      fetch(`${baseUrl}/chat/${sessionId}/history`)
        .then((res) => res.json())
        .then((data) => {
          const history: ChatMessage[] = (data.messages || []).map(
            (m: { role: string; content: string }) => ({
              role: m.role as 'user' | 'assistant',
              content: m.content,
            }),
          );
          setMessages(history);
        })
        .catch((err) => {
          console.error('Failed to load history:', err);
        });
    }
  }, [sessionId, baseUrl]);

  // -----------------------------------------------------------------------
  // SSE connection
  // -----------------------------------------------------------------------

  useEffect(() => {
    if (!sessionId) return;

    const url = `${baseUrl}/chat/${sessionId}/stream`;
    const eventSource = new EventSource(url);
    let assistantBuffer = '';

    setIsStreaming(true);
    setError(null);

    eventSource.onmessage = (event) => {
      try {
        const chunk = JSON.parse(event.data);

        switch (chunk.type) {
          case 'text':
            assistantBuffer += chunk.content;
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last?.role === 'assistant') {
                return [
                  ...prev.slice(0, -1),
                  { role: 'assistant', content: assistantBuffer },
                ];
              }
              return [
                ...prev,
                { role: 'assistant', content: assistantBuffer },
              ];
            });
            break;

          case 'tool_call':
            setDebugEntries((prev) => [
              ...prev,
              {
                type: 'tool_call',
                toolName: chunk.tool_name,
                content: JSON.stringify(chunk.tool_args || {}),
                timestamp: Date.now(),
              },
            ]);
            break;

          case 'tool_result':
            setDebugEntries((prev) => [
              ...prev,
              {
                type: 'tool_result',
                toolName: chunk.tool_name,
                content: chunk.content || '',
                timestamp: Date.now(),
              },
            ]);
            break;

          case 'progress':
            if (chunk.progress) {
              setProgress({
                total: chunk.progress.total ?? 0,
                completed: chunk.progress.completed ?? 0,
                failed: chunk.progress.failed ?? 0,
                activeTask: chunk.progress.active_task ?? null,
                activeDescription: chunk.progress.active_description ?? '',
                percent: chunk.progress.percent ?? 0,
              });
            }
            break;

          case 'done':
            setIsStreaming(false);
            assistantBuffer = '';
            break;

          case 'error':
            setIsStreaming(false);
            setError(chunk.error || 'Unknown error');
            assistantBuffer = '';
            break;

          case 'heartbeat':
            // Keep-alive, ignore
            break;
        }
      } catch (parseError) {
        console.warn('Failed to parse SSE chunk:', event.data);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setIsStreaming(false);
    };

    return () => {
      eventSource.close();
    };
  }, [sessionId, streamTrigger, baseUrl]);

  return {
    messages,
    debugEntries,
    progress,
    isStreaming,
    error,
    addUserMessage,
    reconnect,
  };
}