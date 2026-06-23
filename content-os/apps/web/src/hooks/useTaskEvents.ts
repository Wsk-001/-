"use client";

import { useEffect, useRef, useCallback } from "react";
import { subscribeToTask } from "@/lib/ws";
import { TaskEvent, Task } from "@/lib/types";
import { api } from "@/lib/api";

export function useTaskEvents(taskId: string | null, onTaskUpdate: (task: Task) => void) {
  const cleanupRef = useRef<(() => void) | null>(null);

  const handleEvent = useCallback(
    (event: TaskEvent) => {
      if (event.task_id === taskId) {
        api.getTask(event.task_id).then(onTaskUpdate).catch(console.error);
      }
    },
    [taskId, onTaskUpdate]
  );

  useEffect(() => {
    if (!taskId) return;

    cleanupRef.current?.();
    cleanupRef.current = subscribeToTask(taskId, handleEvent);

    return () => {
      cleanupRef.current?.();
      cleanupRef.current = null;
    };
  }, [taskId, handleEvent]);
}
