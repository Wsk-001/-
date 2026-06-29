"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { streamChat, type ChatMessage } from "@/lib/api";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";

interface ChatPanelProps {
  sessionId: string;
}

export default function ChatPanel({ sessionId }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  // 发送消息
  const handleSend = useCallback(
    async (content: string) => {
      if (isStreaming || !content.trim()) return;

      // 添加用户消息
      const userMsg: ChatMessage = { role: "user", content: content.trim() };
      setMessages((prev) => [...prev, userMsg]);

      // 添加空的 assistant 消息（占位）
      const assistantMsg: ChatMessage = { role: "assistant", content: "" };
      setMessages((prev) => [...prev, assistantMsg]);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      await streamChat(
        content.trim(),
        sessionId,
        // onToken
        (token) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === "assistant") {
              updated[updated.length - 1] = {
                ...last,
                content: last.content + token,
              };
            }
            return updated;
          });
        },
        // onDone
        () => {
          setIsStreaming(false);
          abortRef.current = null;
        },
        // onError
        (error) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === "assistant") {
              updated[updated.length - 1] = {
                ...last,
                content: last.content || `Error: ${error}`,
              };
            }
            return updated;
          });
          setIsStreaming(false);
          abortRef.current = null;
        }
      );
    },
    [isStreaming, sessionId]
  );

  // 停止生成
  const handleStop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* 消息列表 */}
      <MessageList messages={messages} isStreaming={isStreaming} />

      {/* 输入区域 */}
      <ChatInput
        onSend={handleSend}
        onStop={handleStop}
        isStreaming={isStreaming}
      />
    </div>
  );
}
