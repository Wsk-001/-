"use client";

import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "@/lib/api";

interface MessageItemProps {
  message: ChatMessage;
  isLast: boolean;
  isStreaming: boolean;
}

export default function MessageItem({ message, isLast, isStreaming }: MessageItemProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-4 ${isUser ? "justify-end" : "justify-start"}`}>
      {/* Assistant 头像 */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#10a37f] flex items-center justify-center text-white text-sm font-bold mt-1">
          AI
        </div>
      )}

      {/* 消息内容 */}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-[#2f2f2f] text-[#ececec]"
            : "bg-transparent text-[#ececec]"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
        ) : (
          <div className={`prose-chat text-sm ${isStreaming && isLast ? "streaming-cursor" : ""}`}>
            {message.content ? (
              <ReactMarkdown>{message.content}</ReactMarkdown>
            ) : isStreaming ? (
              <span className="text-[#b4b4b4]">思考中...</span>
            ) : null}
          </div>
        )}
      </div>

      {/* User 头像 */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#5436DA] flex items-center justify-center text-white text-sm font-bold mt-1">
          U
        </div>
      )}
    </div>
  );
}
