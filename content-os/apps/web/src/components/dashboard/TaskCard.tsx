"use client";

import React from "react";
import { Task, TaskStatus } from "@/lib/types";
import { statusToBadgeVariant, statusLabel, formatDate } from "@/lib/utils";
import Badge from "@/components/ui/Badge";

interface TaskCardProps {
  task: Task;
  onClick: (taskId: string) => void;
}

export default function TaskCard({ task, onClick }: TaskCardProps) {
  const completedSteps = task.steps.filter(
    (s) => s.status === "success"
  ).length;
  const totalSteps = task.steps.length;
  const progressPercent = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  return (
    <div
      onClick={() => onClick(task.id)}
      className="bg-slate-800 rounded-xl border border-slate-700 p-5 cursor-pointer hover:border-slate-600 hover:bg-slate-800/80 transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-slate-100 truncate">
            {task.title}
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {task.pipeline_name || task.pipeline_id}
          </p>
        </div>
        <Badge variant={statusToBadgeVariant(task.status)}>
          {statusLabel(task.status)}
        </Badge>
      </div>

      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
          <span>
            {completedSteps}/{totalSteps} steps
          </span>
          <span>{Math.round(progressPercent)}%</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all ${
              task.status === "failed"
                ? "bg-red-500"
                : task.status === "success"
                ? "bg-emerald-500"
                : "bg-blue-500"
            }`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>{formatDate(task.created_at)}</span>
        {task.error && (
          <span className="text-red-400 truncate ml-2">{task.error}</span>
        )}
      </div>
    </div>
  );
}
