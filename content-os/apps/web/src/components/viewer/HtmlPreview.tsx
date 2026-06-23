"use client";

import React from "react";

interface HtmlPreviewProps {
  html: string;
}

export default function HtmlPreview({ html }: HtmlPreviewProps) {
  if (!html) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        No HTML content available
      </div>
    );
  }

  return (
    <div className="w-full h-full min-h-[500px] rounded-lg border border-slate-700 overflow-hidden bg-white">
      <iframe
        srcDoc={html}
        className="w-full h-full min-h-[500px] border-0"
        sandbox="allow-same-origin"
        title="HTML Preview"
      />
    </div>
  );
}
