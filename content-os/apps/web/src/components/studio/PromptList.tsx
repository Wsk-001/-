"use client";

import React from "react";
import { Prompt } from "@/lib/types";

interface PromptListProps {
  prompts: Prompt[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
}

export default function PromptList({
  prompts,
  selectedId,
  onSelect,
  onCreate,
}: PromptListProps) {
  const categories = Array.from(new Set(prompts.map((p) => p.category)));

  return (
    <div className="w-72 shrink-0 border-r border-slate-700 flex flex-col">
      <div className="p-4 border-b border-slate-700">
        <button
          onClick={onCreate}
          className="w-full px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors"
        >
          + New Prompt
        </button>
      </div>
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {prompts.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-sm text-slate-500">No prompts yet</p>
          </div>
        ) : (
          categories.map((category) => (
            <div key={category}>
              <div className="px-4 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider bg-slate-800/50">
                {category}
              </div>
              {prompts
                .filter((p) => p.category === category)
                .map((prompt) => (
                  <div
                    key={prompt.id}
                    onClick={() => onSelect(prompt.id)}
                    className={`px-4 py-3 cursor-pointer border-b border-slate-700/50 transition-colors ${
                      selectedId === prompt.id
                        ? "bg-blue-600/10 border-l-2 border-l-blue-500"
                        : "hover:bg-slate-800"
                    }`}
                  >
                    <p className="text-sm font-medium text-slate-200 truncate">
                      {prompt.name}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      v{prompt.version} &middot; {prompt.variables.length} vars
                    </p>
                  </div>
                ))}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
