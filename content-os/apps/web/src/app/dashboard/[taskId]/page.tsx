"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Task } from "@/lib/types";
import { api } from "@/lib/api";
import { useTaskEvents } from "@/hooks/useTaskEvents";
import { statusToBadgeVariant, statusLabel, formatDate } from "@/lib/utils";
import StepTimeline from "@/components/dashboard/StepTimeline";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import Card, { CardContent } from "@/components/ui/Card";

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.taskId as string;

  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTask = useCallback(async () => {
    try {
      const data = await api.getTask(taskId);
      setTask(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load task");
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    fetchTask();
  }, [fetchTask]);

  const handleTaskUpdate = useCallback((updatedTask: Task) => {
    setTask(updatedTask);
  }, []);

  useTaskEvents(taskId, handleTaskUpdate);

  const handleRetry = async () => {
    try {
      const updated = await api.retryTask(taskId);
      setTask(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retry failed");
    }
  };

  const handleCancel = async () => {
    try {
      const updated = await api.cancelTask(taskId);
      setTask(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cancel failed");
    }
  };

  const handleRunStep = async (stepKey: string) => {
    try {
      const updated = await api.runStep(taskId, stepKey);
      setTask(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run step failed");
    }
  };

  const handleRetryStep = async (stepKey: string) => {
    try {
      const updated = await api.runStep(taskId, stepKey);
      setTask(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retry step failed");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="text-center py-20">
        <p className="text-red-400 mb-4">{error || "Task not found"}</p>
        <Button variant="secondary" onClick={() => router.push("/dashboard")}>
          Back to Dashboard
        </Button>
      </div>
    );
  }

  const completedSteps = task.steps.filter((s) => s.status === "success").length;
  const totalSteps = task.steps.length;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => router.push("/dashboard")}
          className="text-slate-400 hover:text-slate-200 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h2 className="text-xl font-bold text-slate-100">{task.title}</h2>
        <Badge variant={statusToBadgeVariant(task.status)}>
          {statusLabel(task.status)}
        </Badge>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card>
          <CardContent>
            <p className="text-xs text-slate-500 mb-1">Pipeline</p>
            <p className="text-sm font-medium text-slate-200">
              {task.pipeline_name || task.pipeline_id}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <p className="text-xs text-slate-500 mb-1">Progress</p>
            <p className="text-sm font-medium text-slate-200">
              {completedSteps}/{totalSteps} steps completed
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <p className="text-xs text-slate-500 mb-1">Created</p>
            <p className="text-sm font-medium text-slate-200">
              {formatDate(task.created_at)}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center gap-2 mb-4">
        {task.status === "failed" && (
          <Button size="sm" onClick={handleRetry}>
            Retry Task
          </Button>
        )}
        {task.status === "running" && (
          <Button size="sm" variant="danger" onClick={handleCancel}>
            Cancel Task
          </Button>
        )}
      </div>

      <Card>
        <CardContent>
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Step Timeline</h3>
          <StepTimeline
            steps={task.steps}
            onRunStep={handleRunStep}
            onRetryStep={handleRetryStep}
          />
        </CardContent>
      </Card>

      {task.outputs && (
        <Card className="mt-6">
          <CardContent>
            <h3 className="text-sm font-semibold text-slate-200 mb-3">Task Outputs</h3>
            <pre className="text-xs bg-slate-900 rounded-lg p-4 overflow-x-auto text-slate-300 scrollbar-thin">
              {JSON.stringify(task.outputs, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
