"use client";

import { useState, useRef, useEffect, useCallback } from "react";

interface ChatInputProps {
  onSend: (content: string) => void;
  onStop: () => void;
  isStreaming: boolean;
}

export default function ChatInput({ onSend, onStop, isStreaming }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动调整高度
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [input]);

  // 提交
  const handleSubmit = useCallback(() => {
    if (!input.trim() || isStreaming) return;
    onSend(input);
    setInput("");
    // 重置高度
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input, isStreaming, onSend]);

  // 键盘事件
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  return (
    <div className="border-t border-[#424242] bg-[#212121]">
      <div className="max-w-3xl mx-auto px-4 py-4">
        <div className="flex items-end gap-3 bg-[#2f2f2f] rounded-2xl border border-[#424242] px-4 py-3 focus-within:border-[#10a37f] transition-colors">
          {/* 输入框 */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="发送消息..."
            rows={1}
            className="flex-1 bg-transparent resize-none outline-none text-sm text-[#ececec] placeholder-[#8e8e8e] max-h-[200px]"
            disabled={isStreaming}
          />

          {/* 发送/停止按钮 */}
          {isStreaming ? (
            <button
              onClick={onStop}
              className="flex-shrink-0 p-2 rounded-lg bg-[#ef4444] hover:bg-[#dc2626] text-white transition-colors"
              title="停止生成"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim()}
              className="flex-shrink-0 p-2 rounded-lg bg-[#10a37f] hover:bg-[#1a7f64] disabled:bg-[#424242] disabled:cursor-not-allowed text-white transition-colors"
              title="发送"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" />
              </svg>
            </button>
          )}
        </div>

        <p className="text-[10px] text-[#8e8e8e] text-center mt-2">
          AI Workspace 可能会犯错，请核实重要信息。
        </p>
      </div>
    </div>
  );
}
