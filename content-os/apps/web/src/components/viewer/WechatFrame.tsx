"use client";

import React from "react";

interface WechatFrameProps {
  html: string;
}

export default function WechatFrame({ html }: WechatFrameProps) {
  if (!html) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        No HTML content available
      </div>
    );
  }

  return (
    <div className="flex items-start justify-center py-6">
      <div className="relative">
        {/* Phone frame */}
        <div className="w-[375px] h-[740px] rounded-[3rem] border-4 border-slate-600 bg-slate-900 overflow-hidden shadow-2xl">
          {/* Phone notch */}
          <div className="bg-slate-800 h-8 flex items-center justify-center">
            <div className="w-20 h-4 bg-slate-700 rounded-b-lg" />
          </div>
          {/* WeChat header */}
          <div className="bg-slate-800 px-4 py-2 flex items-center justify-between border-b border-slate-700">
            <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="text-xs text-slate-300 font-medium">Article Preview</span>
            <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h.01M12 12h.01M19 12h.01" />
            </svg>
          </div>
          {/* Content area */}
          <div className="h-[calc(100%-4rem)] overflow-y-auto bg-white scrollbar-thin">
            <iframe
              srcDoc={html}
              className="w-full h-full border-0"
              sandbox="allow-same-origin"
              title="WeChat Preview"
            />
          </div>
        </div>
        {/* Home indicator */}
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-32 h-1 bg-slate-600 rounded-full" />
      </div>
    </div>
  );
}
