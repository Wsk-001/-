"use client";

import React, { useState } from "react";
import { TaskStep, TaskStatus } from "@/lib/types";
import { statusToBadgeVariant, statusLabel, formatDuration } from "@/lib/utils";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";

interface StepTimelineProps {
  steps: TaskStep[];
  onRunStep?: (stepKey: string) => void;
  onRetryStep?: (stepKey: string) => void;
}

export default function StepTimeline({ steps, onRunStep, onRetryStep }: StepTimelineProps) {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  const sortedSteps = [...steps].sort((a, b) => a.order - b.order);

  return (
    <div className="space-y-0">
      {sortedSteps.map((step, index) => {
        const isExpanded = expandedStep === step.key;
        const isLast = index === sortedSteps.length - 1;

        return (
          <div key={step.key} className="relative">
            {!isLast && (
              <div
                className={`absolute left-5 top-10 w-0.5 h-[calc(100%-2.5rem)] ${
                  step.status === "success" ? "bg-emerald-500/30" : "bg-slate-700"
                }`}
              />
            )}
            <div className="flex items-start gap-4 pb-4">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 border-2 ${
                  step.status === "success"
                    ? "bg-emerald-500/20 border-emerald-500 text-emerald-400"
                    : step.status === "running"
                    ? "bg-blue-500/20 border-blue-500 text-blue-400 animate-pulse"
                    : step.status === "failed"
                    ? "bg-red-500/20 border-red-500 text-red-400"
                    : "bg-slate-700 border-slate-600 text-slate-400"
                }`}
              >
                <span className="text-xs font-bold">{index + 1}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => setExpandedStep(isExpanded ? null : step.key)}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-200">
                      {step.name}
                    </span>
                    <Badge variant={statusToBadgeVariant(step.status)}>
                      {statusLabel(step.status)}
                    </Badge>
                    <span className="text-xs text-slate-500">{step.type}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">
                      {formatDuration(step.started_at, step.finished_at)}
                    </span>
                    <svg
                      className={`w-4 h-4 text-slate-500 transition-transform ${
                        isExpanded ? "rotate-180" : ""
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>

                {isExpanded && (
                  <div className="mt-3 space-y-3">
                    {step.inputs && (
                      <div>
                        <p className="text-xs font-medium text-slate-400 mb-1">Inputs</p>
                        <pre className="text-xs bg-slate-900 rounded-lg p-3 overflow-x-auto text-slate-300 scrollbar-thin">
                          {JSON.stringify(step.inputs, null, 2)}
                        </pre>
                      </div>
                    )}
                    {step.outputs && (
                      <div>
                        <p className="text-xs font-medium text-slate-400 mb-1">Outputs</p>
                        <pre className="text-xs bg-slate-900 rounded-lg p-3 overflow-x-auto text-slate-300 scrollbar-thin">
                          {JSON.stringify(step.outputs, null, 2)}
                        </pre>
                      </div>
                    )}
                    {step.error && (
                      <div>
                        <p className="text-xs font-medium text-red-400 mb-1">Error</p>
                        <pre className="text-xs bg-red-950/50 rounded-lg p-3 overflow-x-auto text-red-300 scrollbar-thin">
                          {step.error}
                        </pre>
                      </div>
                    )}
                    <div className="flex items-center gap-2">
                      {step.status === "failed" && onRetryStep && (
                        <Button size="sm" variant="danger" onClick={() => onRetryStep(step.key)}>
                          Retry
                        </Button>
                      )}
                      {(step.status === "pending" || step.status === "failed") && onRunStep && (
                        <Button size="sm" variant="secondary" onClick={() => onRunStep(step.key)}>
                          Run Step
                        </Button>
                      )}
                      {step.retry_count > 0 && (
                        <span className="text-xs text-slate-500">
                          Retries: {step.retry_count}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
