"use client";

import React from "react";
import { usePathname } from "next/navigation";

const pageTitles: Record<string, string> = {
  "/dashboard": "Task Dashboard",
  "/builder": "Pipeline Builder",
  "/studio": "Prompt Studio",
  "/settings": "Settings",
};

export default function Header() {
  const pathname = usePathname();

  const getTitle = () => {
    const base = "/" + pathname.split("/")[1];
    return pageTitles[base] || "Content OS";
  };

  return (
    <header className="h-14 bg-slate-900 border-b border-slate-700 flex items-center justify-between px-6 shrink-0">
      <h1 className="text-base font-semibold text-slate-200">{getTitle()}</h1>
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-emerald-500" title="System Online" />
        <span className="text-xs text-slate-400">System Online</span>
      </div>
    </header>
  );
}
