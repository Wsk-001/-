"use client";

import React from "react";
import { Pipeline } from "@/lib/types";

interface PipelineListProps {
  pipelines: Pipeline[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
}

export default function PipelineList({
  pipelines,
  selectedId,
  onSelect,
  onCreate,
}: PipelineListProps) {
  return (
    <div className="w-72 shrink-0 border-r border-slate-700 flex flex-col">
      <div className="p-4 border-b border-slate-700">
        <button
          onClick={onCreate}
          className="w-full px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors"
        >
          + New Pipeline
        </button>
      </div>
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {pipelines.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-sm text-slate-500">No pipelines yet</p>
          </div>
        ) : (
          pipelines.map((pipeline) => (
            <div
              key={pipeline.id}
              onClick={() => onSelect(pipeline.id)}
              className={`px-4 py-3 cursor-pointer border-b border-slate-700/50 transition-colors ${
                selectedId === pipeline.id
                  ? "bg-blue-600/10 border-l-2 border-l-blue-500"
                  : "hover:bg-slate-800"
              }`}
            >
              <p className="text-sm font-medium text-slate-200 truncate">
                {pipeline.name}
              </p>
              <p className="text-xs text-slate-500 mt-0.5 truncate">
                {pipeline.steps.length} steps
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
