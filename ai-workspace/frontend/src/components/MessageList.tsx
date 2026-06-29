"use client";

import { useRef, useEffect } from "react";
import type { ChatMessage } from "@/lib/api";
import MessageItem from "./MessageItem";

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export default function MessageList({ messages, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 空状态
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="text-4xl mb-4">✦</div>
          <h2 className="text-xl font-semibold text-[#ececec]">AI Workspace</h2>
          <p className="text-sm text-[#b4b4b4] max-w-md">
            开始一段对话。支持多轮聊天，流式输出。
          </p>
          <div className="flex flex-wrap gap-2 justify-center mt-6">
            {["解释量子计算", "写一个 Python 快排", "帮我设计 API"].map(
              (hint) => (
                <span
                  key={hint}
                  className="px-3 py-1.5 text-sm rounded-full border border-[#424242] text-[#b4b4b4] hover:bg-[#2f2f2f] cursor-default"
                >
                  {hint}
                </span>
              )
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        {messages.map((msg, index) => (
          <MessageItem
            key={index}
            message={msg}
            isLast={index === messages.length - 1}
            isStreaming={isStreaming && index === messages.length - 1 && msg.role === "assistant"}
          />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
