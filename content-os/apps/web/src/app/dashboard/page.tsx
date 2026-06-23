"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Task, TaskStatus } from "@/lib/types";
import { api } from "@/lib/api";
import TaskList from "@/components/dashboard/TaskList";
import Button from "@/components/ui/Button";
import Spinner from "@/components/ui/Spinner";
import Modal from "@/components/ui/Modal";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";

export default function DashboardPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<TaskStatus | "all">("all");
  const [showNewTask, setShowNewTask] = useState(false);
  const [pipelines, setPipelines] = useState<{ id: string; name: string }[]>([]);

  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskPipeline, setNewTaskPipeline] = useState("");
  const [creating, setCreating] = useState(false);

  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      const params = activeFilter !== "all" ? { status: activeFilter } : undefined;
      const data = await api.getTasks(params);
      setTasks(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, [activeFilter]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  useEffect(() => {
    if (showNewTask) {
      api.getPipelines().then(setPipelines).catch(console.error);
    }
  }, [showNewTask]);

  const handleCreateTask = async () => {
    if (!newTaskTitle || !newTaskPipeline) return;
    try {
      setCreating(true);
      const task = await api.createTask({
        title: newTaskTitle,
        pipeline_id: newTaskPipeline,
        inputs: {},
      });
      setShowNewTask(false);
      setNewTaskTitle("");
      setNewTaskPipeline("");
      router.push(`/dashboard/${task.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Task Dashboard</h2>
          <p className="text-sm text-slate-400 mt-1">
            Monitor and manage your content production tasks
          </p>
        </div>
        <Button onClick={() => setShowNewTask(true)}>+ New Task</Button>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : (
        <TaskList
          tasks={tasks}
          onTaskClick={(taskId) => router.push(`/dashboard/${taskId}`)}
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
        />
      )}

      <Modal
        isOpen={showNewTask}
        onClose={() => setShowNewTask(false)}
        title="Create New Task"
      >
        <div className="space-y-4">
          <Input
            label="Task Title"
            placeholder="Enter task title..."
            value={newTaskTitle}
            onChange={(e) => setNewTaskTitle(e.target.value)}
          />
          <Select
            label="Pipeline"
            options={[
              { value: "", label: "Select a pipeline..." },
              ...pipelines.map((p) => ({ value: p.id, label: p.name })),
            ]}
            value={newTaskPipeline}
            onChange={(e) => setNewTaskPipeline(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setShowNewTask(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateTask}
              disabled={!newTaskTitle || !newTaskPipeline || creating}
            >
              {creating ? "Creating..." : "Create Task"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
