"use client";

import { useState, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import ChatPanel from "@/components/ChatPanel";

// 页面加载时生成一个固定的 session ID
const SESSION_ID = uuidv4();

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-[#212121]">
      {/* 主聊天区域 */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* 顶部栏 */}
        <header className="flex items-center justify-between border-b border-[#424242] px-4 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 rounded hover:bg-[#2f2f2f] transition-colors lg:hidden"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 12h18M3 6h18M3 18h18" />
              </svg>
            </button>
            <h1 className="text-base font-semibold text-[#ececec]">AI Workspace</h1>
          </div>
          <div className="text-xs text-[#b4b4b4]">
            Session: {SESSION_ID.slice(0, 8)}...
          </div>
        </header>

        {/* 聊天面板 */}
        <ChatPanel sessionId={SESSION_ID} />
      </main>
    </div>
  );
}
